"""
Pacing Atmosphere Agent
节奏氛围 Agent - 设计剧情情绪曲线
"""
import json
import uuid
from typing import Dict, Any, List, Optional, Union

from agents.base_agent import BaseAgent
from prompts.route_planning.pacing_atmosphere_prompt import (
    PACING_ATMOSPHERE_SYSTEM_PROMPT,
    PACING_ATMOSPHERE_HUMAN_PROMPT
)
from models.route_planning.mood_curve import MoodCurve
from utils.logger import log


class PacingAtmosphereAgent(BaseAgent):
    """
    节奏氛围Agent

    功能:
    - 为每条路线设计章节级情绪曲线
    - 设计场景级情绪分布
    - 确保整体节奏张弛有度
    - 设计情绪转换点
    """

    # 类属性配置
    name = "PacingAtmosphereAgent"
    system_prompt = PACING_ATMOSPHERE_SYSTEM_PROMPT
    human_prompt_template = PACING_ATMOSPHERE_HUMAN_PROMPT
    required_fields = ["common_route_mood", "heroine_route_moods"]
    output_model = MoodCurve

    def process(
        self,
        story_outline_data: Dict[str, Any],
        route_plan: Dict[str, Any],
        user_idea: str = "",
        validate: bool = True
    ) -> MoodCurve:
        """
        处理节奏氛围生成

        Args:
            story_outline_data: 故事大纲数据
            route_plan: 路线规划数据
            user_idea: 用户原始创意
            validate: 是否验证输出

        Returns:
            MoodCurve: 情绪曲线
        """
        if not story_outline_data:
            raise ValueError("story_outline_data不能为空")
        if not route_plan:
            raise ValueError("route_plan不能为空")

        steps = story_outline_data.get("steps", {})
        if not steps:
            raise ValueError("story_outline_data中缺少steps数据")

        if not user_idea:
            user_idea = story_outline_data.get("input", {}).get("user_idea", "")

        log.info("设计节奏与情绪曲线...")

        # 构建输入摘要
        premise = steps.get("premise", {})
        premise_summary = self._format_premise_for_mood(premise)
        common_route_summary = self._format_common_route(route_plan.get("common_route", {}))
        heroine_routes_summary = self._format_heroine_routes(route_plan.get("heroine_routes", []))
        true_route_summary = self._format_true_route(route_plan.get("true_route"))
        escalation_summary = self._format_escalation_curve(steps.get("conflict_engine", {}))

        # 获取 route_plan_id 用于 prompt
        route_plan_id = route_plan.get("route_plan_id", "unknown")

        try:
            result = self.run(
                user_idea=user_idea,
                route_plan_id=route_plan_id,
                emotional_tone=premise.get("emotional_tone", ""),
                core_themes=", ".join(premise.get("core_themes", [])),
                common_route_summary=common_route_summary,
                heroine_routes_summary=heroine_routes_summary,
                true_route_summary=true_route_summary,
                escalation_summary=escalation_summary
            )

            # 生成mood_curve_id
            if "mood_curve_id" not in result:
                result["mood_curve_id"] = f"mood_curve_{uuid.uuid4().hex[:8]}"

            # 添加source_route_plan
            if "source_route_plan" not in result:
                result["source_route_plan"] = route_plan.get("route_plan_id", "")

            mood_curve = MoodCurve(**result)
            self._log_success(mood_curve)
            return mood_curve

        except Exception as e:
            log.error(f"PacingAtmosphereAgent 处理失败: {e}")
            raise RuntimeError(f"节奏氛围生成失败: {e}") from e

    def _format_premise_for_mood(self, premise: Dict[str, Any]) -> str:
        """格式化故事前提用于情绪设计"""
        if not premise:
            return "无"

        return (
            f"情感基调: {premise.get('emotional_tone', '')}\n"
            f"核心主题: {', '.join(premise.get('core_themes', []))}\n"
            f"情绪关键词: {', '.join(premise.get('emotional_keywords', []))}"
        )

    def _format_common_route(self, common_route: Dict[str, Any]) -> str:
        """格式化共通线摘要"""
        if not common_route:
            return "无"

        chapters = common_route.get("chapters", [])
        chapter_list = "\n".join([
            f"  - {ch.get('chapter_name', '')}: {ch.get('summary', '')}"
            for ch in chapters
        ])

        return (
            f"名称: {common_route.get('route_name', '')}\n"
            f"目的: {common_route.get('purpose', '')}\n"
            f"章节数: {common_route.get('estimated_chapters', 0)}\n"
            f"章节列表:\n{chapter_list}"
        )

    def _format_heroine_routes(self, heroine_routes: List[Dict[str, Any]]) -> str:
        """格式化个人路线摘要"""
        if not heroine_routes:
            return "无"

        lines = []
        for route in heroine_routes:
            lines.append(f"- {route.get('heroine_name', '')} ({route.get('route_type', '')})")
            lines.append(f"  主题: {route.get('route_theme', '')}")
            lines.append(f"  章节数: {route.get('estimated_chapters', 0)}")

            # 列出章节
            chapters = route.get("chapters", [])
            if chapters:
                lines.append(f"  章节: {', '.join([ch.get('chapter_name', '') for ch in chapters])}")
            lines.append("")

        return "\n".join(lines)

    def _format_true_route(self, true_route: Optional[Dict[str, Any]]) -> str:
        """格式化真路线摘要"""
        if not true_route:
            return "无真路线"

        return (
            f"名称: {true_route.get('route_name', '')}\n"
            f"章节数: {true_route.get('estimated_chapters', 0)}\n"
            f"解锁条件: {', '.join(true_route.get('unlock_conditions', []))}"
        )

    def _format_escalation_curve(self, conflict_engine: Dict[str, Any]) -> str:
        """格式化冲突升级曲线"""
        if not conflict_engine:
            return "无"

        conflict_map = conflict_engine.get("map", {})
        escalation_curve = conflict_map.get("escalation_curve", [])

        if not escalation_curve:
            return "无"

        lines = []
        for node in escalation_curve:
            node_dict = node.model_dump() if hasattr(node, "model_dump") else node
            lines.append(
                f"- {node_dict.get('node_name', '')}: "
                f"强度{node_dict.get('emotional_intensity', 5)}, "
                f"{node_dict.get('node_type', '')}"
            )
        return "\n".join(lines)

    def _log_success(self, mood_curve: MoodCurve) -> None:
        """记录成功日志"""
        log.info("节奏与情绪曲线生成成功:")
        log.info(f"  共通线场景: {len(mood_curve.common_route_mood.scenes)}个")
        log.info(f"  个人路线曲线: {len(mood_curve.heroine_route_moods)}条")
        if mood_curve.true_route_mood:
            log.info(f"  真路线场景: {len(mood_curve.true_route_mood.scenes)}个")
        log.info(f"  情绪分布: {mood_curve.mood_distribution}")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """验证输出"""
        # 检查common_route_mood
        common_mood = output.get("common_route_mood")
        if not isinstance(common_mood, dict):
            return "common_route_mood必须是对象"

        required_chapter_fields = ["chapter_id", "chapter_name", "route_id",
                                    "dominant_mood", "scenes"]
        for field in required_chapter_fields:
            if not common_mood.get(field):
                return f"common_route_mood缺少{field}"

        # 检查scenes
        scenes = common_mood.get("scenes", [])
        if not isinstance(scenes, list):
            return "common_route_mood.scenes必须是数组"

        valid_moods = ["daily", "sweet", "suspense", "angst",
                       "climax", "aftermath", "comedy", "melancholy"]
        valid_functions = ["introduction", "development", "transition",
                          "buildup", "release", "foreshadowing"]

        for i, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                return f"common_route_mood.scenes[{i}]必须是对象"
            if scene.get("mood_type") not in valid_moods:
                return f"common_route_mood.scenes[{i}]的mood_type无效"
            if scene.get("narrative_function") not in valid_functions:
                return f"common_route_mood.scenes[{i}]的narrative_function无效"

        # 检查intensity范围
        intensity_fields = ["opening_intensity", "peak_intensity", "closing_intensity"]
        for field in intensity_fields:
            intensity = common_mood.get(field, 0)
            if not isinstance(intensity, int) or intensity < 1 or intensity > 10:
                return f"common_route_mood.{field}必须在1-10之间"

        # 检查heroine_route_moods
        heroine_moods = output.get("heroine_route_moods", [])
        if not isinstance(heroine_moods, list) or len(heroine_moods) == 0:
            return "heroine_route_moods必须是非空数组"

        # 检查mood_distribution
        mood_dist = output.get("mood_distribution", {})
        if mood_dist and not isinstance(mood_dist, dict):
            return "mood_distribution必须是对象"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        return {
            "mood_curve_id": f"mood_curve_fallback_{uuid.uuid4().hex[:8]}",
            "source_route_plan": "fallback",
            "common_route_mood": {
                "chapter_id": "common_chapter_1",
                "chapter_name": "第一章",
                "route_id": "route_common",
                "dominant_mood": "daily",
                "opening_intensity": 2,
                "peak_intensity": 4,
                "closing_intensity": 3,
                "rhythm_pattern": "日常→甜→余韵",
                "scenes": [
                    {
                        "scene_id": "common_1_1",
                        "scene_name": "日常场景",
                        "mood_type": "daily",
                        "emotional_intensity": 2,
                        "tension_level": 2,
                        "narrative_function": "introduction",
                        "description": "日常校园生活"
                    }
                ],
                "mood_shifts": []
            },
            "heroine_route_moods": [],
            "true_route_mood": None,
            "overall_pacing_analysis": "无法完成完整分析，请人工审核",
            "mood_distribution": {"daily": 1},
            "intensity_curve": [],
            "fallback": True
        }
