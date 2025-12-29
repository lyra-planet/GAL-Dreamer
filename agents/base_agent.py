"""
Agent基类
所有Agent的父类
"""
import json
from typing import Any, Dict, List
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


class BaseAgent:
    """Agent基类"""

    def __init__(self, name: str, system_prompt: str, human_prompt_template: str, use_structured_output: bool = True):
        """
        初始化Agent

        Args:
            name: Agent名称
            system_prompt: 系统提示词
            human_prompt_template: 人类提示词模板
            use_structured_output: 是否使用结构化输出(默认True)
        """
        self.name = name
        self.system_prompt = system_prompt
        self.human_prompt_template = human_prompt_template
        self.use_structured_output = use_structured_output

        # 初始化LLM配置
        if self.use_structured_output:
            # 使用结构化输出时,需要设置环境变量或直接在client_kwargs中传递
            self.llm = ChatOpenAI(
                model=config.LLM_MODEL,
                api_key=config.LLM_API_KEY,
                base_url=config.LLM_BASE_URL,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
                timeout=config.LLM_TIMEOUT,
                model_kwargs={
                    "response_format": {"type": "json_object"}
                }
            )
            log.info(f"{self.name} 启用结构化输出")
        else:
            self.llm = ChatOpenAI(
                model=config.LLM_MODEL,
                api_key=config.LLM_API_KEY,
                base_url=config.LLM_BASE_URL,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
                timeout=config.LLM_TIMEOUT,
            )

        # 创建JSON输出解析器
        self.parser = JsonOutputParser()

        # 最大修复轮数 (包括初次生成)
        self.max_fix_rounds = 4

        log.info(f"{self.name} 初始化完成")

    def _create_prompt(self) -> ChatPromptTemplate:
        """
        创建完整的prompt模板（不进行变量替换）

        Returns:
            ChatPromptTemplate实例
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", self.human_prompt_template)
        ])

        return prompt

    def _extract_json(self, response: str) -> Dict[str, Any]:
        """
        从响应中提取JSON

        Args:
            response: LLM的响应文本

        Returns:
            解析后的JSON字典
        """
        try:
            # 使用安全解析函数
            result = safe_parse_json(response.strip())

            if not result:
                # 尝试提取JSON部分(处理可能的多余文本)
                start = response.find("{")
                end = response.rfind("}")

                if start != -1 and end != -1 and end > start:
                    json_str = response[start:end + 1]
                    result = safe_parse_json(json_str)

            if result:
                log.debug(f"成功提取JSON: {str(result)[:100]}...")
                return result
            else:
                raise ValueError(f"响应中未找到有效的JSON格式。原始响应: {response}")

        except Exception as e:
            log.error(f"{self.name} JSON解析失败: {e}")
            log.error(f"原始响应: {response}")
            raise

    def _get_required_fields(self) -> List[str]:
        """
        获取当前Agent要求的必填字段列表
        子类应该重写此方法返回其必填字段

        Returns:
            必填字段列表
        """
        return []

    def _fix_json_output(self, previous_json: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """
        让LLM修复不正确的JSON输出

        Args:
            previous_json: 之前生成的JSON
            error_message: 验证错误信息

        Returns:
            修复后的JSON
        """
        required_fields = self._get_required_fields()
        required_fields_str = ", ".join(required_fields) if required_fields else "所有原始字段"

        # 构建修复提示
        fix_prompt = JSON_FIX_PROMPT.format(
            error_message=error_message,
            previous_json=json.dumps(previous_json, ensure_ascii=False, indent=2),
            required_fields=required_fields_str
        )

        # 使用结构化输出调用修复
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=fix_prompt)
        ]

        try:
            response = self.llm.invoke(messages)
            fixed_json = self._extract_json(response.content)
            log.info(f"{self.name} JSON修复尝试成功")
            return fixed_json
        except Exception as e:
            log.error(f"{self.name} JSON修复失败: {e}")
            # 返回原始JSON，让外层继续重试
            return previous_json

    def run(self, **kwargs) -> Dict[str, Any]:
        """
        运行Agent,带JSON验证和修复重试机制

        Args:
            **kwargs: 输入参数

        Returns:
            Agent输出的JSON字典
        """
        log.info(f"{self.name} 开始执行...")

        # 创建prompt模板
        prompt_template = self._create_prompt()

        # 构建链
        chain = prompt_template | self.llm

        current_result = None
        last_error = None

        # 多轮修复机制: 1次初始生成 + 3次修复 = 4轮
        for round_num in range(self.max_fix_rounds):
            try:
                if round_num == 0:
                    # 第一轮: 正常生成
                    log.info(f"{self.name} 第{round_num + 1}轮: 生成中...")
                    response = chain.invoke(kwargs)
                    response_text = response.content
                else:
                    # 后续轮: 修复模式
                    log.info(f"{self.name} 第{round_num + 1}轮: 修复中...")
                    response_text = self._fix_json_output(
                        previous_json=current_result,
                        error_message=last_error
                    )
                    # fix_json_output 已经返回解析后的dict
                    if isinstance(response_text, dict):
                        response_text = json.dumps(response_text, ensure_ascii=False)

                log.info(f"{self.name} LLM原始响应:")
                log.info(f"{response_text}")
                log.info(f"{'='*60}")

                # 提取JSON
                result = self._extract_json(response_text)
                current_result = result

                # 验证输出
                validation_result = self.validate_output(result)

                if validation_result is True:
                    # 验证通过
                    log.success(f"{self.name} 执行成功 (第{round_num + 1}轮)")
                    return result
                elif isinstance(validation_result, str):
                    # 验证失败，返回错误信息
                    last_error = validation_result
                    log.warning(f"{self.name} 验证失败: {validation_result}")
                    # 继续下一轮修复
                else:
                    # 验证失败，没有具体错误信息
                    last_error = "格式验证失败，缺少必填字段或格式不正确"
                    log.warning(f"{self.name} 验证失败，将尝试修复")

            except Exception as e:
                error_msg = str(e)

                # 检查是否是内容审核错误
                if "data_inspection_failed" in error_msg or "inappropriate content" in error_msg.lower():
                    log.warning(f"{self.name} 内容审核失败 (第{round_num + 1}轮)")
                    if round_num < self.max_fix_rounds - 1:
                        import time
                        time.sleep(1)
                        continue
                    else:
                        log.error(f"{self.name} 内容审核失败,已达最大重试次数")
                        return self._get_fallback_response()
                else:
                    last_error = f"执行错误: {error_msg}"
                    log.error(f"{self.name} 执行失败: {e}")
                    # 如果还有重试机会，继续
                    if round_num < self.max_fix_rounds - 1:
                        continue
                    else:
                        raise

        # 所有轮次都失败，返回fallback
        log.error(f"{self.name} 已达最大修复轮数({self.max_fix_rounds}),返回fallback")
        return self._get_fallback_response()

    def _get_fallback_response(self) -> Dict[str, Any]:
        """
        当Agent失败时返回安全默认值
        子类可以重写此方法提供特定默认值
        """
        return {
            "error": "Agent execution failed after max retries",
            "fallback": True
        }

    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        验证输出是否有效

        Args:
            output: Agent输出

        Returns:
            True: 验证通过
            str: 验证失败的错误信息
            bool: False表示验证失败(无具体信息)
        """
        # 子类必须重写此方法
        # 返回 True 表示验证通过
        # 返回 str 表示验证失败，返回错误描述
        required_fields = self._get_required_fields()
        missing_fields = [f for f in required_fields if f not in output]

        if missing_fields:
            return f"缺少必填字段: {', '.join(missing_fields)}"

        return True

    def redo_with_feedback(self, previous_output: Dict[str, Any], feedback_issues: List[Any], original_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据一致性审查反馈重做生成

        Args:
            previous_output: 之前的输出结果
            feedback_issues: ConsistencyIssue 列表，包含具体问题和修复建议
            original_kwargs: 原始输入参数

        Returns:
            修复后的输出
        """
        log.info(f"{self.name} 根据反馈重做，问题数: {len(feedback_issues)}")

        # 构建反馈提示
        feedback_prompt = self._build_feedback_prompt(previous_output, feedback_issues)

        # 使用反馈提示调用 LLM
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=feedback_prompt)
        ]

        max_redo_rounds = 2
        for round_num in range(max_redo_rounds):
            try:
                log.info(f"{self.name} 重做第{round_num + 1}轮...")

                response = self.llm.invoke(messages)
                result = self._extract_json(response.content)

                log.info(f"{self.name} 重做响应:")
                log.info(f"{json.dumps(result, ensure_ascii=False, indent=2)[:500]}...")

                # 验证重做结果
                validation_result = self.validate_output(result)
                if validation_result is True:
                    log.success(f"{self.name} 重做成功!")
                    return result
                else:
                    log.warning(f"{self.name} 重做验证失败: {validation_result}")
                    # 更新 messages 让 LLM 继续修复
                    messages.append(SystemMessage(content=f"你之前的输出仍有问题: {validation_result}。请重新修复。"))
                    continue

            except Exception as e:
                log.error(f"{self.name} 重做失败: {e}")
                if round_num < max_redo_rounds - 1:
                    continue
                else:
                    # 重做失败，返回原始结果
                    log.warning(f"{self.name} 重做失败，返回原始结果")
                    return previous_output

        return previous_output

    def _build_feedback_prompt(self, previous_output: Dict[str, Any], feedback_issues: List[Any]) -> str:
        """
        构建反馈提示词

        Args:
            previous_output: 之前的输出
            feedback_issues: 反馈问题列表

        Returns:
            反馈提示词
        """
        # 过滤出针对当前 Agent 的问题
        my_issues = [issue for issue in feedback_issues
                     if hasattr(issue, 'source_agent') and issue.source_agent == self.name]

        if not my_issues:
            # 如果没有针对当前 Agent 的问题，可能是通用问题
            my_issues = feedback_issues

        prompt_parts = [
            "一致性审查发现了以下问题，请你根据反馈修改之前的输出：",
            "",
            "【之前的输出】",
            json.dumps(previous_output, ensure_ascii=False, indent=2),
            "",
            "【发现的问题】"
        ]

        for issue in my_issues:
            severity_icon = {
                "low": "🟢",
                "medium": "🟡",
                "high": "🟠",
                "critical": "🔴"
            }.get(getattr(issue, 'severity', 'medium'), "⚪")

            issue_desc = f"{severity_icon} 严重程度: {getattr(issue, 'severity', 'medium')}"
            issue_desc += f"\n   问题: {getattr(issue, 'description', '未知问题')}"
            issue_desc += f"\n   修复建议: {getattr(issue, 'fix_suggestion', '无')}"

            if hasattr(issue, 'related_field') and issue.related_field:
                issue_desc += f"\n   相关字段: {issue.related_field}"

            prompt_parts.append(issue_desc)

        prompt_parts.extend([
            "",
            "【要求】",
            "1. 保持与原输出一致的结构",
            "2. 只修改有问题的部分",
            "3. 确保修改后不再违反之前的设定",
            "4. 输出完整的JSON格式",
            "",
            "请输出修复后的JSON:"
        ])

        return "\n".join(prompt_parts)
