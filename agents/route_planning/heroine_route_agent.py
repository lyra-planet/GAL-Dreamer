"""
Heroine Route Agent
个人路线填充 Agent - 基于框架生成详细个人线

新架构：个人线 = 插曲章节 + 结局章节
"""
import uuid
from typing import Dict, Any, List, Optional, Union

from agents.base_agent import BaseAgent
from prompts.route_planning.heroine_route_prompt import (
    HEROINE_ROUTE_SYSTEM_PROMPT,
    HEROINE_ROUTE_PROMPT
)
from models.route_planning.detailed_route import DetailedHeroineRoute
from utils.logger import log


class HeroineRouteAgent(BaseAgent):
    """
    个人路线填充Agent

    基于路线结构框架，为单个女主生成详细个人线
    新架构：插曲章节（穿插在共通线中）+ 结局章节
    """

    name = "HeroineRouteAgent"
    system_prompt = HEROINE_ROUTE_SYSTEM_PROMPT
    human_prompt_template = HEROINE_ROUTE_PROMPT
    required_fields = ["heroine_id", "heroine_name", "interlude_chapters", "ending_chapter", "ending_conditions"]
    output_model = DetailedHeroineRoute

    def process(
        self,
        story_outline_data: Dict[str, Any],
        route_framework: Dict[str, Any],
        heroine_arc: Dict[str, Any],
        user_idea: str = ""
    ) -> DetailedHeroineRoute:
        """处理个人路线生成"""
        if not story_outline_data:
            raise ValueError("story_outline_data不能为空")
        if not route_framework:
            raise ValueError("route_framework不能为空")

        if not user_idea:
            user_idea = story_outline_data.get("input", {}).get("user_idea", "")

        heroine_name = route_framework.get("heroine_name", "该女主")
        log.info(f"生成 {heroine_name} 的个人路线（插曲+结局）...")

        # 提取数据
        heroine_arc_str = self._format_heroine_arc(heroine_arc)
        framework_str = self._format_route_framework(route_framework)

        try:
            result = self.run(
                user_idea=user_idea,
                heroine_name=heroine_name,
                heroine_arc=heroine_arc_str,
                route_framework=framework_str
            )

            # 补充必要字段
            if "heroine_id" not in result:
                result["heroine_id"] = route_framework.get("heroine_id", "")
            if "heroine_name" not in result:
                result["heroine_name"] = heroine_name

            heroine_route = DetailedHeroineRoute(**result)
            self._log_success(heroine_route)
            return heroine_route

        except Exception as e:
            log.error(f"HeroineRouteAgent 失败 ({heroine_name}): {e}")
            raise RuntimeError(f"个人路线生成失败: {e}") from e

    def _format_heroine_arc(self, heroine_arc: Dict[str, Any]) -> str:
        """格式化女主弧光"""
        if not heroine_arc:
            return "无"

        return (
            f"弧光类型: {heroine_arc.get('character_arc_type', '')}\n"
            f"起点: {heroine_arc.get('initial_state', '')}\n"
            f"深层需求: {heroine_arc.get('deep_need', '')}\n"
            f"终点: {heroine_arc.get('final_state', '')}\n"
            f"弧光教训: {heroine_arc.get('arc_lesson', '')}"
        )

    def _format_route_framework(self, route_fw: Dict[str, Any]) -> str:
        """格式化路线框架"""
        interludes = route_fw.get("interlude_chapters", [])
        ending = route_fw.get("ending_chapter", {})

        lines = [
            f"路线类型: {route_fw.get('route_type', '')}",
            f"主题: {route_fw.get('theme', '')}",
            f"插曲章节: {len(interludes)}个",
            "插曲概要:"
        ]

        for ch in interludes:
            lines.append(f"  {ch.get('sequence_order')}. {ch.get('chapter_name')}: {ch.get('summary', '')}")

        if ending:
            lines.append(f"结局章节: {ending.get('chapter_name', '')}")
            lines.append(f"  概要: {ending.get('summary', '')}")

        return "\n".join(lines)

    def _log_success(self, heroine_route: DetailedHeroineRoute) -> None:
        interlude_count = len(heroine_route.interlude_chapters)
        has_ending = heroine_route.ending_chapter is not None
        log.info(f"{heroine_route.heroine_name} 个人路线生成成功:")
        log.info(f"  插曲章节: {interlude_count}个")
        log.info(f"  结局章节: {'有' if has_ending else '无'}")
        log.info(f"  需要好感度: {heroine_route.ending_conditions.get('required_affection', 0)}")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        if not output.get("interlude_chapters"):
            return "interlude_chapters不能为空"

        if not output.get("ending_chapter"):
            return "ending_chapter不能为空"

        if not output.get("ending_conditions"):
            return "ending_conditions不能为空"

        valid_types = ["sweet", "bitter", "tragic", "complex", "hidden", "normal", "bad"]
        if output.get("route_type") not in valid_types:
            return f"route_type无效: {output.get('route_type')}"

        # 验证插曲章节
        for i, ch in enumerate(output.get("interlude_chapters", [])):
            if not ch.get("opening_scene"):
                return f"interlude_chapters[{i}]缺少opening_scene"
            if ch.get("chapter_type") != "interlude":
                return f"interlude_chapters[{i}]的chapter_type必须是interlude"

        # 验证结局章节
        ending = output.get("ending_chapter")
        if ending and ending.get("chapter_type") != "ending":
            return "ending_chapter的chapter_type必须是ending"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        return {
            "heroine_id": "heroine_001",
            "heroine_name": "女主",
            "route_type": "sweet",
            "route_theme": "主题",
            "interlude_chapters": [{
                "chapter_id": "heroine_001_interlude_1", "chapter_name": "插曲1",
                "sequence_order": 3, "chapter_type": "interlude",
                "associated_heroine": "heroine_001",
                "summary": "概要", "opening_scene": "开场",
                "main_events": ["事件"], "character_development": "发展",
                "mystery_progress": "", "plot_points": [], "chapter_end_state": "状态"
            }],
            "ending_chapter": {
                "chapter_id": "heroine_001_ending", "chapter_name": "结局",
                "sequence_order": 99, "chapter_type": "ending",
                "associated_heroine": "heroine_001",
                "summary": "结局概要", "opening_scene": "开场",
                "main_events": ["事件"], "character_development": "收束",
                "mystery_progress": "主线交汇", "plot_points": [], "chapter_end_state": "最终状态"
            },
            "ending_conditions": {
                "required_affection": 70,
                "required_flags": [],
                "forbidden_flags": []
            },
            "personal_conflict": "冲突",
            "conflict_resolution": "解决",
            "main_story_intersection": "交汇",
            "ending_summary": "结局摘要",
            "fallback": True
        }
