"""
Agent基类
所有Agent的父类，提供通用的LLM调用、错误处理、重试机制
"""
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ValidationError

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage, SystemMessage

from utils.config import config
from utils.logger import log
from utils.json_utils import safe_parse_json


# JSON修复提示词模板
JSON_FIX_PROMPT = """你之前生成的JSON格式不正确，请修复。

【错误信息】
{error_message}

【你之前生成的JSON】
{previous_json}

【要求】
1. 必须返回完整的JSON格式
2. 必须包含以下必填字段: {required_fields}
3. 不要输出任何JSON之外的解释文字
4. 直接输出修复后的JSON

请重新生成正确的JSON:
"""


class AgentConfig(BaseModel):
    """Agent配置模型"""
    name: str
    system_prompt: str
    human_prompt_template: str
    use_structured_output: bool = True
    max_fix_rounds: int = 4
    max_redo_rounds: int = 2
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class BaseAgent(ABC):
    """
    Agent基类

    提供以下功能:
    - LLM调用封装
    - JSON格式验证和自动修复
    - 错误重试机制
    - 内容审核错误处理
    - 降级响应(fallback)
    """

    # 子类需要定义这些类属性
    name: str = ""
    system_prompt: str = ""
    human_prompt_template: str = ""
    required_fields: List[str] = []

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        初始化Agent

        Args:
            config: Agent配置，如果不提供则使用类属性
        """
        if config:
            self._config = config
        else:
            self._config = AgentConfig(
                name=self.name,
                system_prompt=self.system_prompt,
                human_prompt_template=self.human_prompt_template,
            )

        # 初始化LLM
        self._llm = self._create_llm()
        self._parser = JsonOutputParser()

        log.info(f"{self._config.name} 初始化完成")

    def _create_llm(self) -> ChatOpenAI:
        """创建LLM实例"""
        llm_kwargs = {
            "model": config.LLM_MODEL,
            "api_key": config.LLM_API_KEY,
            "base_url": config.LLM_BASE_URL,
            "temperature": self._config.temperature or config.LLM_TEMPERATURE,
            "max_tokens": self._config.max_tokens or config.LLM_MAX_TOKENS,
            "timeout": config.LLM_TIMEOUT,
        }

        # 结构化输出需要JSON模式
        if self._config.use_structured_output:
            llm_kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
            log.debug(f"{self._config.name} 启用结构化输出")

        return ChatOpenAI(**llm_kwargs)

    def _create_prompt_template(self) -> ChatPromptTemplate:
        """创建prompt模板"""
        return ChatPromptTemplate.from_messages([
            ("system", self._config.system_prompt),
            ("human", self._config.human_prompt_template)
        ])

    def _extract_json(self, response: str) -> Dict[str, Any]:
        """
        从响应中提取JSON

        Args:
            response: LLM的响应文本

        Returns:
            解析后的JSON字典

        Raises:
            ValueError: 无法解析JSON时
        """
        response = response.strip()

        # 移除markdown代码块标记
        if response.startswith("```"):
            # 找到第一个换行
            newline_idx = response.find("\n")
            if newline_idx != -1:
                response = response[newline_idx + 1:]
            # 移除结尾的```
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

        # 首先尝试直接解析
        parsed = safe_parse_json(response)
        if parsed is not None:
            return parsed

        # 尝试提取JSON部分（处理有额外文字的情况）
        start = response.find("{")
        end = response.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"响应中未找到有效的JSON格式。响应内容: {response[:500]}...")

        json_str = response[start:end + 1]
        result = safe_parse_json(json_str)

        if result is None:
            raise ValueError(f"JSON解析失败。响应内容: {response[:500]}...")

        return result

    def _fix_json_output(self, previous_json: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """
        让LLM修复不正确的JSON输出

        Args:
            previous_json: 之前生成的JSON
            error_message: 验证错误信息

        Returns:
            修复后的JSON
        """
        required_fields_str = ", ".join(self.required_fields) if self.required_fields else "所有原始字段"

        fix_prompt = JSON_FIX_PROMPT.format(
            error_message=error_message,
            previous_json=json.dumps(previous_json, ensure_ascii=False, indent=2),
            required_fields=required_fields_str
        )

        messages = [
            SystemMessage(content=self._config.system_prompt),
            HumanMessage(content=fix_prompt)
        ]

        try:
            response = self._llm.invoke(messages)
            return self._extract_json(response.content)
        except Exception as e:
            log.error(f"{self._config.name} JSON修复失败: {e}")
            return previous_json

    def _is_content_filter_error(self, error_msg: str) -> bool:
        """检查是否是内容审核错误"""
        error_keywords = [
            "data_inspection_failed",
            "inappropriate content",
            "content_filter",
            "safety_filter",
            "moderation",
        ]
        return any(keyword in error_msg.lower() for keyword in error_keywords)

    def _should_retry(self, round_num: int, last_error: Optional[str]) -> bool:
        """判断是否应该继续重试"""
        return round_num < self._config.max_fix_rounds - 1

    def _handle_content_filter_error(self, round_num: int) -> None:
        """处理内容审核错误"""
        log.warning(f"{self._config.name} 触发内容审核 (第{round_num + 1}轮)")
        if self._should_retry(round_num, None):
            time.sleep(1)  # 等待后重试

    def run(self, **kwargs) -> Dict[str, Any]:
        """
        运行Agent，带JSON验证和修复重试机制

        Args:
            **kwargs: 输入参数，会替换prompt模板中的变量

        Returns:
            Agent输出的JSON字典

        Raises:
            RuntimeError: 达到最大重试次数后仍然失败
        """
        log.info(f"{self._config.name} 开始执行...")
        log.debug(f"输入参数: {json.dumps(kwargs, ensure_ascii=False)[:200]}...")

        prompt_template = self._create_prompt_template()
        chain = prompt_template | self._llm

        current_result: Optional[Dict[str, Any]] = None
        last_error: Optional[str] = None

        for round_num in range(self._config.max_fix_rounds):
            try:
                if round_num == 0:
                    # 第一轮：正常生成
                    log.info(f"{self._config.name} 第{round_num + 1}轮: 生成中...")
                    response = chain.invoke(kwargs)
                    response_text = response.content
                else:
                    # 后续轮：修复模式
                    log.info(f"{self._config.name} 第{round_num + 1}轮: 修复中...")
                    fixed_result = self._fix_json_output(current_result, last_error)
                    response_text = json.dumps(fixed_result, ensure_ascii=False)

                log.debug(f"原始响应: {response_text[:500]}...")

                # 解析JSON
                result = self._extract_json(response_text)
                current_result = result

                # 验证输出
                validation_result = self._validate_output(result)

                if validation_result is True:
                    log.success(f"{self._config.name} 执行成功 (第{round_num + 1}轮)")
                    return result
                else:
                    last_error = str(validation_result)
                    log.warning(f"{self._config.name} 验证失败: {last_error}")

            except Exception as e:
                error_msg = str(e)

                # 检查是否是内容审核错误
                if self._is_content_filter_error(error_msg):
                    self._handle_content_filter_error(round_num)
                    if not self._should_retry(round_num, error_msg):
                        log.error(f"{self._config.name} 内容审核失败，已达最大重试次数")
                        return self._get_fallback_response()
                    continue

                last_error = f"执行错误: {error_msg}"
                log.error(f"{self._config.name} 第{round_num + 1}轮异常: {e}")

                if not self._should_retry(round_num, error_msg):
                    raise RuntimeError(f"{self._config.name} 执行失败: {error_msg}") from e

        # 达到最大重试次数
        log.error(f"{self._config.name} 达到最大重试次数({self._config.max_fix_rounds})")
        return self._get_fallback_response()

    def redo_with_feedback(
        self,
        previous_output: Dict[str, Any],
        feedback_issues: List[Any],
        original_kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根据一致性审查反馈重做生成

        Args:
            previous_output: 之前的输出结果
            feedback_issues: 反馈问题列表
            original_kwargs: 原始输入参数

        Returns:
            修复后的输出
        """
        log.info(f"{self._config.name} 根据反馈重做，问题数: {len(feedback_issues)}")

        feedback_prompt = self._build_feedback_prompt(previous_output, feedback_issues)

        messages = [
            SystemMessage(content=self._config.system_prompt),
            HumanMessage(content=feedback_prompt)
        ]

        for round_num in range(self._config.max_redo_rounds):
            try:
                log.info(f"{self._config.name} 重做第{round_num + 1}轮...")

                response = self._llm.invoke(messages)
                result = self._extract_json(response.content)

                validation_result = self._validate_output(result)
                if validation_result is True:
                    log.success(f"{self._config.name} 重做成功!")

                    # 输出更改摘要
                    self._log_changes(previous_output, result)

                    return result
                else:
                    log.warning(f"{self._config.name} 重做验证失败: {validation_result}")
                    messages.append(SystemMessage(
                        content=f"输出仍有问题: {validation_result}。请重新修复。"
                    ))

            except Exception as e:
                log.error(f"{self._config.name} 重做失败: {e}")
                if round_num >= self._config.max_redo_rounds - 1:
                    log.warning(f"{self._config.name} 重做失败，返回原始结果")
                    return previous_output

        return previous_output

    def _build_feedback_prompt(
        self,
        previous_output: Dict[str, Any],
        feedback_issues: List[Any]
    ) -> str:
        """构建反馈提示词"""
        # 过滤出针对当前Agent的问题
        my_issues = [
            issue for issue in feedback_issues
            if hasattr(issue, 'source_agent') and issue.source_agent == self._config.name
        ]

        if not my_issues:
            my_issues = feedback_issues

        severity_icons = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🟠",
            "critical": "🔴"
        }

        issue_descriptions = []
        for issue in my_issues:
            severity = getattr(issue, 'severity', 'medium')
            icon = severity_icons.get(severity, "⚪")

            desc = f"{icon} [{severity}]\n"
            desc += f"   问题: {getattr(issue, 'description', '未知问题')}\n"
            desc += f"   建议: {getattr(issue, 'fix_suggestion', '无')}"

            if hasattr(issue, 'related_field') and issue.related_field:
                desc += f"\n   字段: {issue.related_field}"

            issue_descriptions.append(desc)

        prompt_parts = [
            "一致性审查发现以下问题，请根据反馈修改之前的输出：",
            "",
            "【之前的输出】",
            json.dumps(previous_output, ensure_ascii=False, indent=2),
            "",
            "【发现的问题】",
            *issue_descriptions,
            "",
            "【要求】",
            "1. 保持与原输出一致的结构",
            "2. 只修改有问题的部分",
            "3. 确保修改后不再违反之前的设定",
            "4. 输出完整的JSON格式",
            "",
            "请输出修复后的JSON:"
        ]

        return "\n".join(prompt_parts)

    def _log_changes(self, previous_output: Dict[str, Any], new_output: Dict[str, Any]) -> None:
        """记录并显示输出变更"""
        import difflib

        def compare_dicts(prev, new, path=""):
            changes = []

            # 检查新增或修改的键
            for key in set(list(prev.keys()) + list(new.keys())):
                current_path = f"{path}.{key}" if path else key

                if key not in prev:
                    changes.append(f"  + {current_path}: {new[key]}")
                elif key not in new:
                    changes.append(f"  - {current_path}: {prev[key]}")
                elif prev[key] != new[key]:
                    # 类型不同或值不同
                    prev_val = prev[key]
                    new_val = new[key]

                    if isinstance(prev_val, dict) and isinstance(new_val, dict):
                        # 递归比较嵌套字典
                        changes.extend(compare_dicts(prev_val, new_val, current_path))
                    elif isinstance(prev_val, list) and isinstance(new_val, list):
                        # 列表比较
                        if str(prev_val) != str(new_val):
                            changes.append(f"  ~ {current_path}:")
                            changes.append(f"      旧: {prev_val}")
                            changes.append(f"      新: {new_val}")
                    else:
                        # 简单值比较
                        changes.append(f"  ~ {current_path}:")
                        changes.append(f"      旧: {prev_val}")
                        changes.append(f"      新: {new_val}")

            return changes

        changes = compare_dicts(previous_output, new_output)

        if changes:
            log.info(f"📝 {self._config.name} 更新内容:")
            for change in changes[:20]:  # 最多显示20条更改
                log.info(f"{change}")
            if len(changes) > 20:
                log.info(f"  ... 还有 {len(changes) - 20} 条更改")
        else:
            log.info(f"📝 {self._config.name} 无实质性更改")

    def _validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """
        验证输出是否有效

        Args:
            output: Agent输出

        Returns:
            True: 验证通过
            str: 验证失败的错误信息
        """
        # 检查必填字段
        missing_fields = [f for f in self.required_fields if f not in output]

        if missing_fields:
            return f"缺少必填字段: {', '.join(missing_fields)}"

        # 调用子类的自定义验证
        custom_result = self.validate_output(output)
        if custom_result is not True:
            return custom_result

        # 如果子类定义了 output_model，进行 Pydantic 验证
        if hasattr(self, 'output_model') and self.output_model is not None:
            return self._pydantic_validate(output, self.output_model)

        return True

    def _pydantic_validate(self, output: Dict[str, Any], model_class) -> Union[bool, str]:
        """
        使用 Pydantic 模型进行完整验证

        Args:
            output: Agent输出
            model_class: Pydantic 模型类

        Returns:
            True: 验证通过
            str: 验证失败的错误信息
        """
        try:
            model_class(**output)
            return True
        except ValidationError as e:
            # 解析 Pydantic 错误，提取清晰的信息
            errors = e.errors()
            error_msgs = []
            for error in errors:
                loc = " -> ".join(str(x) for x in error['loc'])
                msg = error['msg']
                error_msgs.append(f"{loc}: {msg}")
            return "类型验证失败:\n" + "\n".join(error_msgs)
        except Exception as e:
            return f"验证失败: {str(e)}"

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """
        验证输出的自定义逻辑

        子类可以重写此方法添加额外的验证逻辑

        Args:
            output: Agent输出

        Returns:
            True: 验证通过
            str: 验证失败的错误信息
        """
        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """
        获取降级响应

        当Agent失败时返回的安全默认值。
        子类可以重写此方法提供特定默认值。

        Returns:
            降级响应字典
        """
        return {
            "error": f"{self._config.name} execution failed after max retries",
            "fallback": True,
            "agent_name": self._config.name
        }
