"""
Director Agent
全局统筹 Agent - 负责整体故事一致性和协调各Agent修改
"""
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from utils.config import config
from utils.logger import log
from utils.json_utils import safe_parse_json
from prompts.director_prompt import DIRECTOR_SYSTEM_PROMPT, DIRECTOR_HUMAN_PROMPT
from models.director import GlobalRevisionPlan, StorySnapshot
from models.plot import ConsistencyIssue


class DirectorAgent:
    """全局统筹Agent - 协调各Agent修改，确保整体一致性"""

    def __init__(self):
        """初始化Director Agent"""
        self.name = "DirectorAgent"
        self.system_prompt = DIRECTOR_SYSTEM_PROMPT
        self.human_prompt_template = DIRECTOR_HUMAN_PROMPT

        # Director 使用结构化输出确保返回有效 JSON
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL,
            temperature=0.3,  # 较低温度，保证输出稳定
            max_tokens=config.LLM_MAX_TOKENS,  # 使用配置中的max_tokens
            timeout=config.LLM_TIMEOUT,
            model_kwargs={
                "response_format": {"type": "json_object"}
            }
        )

        log.info(f"{self.name} 初始化完成 (使用结构化输出, max_tokens={config.LLM_MAX_TOKENS})")

    def analyze_and_plan(
        self,
        story_snapshot: StorySnapshot,
        consistency_issues: List[ConsistencyIssue]
    ) -> GlobalRevisionPlan:
        """
        分析一致性问题并制定全局修订计划

        Args:
            story_snapshot: 完整故事快照
            consistency_issues: 一致性问题列表

        Returns:
            GlobalRevisionPlan: 全局修订计划
        """
        log.info(f"{self.name} 开始分析，问题数: {len(consistency_issues)}")

        # 构建输入
        story_constraints = self._format_story_constraints(story_snapshot)
        world_setting = self._format_world_setting(story_snapshot)
        cast_summary = self._format_cast_summary(story_snapshot)
        macro_plot_summary = self._format_macro_plot_summary(story_snapshot)
        route_design_summary = self._format_route_design_summary(story_snapshot)
        issues_text = self._format_consistency_issues(consistency_issues)

        prompt = DIRECTOR_HUMAN_PROMPT.format(
            story_constraints=story_constraints,
            world_setting=world_setting,
            cast_summary=cast_summary,
            macro_plot_summary=macro_plot_summary,
            route_design_summary=route_design_summary,
            consistency_issues=issues_text
        )

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]

        response = self.llm.invoke(messages)
        result = self._extract_revision_plan(response.content)

        log.info(f"{self.name} 分析完成:")
        log.info(f"  有问题: {result.has_issues}")
        log.info(f"  涉及Agent数: {len(result.agent_modifications)}")
        log.info(f"  执行顺序: {' -> '.join(result.execution_order)}")

        return result

    def execute_revision(
        self,
        plan: GlobalRevisionPlan,
        agents: Dict[str, Any],
        story_snapshot: StorySnapshot
    ) -> Dict[str, Any]:
        """
        执行修订计划，统筹各Agent进行修改

        Args:
            plan: 全局修订计划
            agents: 所有Agent的字典
            story_snapshot: 当前故事快照

        Returns:
            修改后的故事快照
        """
        log.info(f"{self.name} 开始执行修订计划...")

        # 按照执行顺序修改各Agent
        for agent_name in plan.execution_order:
            # 找到对应的修改指令
            mod = next((m for m in plan.agent_modifications if m.agent_name == agent_name), None)
            if not mod:
                log.warning(f"未找到 {agent_name} 的修改指令")
                continue

            if agent_name not in agents:
                log.warning(f"未找到Agent: {agent_name}")
                continue

            agent = agents[agent_name]
            log.info(f"指挥 {agent_name} 进行修改...")

            # 获取其他Agent的上下文
            context = self._build_cross_agent_context(mod, story_snapshot)

            # 执行修改
            new_content = self._execute_agent_modification(
                agent=agent,
                modification=mod,
                context=context,
                snapshot=story_snapshot
            )

            # 更新快照
            self._update_snapshot(story_snapshot, agent_name, new_content)

            log.success(f"{agent_name} 修改完成")

        return story_snapshot.to_full_dict()

    def _execute_agent_modification(
        self,
        agent: Any,
        modification: Any,
        context: str,
        snapshot: StorySnapshot
    ) -> Dict[str, Any]:
        """
        执行单个Agent的修改

        使用Agent自身的重试修复机制（最多4轮）

        Args:
            agent: Agent实例
            modification: 修改指令
            context: 跨Agent上下文
            snapshot: 故事快照

        Returns:
            修改后的内容
        """
        # 构建全局修改提示
        global_revision_prompt = self._build_global_revision_prompt(
            modification=modification,
            context=context,
            snapshot=snapshot
        )

        # 使用Agent的重试机制（类似run方法，但用自定义prompt）
        from langchain_core.messages import SystemMessage, HumanMessage
        import json

        messages = [
            SystemMessage(content=agent.system_prompt),
            HumanMessage(content=global_revision_prompt)
        ]

        max_retries = 4  # 与BaseAgent的max_fix_rounds一致
        last_error = None
        current_result = None

        for attempt in range(max_retries):
            try:
                log.info(f"{agent.name} 全局修改第{attempt + 1}轮...")

                response = agent.llm.invoke(messages)
                result = agent._extract_json(response.content)
                current_result = result

                # 输出完整响应用于调试
                log.debug(f"{agent.name} 完整LLM响应:")
                log.debug(json.dumps(result, ensure_ascii=False, indent=2))
                log.info(f"{agent.name} LLM响应预览: {json.dumps(result, ensure_ascii=False)[:300]}...")

                # 验证结果
                validation = agent.validate_output(result)
                if validation is True:
                    log.success(f"{agent.name} 全局修改成功 (第{attempt + 1}轮)")
                    return result
                else:
                    last_error = validation
                    log.warning(f"{agent.name} 修改验证失败: {validation}")
                    if attempt < max_retries - 1:
                        # 构建修复提示
                        fix_prompt = self._build_fix_prompt(
                            previous_result=result,
                            error_message=validation,
                            original_instructions=modification.modification_instructions
                        )
                        messages = [
                            SystemMessage(content=agent.system_prompt),
                            HumanMessage(content=fix_prompt)
                        ]
                        continue

            except Exception as e:
                last_error = str(e)
                log.error(f"{agent.name} 修改失败: {e}")
                if attempt < max_retries - 1:
                    continue

        # 所有重试都失败，记录并返回原内容
        log.error(f"{agent.name} 已达最大重试次数({max_retries})，修改失败")
        log.error(f"最后错误: {last_error}")
        log.warning(f"{agent.name} 保留原内容")
        return modification.current_content

    def _build_fix_prompt(
        self,
        previous_result: Dict[str, Any],
        error_message: str,
        original_instructions: str
    ) -> str:
        """构建修复提示"""
        import json
        import re

        # 提取缺少的字段名
        required_fields = []
        if "缺少必填字段" in error_message:
            match = re.search(r'缺少必填字段: (.+)', error_message)
            if match:
                required_fields = match.group(1).split(", ")
        elif "值为空" in error_message:
            # 提取空字段名
            match = re.search(r'([^.]+)\.([^"]+?)值为空', error_message)
            if match:
                required_fields = [match.group(2)]

        prompt_parts = [
            "【JSON 修复任务】",
            "",
            "你之前的输出JSON缺少某些必填字段或字段值为空。请补充完整。",
            "",
            "【错误信息】",
            error_message,
        ]

        if required_fields:
            prompt_parts.extend([
                "",
                f"【需要补充/修复的字段】: {', '.join(required_fields)}",
            ])

        prompt_parts.extend([
            "",
            "【你之前的输出 - 必须保留所有已有内容！】",
            json.dumps(previous_result, ensure_ascii=False, indent=2),
            "",
            "【完整结构要求 - 必须满足！】",
            "",
            "**主角 (protagonist) 必须包含的字段:**",
            "  - character_id: 角色ID",
            "  - name: 姓名",
            "  - personality: 性格列表",
            "  - background: 背景故事",
            "  - appearance: 外貌描述",
            "  - motivation: 动机",
            "  - core_flaw: 核心缺陷",
            "",
            "**每个可攻略角色 (heroines数组中每个元素) 必须包含的字段:**",
            "  - character_id: 角色ID",
            "  - name: 姓名",
            "  - personality: 性格列表",
            "  - background: 背景故事",
            "  - appearance: 外貌描述",
            "  - motivation: 动机",
            "  - personality_type: 性格原型",
            "  - first_impression: 第一印象",
            "  - relationship_start: 与主角初始关系",
            "  - voice_tone: 说话语气",
            "",
            "**每个配角 (side_characters数组中每个元素) 必须包含的字段:**",
            "  - character_id: 角色ID",
            "  - name: 姓名",
            "  - personality: 性格列表",
            "  - background: 背景故事",
            "  - appearance: 外貌描述",
            "  - motivation: 动机",
            "  - importance: 重要程度",
            "  - story_function: 故事作用",
            "",
            "**顶层必须包含的字段:**",
            "  - protagonist: 主角对象",
            "  - heroines: 可攻略角色数组",
            "  - side_characters: 配角数组",
            "  - character_relationships: 关系对象",
            "",
            "【修复要求】",
            "1. 输出完整的JSON，不要截断任何内容！",
            "2. 保留之前输出中已有的所有内容",
            "3. 为缺少或为空的字段填充合理的值",
            "4. 确保所有角色都包含完整的必填字段",
            "",
            "请输出完整的修复后JSON:"
        ])

        return "\n".join(prompt_parts)

    def _build_global_revision_prompt(
        self,
        modification: Any,
        context: str,
        snapshot: StorySnapshot
    ) -> str:
        """构建全局修改提示"""
        prompt_parts = [
            "【全局修改指令】",
            "",
            f"**修改目标**: {modification.modification_instructions}",
            f"**预期效果**: {modification.expected_outcome}",
            "",
            "【当前内容】",
            f"{self._format_current_content(modification)}",
            "",
            "【全局上下文 - 其他Agent的相关内容】",
            context if context else "(无)",
            "",
            "【重要提醒】",
            "1. 你的修改必须与整个故事保持一致",
            "2. 考虑修改对其他部分的影响",
            "3. 保持与已设定的世界观、角色性格的协调",
            "",
            "请输出修改后的完整JSON:"
        ]

        return "\n".join(prompt_parts)

    def _format_current_content(self, modification: Any) -> str:
        """格式化当前内容"""
        import json
        return json.dumps(modification.current_content, ensure_ascii=False, indent=2)

    def _build_cross_agent_context(self, modification: Any, snapshot: StorySnapshot) -> str:
        """构建跨Agent上下文"""
        context_parts = []

        for ref in modification.context_from_other_agents:
            if "世界观" in ref or "world" in ref.lower():
                context_parts.append(f"【世界观】{snapshot.worldbuilding.get('description', '')}")
            elif "角色" in ref or "cast" in ref.lower():
                context_parts.append(f"【角色】主角: {snapshot.cast_design.get('protagonist', {}).get('name', '')}")
            elif "剧情" in ref or "plot" in ref.lower():
                context_parts.append(f"【剧情】{snapshot.macro_plot.get('story_arc', '')}")

        return "\n\n".join(context_parts) if context_parts else ""

    def _update_snapshot(self, snapshot: StorySnapshot, agent_name: str, new_content: Dict[str, Any]):
        """更新快照"""
        if agent_name == "worldbuilding":
            snapshot.worldbuilding = new_content
        elif agent_name == "cast_design":
            snapshot.cast_design = new_content
        elif agent_name == "macro_plot":
            snapshot.macro_plot = new_content
        elif agent_name == "route_design":
            snapshot.route_design = new_content
        elif agent_name == "conflict_emotion":
            snapshot.conflict_emotion = new_content

    def _extract_revision_plan(self, response: str) -> GlobalRevisionPlan:
        """提取修订计划"""
        import re

        # 首先尝试直接解析
        result = safe_parse_json(response)

        if not result:
            # 尝试提取 markdown 代码块中的 JSON
            json_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_block:
                result = safe_parse_json(json_block.group(1))

        if not result:
            # 尝试找到第一个完整的 JSON 对象
            start = response.find("{")
            if start != -1:
                # 找到匹配的结束括号
                depth = 0
                for i in range(start, len(response)):
                    if response[i] == '{':
                        depth += 1
                    elif response[i] == '}':
                        depth -= 1
                        if depth == 0:
                            result = safe_parse_json(response[start:i + 1])
                            break

        if result:
            try:
                return GlobalRevisionPlan(**result)
            except Exception as e:
                log.warning(f"GlobalRevisionPlan解析失败: {e}")
                # 尝试修复数据
                return self._fix_revision_plan(result)
        else:
            log.error(f"无法从响应中提取JSON: {response[:500]}...")
            # 返回默认计划
            return GlobalRevisionPlan(
                has_issues=False,
                overall_assessment="解析失败，假设无问题",
                revision_strategy="无",
                agent_modifications=[],
                execution_order=[],
                verification_points=[]
            )

    def _fix_revision_plan(self, data: Dict) -> GlobalRevisionPlan:
        """尝试修复不完整的修订计划"""
        log.info("尝试修复修订计划数据...")

        # 确保必填字段存在
        if "has_issues" not in data:
            data["has_issues"] = True
        if "overall_assessment" not in data:
            data["overall_assessment"] = "需要修复一致性问题"
        if "revision_strategy" not in data:
            data["revision_strategy"] = "根据反馈逐步修改"
        if "agent_modifications" not in data:
            data["agent_modifications"] = []
        if "verification_points" not in data:
            data["verification_points"] = []

        # 修复 execution_order 和 agent_modifications 不匹配的问题
        if "execution_order" not in data or not data["execution_order"]:
            # 从 agent_modifications 中提取 agent_name
            data["execution_order"] = [m.get("agent_name") for m in data["agent_modifications"] if "agent_name" in m]
            log.info(f"从agent_modifications重建execution_order: {data['execution_order']}")
        else:
            # 检查 execution_order 中的每个 agent 是否在 agent_modifications 中
            valid_order = []
            existing_agents = {m.get("agent_name") for m in data["agent_modifications"] if "agent_name" in m}
            for agent_name in data["execution_order"]:
                if agent_name in existing_agents:
                    valid_order.append(agent_name)
                else:
                    log.warning(f"execution_order 中的 {agent_name} 在 agent_modifications 中找不到，已移除")
            data["execution_order"] = valid_order

        try:
            plan = GlobalRevisionPlan(**data)
            log.info(f"修订计划修复成功: {len(plan.agent_modifications)}个修改, 顺序: {plan.execution_order}")
            return plan
        except Exception as e:
            log.error(f"修复失败: {e}")
            return GlobalRevisionPlan(
                has_issues=False,
                overall_assessment="数据解析失败",
                revision_strategy="无",
                agent_modifications=[],
                execution_order=[],
                verification_points=[]
            )

    # ===== 格式化方法 =====

    def _format_story_constraints(self, snapshot: StorySnapshot) -> str:
        """格式化故事约束"""
        c = snapshot.story_intake
        return f"题材: {c.get('genre', '')}\n主题: {', '.join(c.get('themes', []))}\n基调: {c.get('tone', '')}"

    def _format_world_setting(self, snapshot: StorySnapshot) -> str:
        """格式化世界观"""
        w = snapshot.worldbuilding
        return f"时代: {w.get('era', '')}\n地点: {w.get('location', '')}\n类型: {w.get('type', '')}\n核心冲突: {w.get('core_conflict_source', '')}"

    def _format_cast_summary(self, snapshot: StorySnapshot) -> str:
        """格式化角色摘要"""
        c = snapshot.cast_design
        protagonist = c.get('protagonist', {})
        heroines = c.get('heroines', [])
        return f"主角: {protagonist.get('name', '')} (缺陷: {protagonist.get('core_flaw', '')})\n可攻略角色: {', '.join([h.get('name', '') for h in heroines])}"

    def _format_macro_plot_summary(self, snapshot: StorySnapshot) -> str:
        """格式化大剧情摘要"""
        p = snapshot.macro_plot
        return f"故事弧: {p.get('story_arc', '')}\n高潮: {p.get('climax_point', '')}"

    def _format_route_design_summary(self, snapshot: StorySnapshot) -> str:
        """格式化线路设计摘要"""
        r = snapshot.route_design
        routes = r.get('routes', [])
        return f"线路数: {len(routes)}\n分歧策略: {r.get('branching_strategy', '')}"

    def _format_consistency_issues(self, issues: List[ConsistencyIssue]) -> str:
        """格式化一致性问题"""
        lines = []
        for issue in issues:
            severity_icon = {
                "low": "🟢",
                "medium": "🟡",
                "high": "🟠",
                "critical": "🔴"
            }.get(issue.severity, "⚪")

            lines.append(f"{severity_icon} [{issue.source_agent}] {issue.description}")
            lines.append(f"   修复建议: {issue.fix_suggestion}")

        return "\n".join(lines)
