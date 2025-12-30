"""
True Route Agent
真结局线填充 Agent - 基于框架生成详细真路线
"""
import uuid
from typing import Dict, Any, List, Optional, Union

from agents.base_agent import BaseAgent
from prompts.route_planning.true_route_prompt import (
    TRUE_ROUTE_SYSTEM_PROMPT,
    TRUE_ROUTE_PROMPT
)
from models.route_planning.detailed_route import DetailedTrueRoute
from utils.logger import log


class TrueRouteAgent(BaseAgent):
    """
    真结局路线填充Agent

    基于路线结构框架，生成详细的真结局路线
    """

    name = "TrueRouteAgent"
    system_prompt = TRUE_ROUTE_SYSTEM_PROMPT
    human_prompt_template = TRUE_ROUTE_PROMPT
    required_fields = ["route_id", "chapters", "world_mystery_resolution", "true_ending"]
    output_model = DetailedTrueRoute

    def process(
        self,
        story_outline_data: Dict[str, Any],
        route_framework: Dict[str, Any],
        user_idea: str = ""
    ) -> DetailedTrueRoute:
        """处理真结局路线生成"""
        if not story_outline_data:
            raise ValueError("story_outline_data不能为空")
        if not route_framework:
            raise ValueError("route_framework不能为空")

        if not user_idea:
            user_idea = story_outline_data.get("input", {}).get("user_idea", "")

        log.info("生成真结局路线...")

        # 提取数据
        story_summary = self._format_story_summary(story_outline_data)
        framework_str = self._format_route_framework(route_framework)

        try:
            result = self.run(
                user_idea=user_idea,
                story_summary=story_summary,
                route_framework=framework_str
            )

            # 补充必要字段
            if "route_id" not in result:
                result["route_id"] = "route_true"

            true_route = DetailedTrueRoute(**result)
            self._log_success(true_route)
            return true_route

        except Exception as e:
            log.error(f"TrueRouteAgent 失败: {e}")
            raise RuntimeError(f"真结局路线生成失败: {e}") from e

    def _format_story_summary(self, outline_data: Dict[str, Any]) -> str:
        """格式化故事大纲摘要"""
        steps = outline_data.get("steps", {})
        premise = steps.get("premise", {})
        conflict = steps.get("conflict_engine", {}).get("map", {})

        # 主冲突摘要
        main_conflicts = conflict.get("main_conflicts", [])
        conflict_lines = []
        for mc in main_conflicts:
            mc_dict = mc.model_dump() if hasattr(mc, "model_dump") else mc
            conflict_lines.append(f"- {mc_dict.get('conflict_name', '')}: {mc_dict.get('root_cause', '')}")

        return (
            f"核心问题: {premise.get('core_question', '')}\n"
            f"核心主题: {', '.join(premise.get('core_themes', []))}\n"
            f"情感基调: {premise.get('emotional_tone', '')}\n"
            f"\n主冲突:\n" + "\n".join(conflict_lines)
        )

    def _format_route_framework(self, route_fw: Dict[str, Any]) -> str:
        """格式化路线框架"""
        chapters = route_fw.get("chapter_outlines", [])

        lines = [
            f"章节数: {route_fw.get('chapter_count', 0)}",
            f"解锁条件: {', '.join(route_fw.get('unlock_conditions', []))}",
            f"概要: {route_fw.get('outline', '')}",
            "章节概要:"
        ]

        for ch in chapters:
            lines.append(f"  {ch.get('sequence_order')}. {ch.get('chapter_name')}: {ch.get('summary', '')}")

        return "\n".join(lines)

    def _log_success(self, true_route: DetailedTrueRoute) -> None:
        log.info(f"真结局路线生成成功: {len(true_route.chapters)}章")
        log.info(f"  结局类型: {true_route.true_ending.get('ending_type', '')}")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        if not output.get("chapters"):
            return "chapters不能为空"

        if not output.get("world_mystery_resolution"):
            return "必须包含world_mystery_resolution"

        if not output.get("character_arc_convergence"):
            return "必须包含character_arc_convergence"

        if not output.get("true_ending"):
            return "必须包含true_ending"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        return {
            "route_id": "route_true",
            "route_name": "真结局路线",
            "unlock_conditions": [],
            "required_flags": [],
            "chapters": [{
                "chapter_id": "true_ch1", "chapter_name": "最终章", "sequence_order": 1,
                "summary": "概要", "opening_scene": "开场", "main_events": ["事件"],
                "character_development": "发展", "mystery_progress": "揭示", "plot_points": [],
                "chapter_end_state": "状态"
            }],
            "world_mystery_resolution": "谜团解答",
            "character_arc_convergence": "弧光收束",
            "final_climax": "高潮",
            "true_ending": {"ending_type": "True Ending", "description": "真结局"},
            "fallback": True
        }
