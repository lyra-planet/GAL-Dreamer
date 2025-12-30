"""
Route Structure Agent
路线结构规划 Agent - 只规划整体框架
"""
import uuid
from typing import Dict, Any, List, Optional, Union

from agents.base_agent import BaseAgent
from prompts.route_planning.route_structure_prompt import (
    ROUTE_STRUCTURE_SYSTEM_PROMPT,
    ROUTE_STRUCTURE_PROMPT
)
from models.route_planning.route_structure import RouteStructure
from utils.logger import log


class RouteStructureAgent(BaseAgent):
    """
    路线结构规划Agent

    只负责规划框架：
    - 共通线有多少章、每章概要
    - 每个女主路线有多少章、每章概要
    - 真结局线概要
    - Flag框架（不含具体触发条件）

    不生成具体内容！
    """

    name = "RouteStructureAgent"
    system_prompt = ROUTE_STRUCTURE_SYSTEM_PROMPT
    human_prompt_template = ROUTE_STRUCTURE_PROMPT
    required_fields = ["common_route_framework", "heroine_route_frameworks"]
    output_model = RouteStructure

    def process(
        self,
        story_outline_data: Dict[str, Any],
        user_idea: str = ""
    ) -> RouteStructure:
        """处理路线结构规划"""
        if not story_outline_data:
            raise ValueError("story_outline_data不能为空")

        steps = story_outline_data.get("steps", {})
        if not steps:
            raise ValueError("story_outline_data中缺少steps数据")

        if not user_idea:
            user_idea = story_outline_data.get("input", {}).get("user_idea", "")

        log.info("规划路线结构框架...")

        # 提取数据
        heroines_summary = self._format_heroines(steps.get("cast_arc", {}))
        critical_choices = self._format_critical_choices(steps.get("conflict_engine", {}))

        try:
            result = self.run(
                user_idea=user_idea,
                heroines_summary=heroines_summary,
                critical_choices=critical_choices
            )

            if "structure_id" not in result:
                result["structure_id"] = f"route_struct_{uuid.uuid4().hex[:8]}"

            if "source_outline" not in result:
                result["source_outline"] = steps.get("conflict_engine", {}).get("map", {}).get("conflict_map_id", "")

            structure = RouteStructure(**result)
            self._log_success(structure)
            return structure

        except Exception as e:
            log.error(f"RouteStructureAgent 失败: {e}")
            raise RuntimeError(f"路线结构规划失败: {e}") from e

    def _format_heroines(self, cast_arc: Dict[str, Any]) -> str:
        heroines = cast_arc.get("heroines", [])
        if not heroines:
            return "无"

        lines = []
        for h in heroines:
            lines.append(f"- {h.get('character_name', '')}: {h.get('character_arc_type', '')}弧光")
            lines.append(f"  深层需求: {h.get('deep_need', '')}")
        return "\n".join(lines)

    def _format_critical_choices(self, conflict_engine: Dict[str, Any]) -> str:
        outline = conflict_engine.get("outline", {})
        critical_choices = outline.get("critical_choice_outline", [])

        if not critical_choices:
            return "无"

        lines = []
        for cc in critical_choices:
            lines.append(
                f"- 抉择{cc.get('choice_position', '')}: "
                f"{cc.get('choice_type', '')} - {cc.get('consequences_hint', '')}"
            )
        return "\n".join(lines)

    def _log_success(self, structure: RouteStructure) -> None:
        log.info("路线结构框架生成成功:")
        log.info(f"  总章节: {structure.total_estimated_chapters}章")
        log.info(f"  共通线: {structure.common_route_framework.get('chapter_count')}章（主线）")
        log.info(f"  插曲章节: {len(structure.common_route_framework.get('heroine_interlude_chapters', []))}章")
        log.info(f"  个人路线: {len(structure.heroine_route_frameworks)}条")
        for fw in structure.heroine_route_frameworks:
            interlude_count = len(fw.get('interlude_chapters', []))
            has_ending = fw.get('ending_chapter') is not None
            log.info(f"    - {fw.get('heroine_name')}: 插曲{interlude_count}章, 结局{'有' if has_ending else '无'} ({fw.get('route_type')})")
        if structure.true_route_framework:
            log.info(f"  真路线: {structure.true_route_framework.get('chapter_count')}章")
        log.info(f"  结局条件: {len(structure.ending_conditions)}个")
        log.info(f"  Flag框架: {len(structure.flag_framework)}个")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        common_fw = output.get("common_route_framework")
        if not isinstance(common_fw, dict):
            return "common_route_framework必须是对象"
        if not common_fw.get("chapter_count"):
            return "common_route_framework缺少chapter_count"
        if not common_fw.get("chapter_outlines"):
            return "common_route_framework缺少chapter_outlines"

        heroine_fws = output.get("heroine_route_frameworks", [])
        if not isinstance(heroine_fws, list) or len(heroine_fws) == 0:
            return "heroine_route_frameworks必须是非空数组"

        valid_types = ["sweet", "bitter", "tragic", "complex", "hidden", "normal", "bad"]
        for i, fw in enumerate(heroine_fws):
            if not isinstance(fw, dict):
                return f"heroine_route_frameworks[{i}]必须是对象"
            if fw.get("route_type") not in valid_types:
                return f"heroine_route_frameworks[{i}]的route_type无效"
            if not fw.get("interlude_chapters"):
                return f"heroine_route_frameworks[{i}]缺少interlude_chapters"
            if not fw.get("ending_chapter"):
                return f"heroine_route_frameworks[{i}]缺少ending_chapter"

        ending_conditions = output.get("ending_conditions", [])
        if not isinstance(ending_conditions, list):
            return "ending_conditions必须是数组"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        return {
            "structure_id": f"route_struct_fallback_{uuid.uuid4().hex[:8]}",
            "source_outline": "fallback",
            "total_estimated_chapters": 20,
            "common_ratio": 0.7,
            "common_route_framework": {
                "chapter_count": 15,
                "purpose": "介绍世界观和角色",
                "chapter_outlines": [
                    {"chapter_id": "common_ch1", "chapter_name": "相遇", "sequence_order": 1,
                     "chapter_type": "common", "associated_heroine": None,
                     "summary": "与各位女主相遇", "emotional_goal": "建立初步印象"}
                ],
                "heroine_interlude_chapters": [],
                "choice_points": []
            },
            "heroine_route_frameworks": [
                {
                    "heroine_id": "heroine_001", "heroine_name": "女主1", "route_type": "sweet",
                    "interlude_chapters": [
                        {"chapter_id": "heroine_001_interlude_1", "chapter_name": "插曲1", "sequence_order": 3,
                         "summary": "插曲1", "emotional_goal": "发展关系"}
                    ],
                    "ending_chapter": {
                        "chapter_id": "heroine_001_ending", "chapter_name": "结局", "sequence_order": 99,
                        "chapter_type": "ending", "associated_heroine": "heroine_001",
                        "summary": "结局", "emotional_goal": "收束"
                    },
                    "theme": "爱与成长"
                }
            ],
            "true_route_framework": {"chapter_count": 5, "unlock_from": ["heroine_001"],
                                     "unlock_conditions": ["通关个人线"], "outline": "真路线"},
            "ending_conditions": [
                {"heroine_id": "heroine_001", "heroine_name": "女主1", "ending_type": "sweet",
                 "required_affection": 70, "required_flags": [], "forbidden_flags": [],
                 "ending_chapter_id": "heroine_001_ending"}
            ],
            "flag_framework": [],
            "creative_constraints": [],
            "fallback": True
        }
