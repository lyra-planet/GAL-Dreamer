"""
Conflict Outline Agent
冲突大纲 Agent - 规划整体冲突框架
"""
import json
import uuid
from typing import Dict, Any, List, Optional, Union

from agents.base_agent import BaseAgent
from prompts.story_outline.conflict_outline_prompt import (
    CONFLICT_OUTLINE_SYSTEM_PROMPT,
    CONFLICT_OUTLINE_HUMAN_PROMPT
)
from utils.logger import log


class ConflictOutlineAgent(BaseAgent):
    """
    冲突大纲Agent

    功能:
    - 规划整体冲突框架
    - 确定冲突类型和数量
    - 设计冲突的因果链条
    - 规划关键抉择点
    """

    # 类属性配置
    name = "ConflictOutlineAgent"
    system_prompt = CONFLICT_OUTLINE_SYSTEM_PROMPT
    human_prompt_template = CONFLICT_OUTLINE_HUMAN_PROMPT
    required_fields = ["main_conflicts_outline", "secondary_conflicts_outline", "critical_choice_outline"]
    output_model = None  # 不使用特定的输出模型

    def generate_outline(
        self,
        world_setting_json: Dict[str, Any],
        premise_json: Dict[str, Any],
        cast_arc_json: Dict[str, Any],
        user_idea: str = "",
        fix_instructions: str = ""
    ) -> Dict[str, Any]:
        """
        生成冲突大纲

        Args:
            world_setting_json: 完整的世界观数据
            premise_json: 故事前提数据
            cast_arc_json: 角色弧光数据
            user_idea: 用户原始创意
            fix_instructions: 修复指令（如果有）

        Returns:
            冲突大纲字典
        """
        if not world_setting_json:
            raise ValueError("world_setting_json不能为空")
        if not premise_json:
            raise ValueError("premise_json不能为空")
        if not cast_arc_json:
            raise ValueError("cast_arc_json不能为空")

        # 如果没有传user_idea，从world_setting中获取
        if not user_idea:
            user_idea = world_setting_json.get("input", {}).get("user_idea", "")

        log.info("生成冲突大纲...")

        # 提取steps中的数据
        steps = world_setting_json.get("steps", {})
        if not steps:
            raise ValueError("world_setting_json中缺少steps数据")

        # 构建prompt字符串
        world_setting_str = self._format_world_setting_for_prompt(steps)
        premise_str = json.dumps(premise_json, ensure_ascii=False, indent=2)
        cast_arc_str = json.dumps(cast_arc_json, ensure_ascii=False, indent=2)

        try:
            result = self.run(
                user_idea=user_idea,
                world_setting_json=world_setting_str,
                premise_json=premise_str,
                cast_arc_json=cast_arc_str,
                fix_instructions=fix_instructions or "无"
            )

            # 生成outline_id
            if "outline_id" not in result:
                result["outline_id"] = f"conflict_outline_{uuid.uuid4().hex[:8]}"

            self._log_success(result)
            return result

        except Exception as e:
            log.error(f"ConflictOutlineAgent 处理失败: {e}")
            raise RuntimeError(f"冲突大纲生成失败: {e}") from e

    def _format_world_setting_for_prompt(self, steps: Dict[str, Any]) -> str:
        """将世界观数据格式化为prompt字符串（每个元素当str处理，不解析）"""
        lines = []
        for key, value in steps.items():
            # 直接转字符串，不做JSON序列化
            lines.append(f"【{key}】")
            lines.append(str(value))
            lines.append("")  # 空行分隔
        return "\n".join(lines)

    def _log_success(self, outline: Dict[str, Any]) -> None:
        """记录成功日志"""
        log.info("冲突大纲生成成功:")
        main_conflicts = outline.get("main_conflicts_outline", [])
        if main_conflicts:
            for i, main in enumerate(main_conflicts):
                log.info(f"  主冲突{i+1}类型: {main.get('conflict_type', '')}")
        log.info(f"  次要冲突: {len(outline.get('secondary_conflicts_outline', []))}个")
        log.info(f"  背景冲突: {len(outline.get('background_conflicts_outline', []))}个")
        log.info(f"  关键抉择: {len(outline.get('critical_choice_outline', []))}个")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """验证输出"""
        # 检查main_conflicts_outline（复数形式）
        main_conflicts = output.get("main_conflicts_outline")
        if not isinstance(main_conflicts, list):
            return "main_conflicts_outline必须是数组"
        if len(main_conflicts) < 3:
            return "main_conflicts_outline至少需要3个主冲突"

        # 检查每个主冲突的字段
        required_main_fields = ["conflict_type", "core_question", "opposing_forces_hint"]
        for i, main in enumerate(main_conflicts):
            if not isinstance(main, dict):
                return f"main_conflicts_outline[{i}]必须是对象"
            for field in required_main_fields:
                if not main.get(field):
                    return f"main_conflicts_outline[{i}]缺少{field}"

        # 检查secondary_conflicts_outline
        secondary = output.get("secondary_conflicts_outline")
        if not isinstance(secondary, list) or len(secondary) < 3:
            return "secondary_conflicts_outline必须是数组，至少3个"

        # 检查critical_choice_outline
        critical = output.get("critical_choice_outline")
        if not isinstance(critical, list) or len(critical) < 3:
            return "critical_choice_outline必须是数组，至少3个"

        # 检查background_conflicts_outline
        background = output.get("background_conflicts_outline")
        if background is not None and not isinstance(background, list):
            return "background_conflicts_outline必须是数组"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        return {
            "outline_id": f"conflict_outline_fallback_{uuid.uuid4().hex[:8]}",
            "main_conflicts_outline": [
                {
                    "conflict_type": "internal",
                    "core_question": "主角如何在爱情和责任之间选择",
                    "opposing_forces_hint": "内心欲望 vs 外部责任",
                    "thematic_connection": "探索爱与牺牲的主题",
                    "position": "early"
                },
                {
                    "conflict_type": "interpersonal",
                    "core_question": "信任是否能跨越身份的鸿沟",
                    "opposing_forces_hint": "不同立场的角色之间",
                    "thematic_connection": "探索理解与接纳的主题",
                    "position": "mid"
                },
                {
                    "conflict_type": "existential",
                    "core_question": "牺牲少数是否值得拯救多数",
                    "opposing_forces_hint": "个人生命 vs 世界存续",
                    "thematic_connection": "探索生存的代价",
                    "position": "late"
                }
            ],
            "secondary_conflicts_outline": [
                {
                    "conflict_type": "interpersonal",
                    "position": "early",
                    "derives_from": "主冲突",
                    "escalates_to": "信任危机",
                    "character_focus": "主角与女主"
                },
                {
                    "conflict_type": "supernatural",
                    "position": "mid",
                    "derives_from": "主冲突",
                    "escalates_to": "世界崩坏",
                    "character_focus": "全员"
                },
                {
                    "conflict_type": "societal",
                    "position": "mid",
                    "derives_from": "主冲突",
                    "escalates_to": "立场对立",
                    "character_focus": "主角与社会"
                }
            ],
            "background_conflicts_outline": [
                {
                    "conflict_type": "societal",
                    "pervasive_effect": "社会对异界的恐惧",
                    "eruption_points": ["中期", "高潮"]
                }
            ],
            "critical_choice_outline": [
                {
                    "choice_position": 1,
                    "story_phase": "early",
                    "choice_type": "人际关系牺牲",
                    "stake_level": "medium",
                    "consequences_hint": "失去一个朋友，获得关键信息"
                },
                {
                    "choice_position": 2,
                    "story_phase": "mid",
                    "choice_type": "价值观冲突",
                    "stake_level": "high",
                    "consequences_hint": "改变主角的世界观，影响后续选择"
                },
                {
                    "choice_position": 3,
                    "story_phase": "late",
                    "choice_type": "命运与自由意志",
                    "stake_level": "extreme",
                    "consequences_hint": "决定世界的最终走向"
                }
            ],
            "conflict_chain_outline": [
                "主冲突引发人际冲突",
                "人际冲突升级为社会冲突"
            ],
            "escalation_structure": {
                "opening_intensity": 3,
                "midpoint_intensity": 7,
                "climax_intensity": 10,
                "rhythm_pattern": "逐渐上升"
            },
            "fallback": True
        }
