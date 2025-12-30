"""
Common Route Agent
共通线填充 Agent - 基于框架生成详细共通线
"""
import uuid
from typing import Dict, Any, List, Optional, Union

from agents.base_agent import BaseAgent
from prompts.route_planning.common_route_prompt import (
    COMMON_ROUTE_SYSTEM_PROMPT,
    COMMON_ROUTE_PROMPT
)
from models.route_planning.detailed_route import DetailedCommonRoute
from utils.logger import log


class CommonRouteAgent(BaseAgent):
    """
    共通线填充Agent

    基于路线结构框架，生成详细的共通线内容
    """

    name = "CommonRouteAgent"
    system_prompt = COMMON_ROUTE_SYSTEM_PROMPT
    human_prompt_template = COMMON_ROUTE_PROMPT
    required_fields = ["route_id", "chapters"]
    output_model = DetailedCommonRoute

    def process(
        self,
        story_outline_data: Dict[str, Any],
        structure_framework: Dict[str, Any],
        user_idea: str = ""
    ) -> DetailedCommonRoute:
        """处理共通线生成"""
        if not story_outline_data:
            raise ValueError("story_outline_data不能为空")
        if not structure_framework:
            raise ValueError("structure_framework不能为空")

        if not user_idea:
            user_idea = story_outline_data.get("input", {}).get("user_idea", "")

        log.info("生成共通线详细内容...")

        # 提取数据
        story_summary = self._format_story_summary(story_outline_data)
        framework_str = self._format_framework(structure_framework)

        try:
            result = self.run(
                user_idea=user_idea,
                story_summary=story_summary,
                structure_framework=framework_str
            )

            # 补充必要字段
            if "route_id" not in result:
                result["route_id"] = "route_common"

            common_route = DetailedCommonRoute(**result)
            self._log_success(common_route)
            return common_route

        except Exception as e:
            log.error(f"CommonRouteAgent 失败: {e}")
            raise RuntimeError(f"共通线生成失败: {e}") from e

    def _format_story_summary(self, outline_data: Dict[str, Any]) -> str:
        """格式化故事大纲摘要"""
        steps = outline_data.get("steps", {})
        premise = steps.get("premise", {})

        lines = [
            f"核心钩子: {premise.get('hook', '')}",
            f"核心问题: {premise.get('core_question', '')}",
            f"情感基调: {premise.get('emotional_tone', '')}",
            f"核心主题: {', '.join(premise.get('core_themes', []))}"
        ]
        return "\n".join(lines)

    def _format_framework(self, framework: Dict[str, Any]) -> str:
        """格式化结构框架"""
        common_fw = framework.get("common_route_framework", {})
        chapters = common_fw.get("chapter_outlines", [])

        lines = [
            f"共通线: {common_fw.get('chapter_count')}章",
            f"目的: {common_fw.get('purpose', '')}",
            "章节概要:"
        ]

        for ch in chapters:
            lines.append(f"  {ch.get('sequence_order')}. {ch.get('chapter_name')}: {ch.get('summary', '')}")

        return "\n".join(lines)

    def _log_success(self, common_route: DetailedCommonRoute) -> None:
        log.info(f"共通线生成成功: {len(common_route.chapters)}章")
        log.info(f"  选择点: {len(common_route.choice_points)}个")
        log.info(f"  谜团线索: {len(common_route.mystery_clues)}条")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        if not output.get("chapters"):
            return "chapters不能为空"

        for i, ch in enumerate(output.get("chapters", [])):
            if not ch.get("opening_scene"):
                return f"chapters[{i}]缺少opening_scene"
            if not ch.get("main_events"):
                return f"chapters[{i}]缺少main_events"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        return {
            "route_id": "route_common",
            "route_name": "共通线",
            "purpose": "介绍世界观",
            "chapters": [{
                "chapter_id": "common_ch1", "chapter_name": "第一章", "sequence_order": 1,
                "chapter_type": "common", "associated_heroine": None,
                "summary": "概要", "opening_scene": "开场", "main_events": ["事件"],
                "character_development": "发展", "mystery_progress": "",
                "plot_points": [], "chapter_end_state": "状态"
            }],
            "character_introductions": {},
            "mystery_clues": [],
            "choice_points": [],
            "fallback": True
        }
