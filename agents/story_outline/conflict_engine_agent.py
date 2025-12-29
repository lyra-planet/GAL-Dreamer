"""
Conflict Engine Agent
矛盾引擎 Agent - 基于冲突大纲生成具体冲突
"""
import json
import uuid
from typing import Dict, Any, List, Optional, Union

from agents.base_agent import BaseAgent
from prompts.story_outline.conflict_map_prompt import (
    CONFLICT_ENGINE_SYSTEM_PROMPT_STR,
    GENERATE_MAIN_CONFLICTS_HUMAN_PROMPT,
    GENERATE_MAIN_CONFLICT_HUMAN_PROMPT,
    GENERATE_SECONDARY_CONFLICT_HUMAN_PROMPT,
    GENERATE_BACKGROUND_CONFLICT_HUMAN_PROMPT,
    GENERATE_ESCALATION_CURVE_HUMAN_PROMPT,
    GENERATE_CONFLICT_CHAIN_HUMAN_PROMPT
)
from models.story_outline.conflict_map import ConflictMap, Conflict, EscalationNode
from utils.logger import log


class ConflictEngineAgent(BaseAgent):
    """
    矛盾引擎Agent

    功能:
    - 根据冲突大纲生成具体冲突
    - 生成主冲突、次要冲突、背景冲突
    - 生成升级曲线
    - 生成冲突链和势力博弈
    """

    # 类属性配置
    name = "ConflictEngineAgent"
    system_prompt = CONFLICT_ENGINE_SYSTEM_PROMPT_STR
    required_fields = []
    output_model = ConflictMap

    def generate_main_conflicts(
        self,
        world_setting_json: str,
        premise_json: str,
        cast_arc_json: str,
        main_conflicts_outline: str,
        user_idea: str = "",
        fix_instructions: str = ""
    ) -> List[Conflict]:
        """生成主冲突列表（至少3个）"""
        result = self._run_with_template(
            GENERATE_MAIN_CONFLICTS_HUMAN_PROMPT,
            user_idea=user_idea,
            fix_instructions=fix_instructions or "无",
            world_setting_json=world_setting_json,
            premise_json=premise_json,
            cast_arc_json=cast_arc_json,
            main_conflicts_outline=main_conflicts_outline
        )
        main_conflicts_data = result.get("main_conflicts", result)
        return [Conflict(**mc) for mc in main_conflicts_data]

    def generate_main_conflict(
        self,
        world_setting_json: str,
        premise_json: str,
        cast_arc_json: str,
        conflict_outline: str,
        user_idea: str = "",
        other_main_conflicts: str = "",
        fix_instructions: str = ""
    ) -> Conflict:
        """生成单个主冲突（用于逐个生成）"""
        result = self._run_with_template(
            GENERATE_MAIN_CONFLICT_HUMAN_PROMPT,
            user_idea=user_idea,
            fix_instructions=fix_instructions or "无",
            world_setting_json=world_setting_json,
            premise_json=premise_json,
            cast_arc_json=cast_arc_json,
            conflict_outline=conflict_outline,
            other_main_conflicts=other_main_conflicts or "无"
        )
        return Conflict(**result)

    def generate_secondary_conflict(
        self,
        world_setting_json: str,
        premise_json: str,
        previous_conflicts: str,
        conflict_outline: str,
        conflict_index: int,
        user_idea: str = "",
        fix_instructions: str = ""
    ) -> Conflict:
        """生成次要冲突"""
        result = self._run_with_template(
            GENERATE_SECONDARY_CONFLICT_HUMAN_PROMPT,
            user_idea=user_idea,
            fix_instructions=fix_instructions or "无",
            world_setting_json=world_setting_json,
            premise_json=premise_json,
            previous_conflicts=previous_conflicts,
            conflict_outline=conflict_outline,
            conflict_index=conflict_index
        )
        return Conflict(**result)

    def generate_background_conflict(
        self,
        world_setting_json: str,
        previous_conflicts: str,
        conflict_outline: str,
        conflict_index: int,
        user_idea: str = "",
        fix_instructions: str = ""
    ) -> Conflict:
        """生成背景冲突"""
        result = self._run_with_template(
            GENERATE_BACKGROUND_CONFLICT_HUMAN_PROMPT,
            user_idea=user_idea,
            fix_instructions=fix_instructions or "无",
            world_setting_json=world_setting_json,
            previous_conflicts=previous_conflicts,
            conflict_outline=conflict_outline,
            conflict_index=conflict_index
        )
        return Conflict(**result)

    def generate_escalation_curve(
        self,
        world_setting_json: str,
        premise_json: str,
        all_conflicts_json: str,
        escalation_structure: str,
        critical_choices: str,
        user_idea: str = "",
        fix_instructions: str = ""
    ) -> List[EscalationNode]:
        """生成升级曲线"""
        result = self._run_with_template(
            GENERATE_ESCALATION_CURVE_HUMAN_PROMPT,
            user_idea=user_idea,
            fix_instructions=fix_instructions or "无",
            world_setting_json=world_setting_json,
            premise_json=premise_json,
            all_conflicts=all_conflicts_json,
            escalation_structure=escalation_structure,
            critical_choices=critical_choices
        )
        curve_data = result.get("escalation_curve", result)
        return [EscalationNode(**node) for node in curve_data]

    def generate_conflict_chain(
        self,
        all_conflicts_json: str,
        cast_arc_json: str,
        user_idea: str = "",
        fix_instructions: str = ""
    ) -> Dict[str, Any]:
        """生成冲突链和势力博弈"""
        result = self._run_with_template(
            GENERATE_CONFLICT_CHAIN_HUMAN_PROMPT,
            user_idea=user_idea,
            fix_instructions=fix_instructions or "无",
            all_conflicts=all_conflicts_json,
            cast_arc_json=cast_arc_json
        )
        return result

    def _run_with_template(self, template: str, **kwargs) -> Dict[str, Any]:
        """使用指定模板运行"""
        # 替换模板中的占位符
        human_prompt = template.format(**kwargs)

        # 构造消息（包含system prompt）
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=human_prompt)
        ]

        # 调用LLM
        response = self._llm.invoke(messages)
        result = self._parse_json_response(response.content)

        # 如果有fixer，尝试修复
        if hasattr(self, 'json_fixer') and self.json_fixer:
            result = self.json_fixer.fix_json(result)

        return result

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """解析JSON响应"""
        import re
        # 查找JSON代码块
        match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        # 尝试直接解析
        try:
            return json.loads(content)
        except:
            # 如果失败，尝试提取JSON对象
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        raise ValueError(f"无法解析JSON响应: {content[:200]}")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """验证输出（保留兼容性）"""
        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        return {
            "conflict_id": "conflict_main",
            "conflict_name": "爱情与责任",
            "conflict_type": "internal",
            "conflict_level": "critical",
            "opposing_forces": {
                "爱情": "对女主的爱",
                "责任": "守护世界的责任"
            },
            "origin": "故事开始前",
            "root_cause": "两个需求不可兼得",
            "manifestations": ["选择的痛苦", "内心的挣扎"],
            "involved_characters": [],
            "resolution_conditions": ["做出最终选择"],
            "world_rule_references": []
        }
