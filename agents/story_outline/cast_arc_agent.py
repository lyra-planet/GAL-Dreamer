"""
Cast Arc Agent
角色弧光 Agent - 建立人物弧光（起点-裂缝-需求-误区-转变-结局）
"""
import json
import uuid
from typing import Dict, Any, List, Optional, Union
from copy import deepcopy

from agents.base_agent import BaseAgent
from prompts.story_outline.cast_arc_prompt import (
    CAST_ARC_SYSTEM_PROMPT,
    CAST_ARC_HUMAN_PROMPT
)
from models.story_outline.cast_arc import CastArc
from utils.logger import log


class CastArcAgent(BaseAgent):
    """
    角色弧光Agent

    功能:
    - 为主角、女主、配角设计人物弧光
    - 定义角色关系网络
    - 确保与世界观严格一致
    """

    # 类属性配置
    name = "CastArcAgent"
    system_prompt = CAST_ARC_SYSTEM_PROMPT
    human_prompt_template = CAST_ARC_HUMAN_PROMPT
    required_fields = ["protagonist"]
    output_model = CastArc

    # 角色类型
    ROLE_TYPES = ["protagonist", "heroine", "supporting", "antagonist", "minor"]
    # 弧光类型
    ARC_TYPES = ["positive", "negative", "flat", "tragic", "redemptive"]
    # 关系类型
    RELATIONSHIP_TYPES = ["love_interest", "mentor", "rival", "ally", "family", "enemy", "complex"]

    def process(
        self,
        world_setting_json: Dict[str, Any],
        premise_json: Dict[str, Any],
        user_idea: str = "",
        fix_instructions: str = "",
        validate: bool = True
    ) -> CastArc:
        """
        处理角色弧光生成

        Args:
            world_setting_json: 完整的世界观数据
            premise_json: 故事前提数据
            user_idea: 用户原始创意
            fix_instructions: 修复指令（如果有）
            validate: 是否验证输出

        Returns:
            CastArc: 角色弧光集合
        """
        if not world_setting_json:
            raise ValueError("world_setting_json不能为空")
        if not premise_json:
            raise ValueError("premise_json不能为空")

        # 如果没有传user_idea，从world_setting中获取
        if not user_idea:
            user_idea = world_setting_json.get("input", {}).get("user_idea", "")

        log.info("生成角色弧光...")

        # 提取steps中的数据
        steps = world_setting_json.get("steps", {})
        if not steps:
            raise ValueError("world_setting_json中缺少steps数据")

        # 构建prompt字符串
        world_setting_str = self._format_world_setting_for_prompt(steps)
        premise_str = json.dumps(premise_json, ensure_ascii=False, indent=2)

        try:
            result = self.run(
                world_setting_json=world_setting_str,
                premise_json=premise_str,
                user_idea=user_idea,
                fix_instructions=fix_instructions or "无"
            )

            # 生成 cast_arc_id
            if "cast_arc_id" not in result:
                result["cast_arc_id"] = f"cast_arc_{uuid.uuid4().hex[:8]}"

            # 处理角色ID
            result = self._ensure_character_ids(result)

            cast_arc = CastArc(**result)
            self._log_success(cast_arc)
            return cast_arc

        except Exception as e:
            log.error(f"CastArcAgent 处理失败: {e}")
            raise RuntimeError(f"角色弧光生成失败: {e}") from e

    def _ensure_character_ids(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """确保所有角色有唯一ID"""
        id_counter = 1

        def ensure_id(character: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal id_counter
            if "character_id" not in character or not character["character_id"]:
                character["character_id"] = f"char_{id_counter:03d}"
                id_counter += 1
            return character

        # 处理主角
        if "protagonist" in result:
            result["protagonist"] = ensure_id(result["protagonist"])

        # 处理女主
        if "heroines" in result:
            result["heroines"] = [ensure_id(h) for h in result["heroines"]]

        # 处理配角
        if "supporting_cast" in result:
            result["supporting_cast"] = [ensure_id(s) for s in result["supporting_cast"]]

        # 处理反派
        if "antagonists" in result:
            result["antagonists"] = [ensure_id(a) for a in result["antagonists"]]

        return result

    def _format_world_setting_for_prompt(self, steps: Dict[str, Any]) -> str:
        """将世界观数据格式化为prompt字符串"""
        lines = []

        # Story Intake
        if "story_intake" in steps:
            intake = steps["story_intake"]
            lines.append("=== 故事约束 ===")
            if isinstance(intake, dict):
                lines.append(f"题材: {intake.get('genre', '')}")
                lines.append(f"主题: {intake.get('themes', [])}")
                lines.append(f"基调: {intake.get('tone', '')}")
            else:
                lines.append(str(intake))
            lines.append("")

        # Worldbuilding
        if "worldbuilding" in steps:
            world = steps["worldbuilding"]
            lines.append("=== 世界观设定 ===")
            if isinstance(world, dict):
                lines.append(f"时代: {world.get('era', '')}")
                lines.append(f"地点: {world.get('location', '')}")
                lines.append(f"类型: {world.get('type', '')}")
                lines.append(f"核心冲突: {world.get('core_conflict_source', '')}")
                if world.get('rules'):
                    rules = world.get('rules', [])
                    lines.append("世界规则:")
                    for r in rules:
                        if isinstance(r, dict):
                            lines.append(f"  - {r.get('description', '')}")
            else:
                lines.append(str(world))
            lines.append("")

        # Key Elements
        if "key_element" in steps:
            elements = steps["key_element"]
            lines.append("=== 关键元素 ===")
            if isinstance(elements, dict):
                items = elements.get('items', [])
                lines.append("关键道具:")
                for i in items:
                    if isinstance(i, dict):
                        lines.append(f"  - {i.get('name', '')}: {i.get('description', '')}")

                locations = elements.get('locations', [])
                lines.append("关键地点:")
                for l in locations:
                    if isinstance(l, dict):
                        lines.append(f"  - {l.get('name', '')}: {l.get('description', '')}")

                orgs = elements.get('organizations', [])
                lines.append("组织:")
                for o in orgs:
                    if isinstance(o, dict):
                        lines.append(f"  - {o.get('name', '')}: {o.get('description', '')}")
            else:
                lines.append(str(elements))
            lines.append("")

        # Timeline
        if "timeline" in steps:
            timeline = steps["timeline"]
            lines.append("=== 时间线 ===")
            if isinstance(timeline, dict):
                lines.append(f"时代概述: {timeline.get('era_summary', '')}")
                events = timeline.get('events', [])
                lines.append("历史事件:")
                for e in events:
                    if isinstance(e, dict):
                        lines.append(f"  - {e.get('time_period', '')}: {e.get('name', '')} - {e.get('description', '')}")
            else:
                lines.append(str(timeline))
            lines.append("")

        # NPC/Factions (重要！角色必须引用这些)
        if "npc_faction" in steps:
            factions = steps["npc_faction"]
            lines.append("=== 势力/NPC (必须引用) ===")
            if isinstance(factions, dict):
                faction_list = factions.get('factions', [])
                lines.append("势力列表 (faction_id 必须从中引用):")
                for f in faction_list:
                    if isinstance(f, dict):
                        lines.append(f"  faction_id: {f.get('faction_id', '')}")
                        lines.append(f"  名称: {f.get('name', '')}")
                        lines.append(f"  描述: {f.get('description', '')}")
                        lines.append(f"  理念: {f.get('philosophy', '')}")
                        lines.append("")

                npcs = factions.get('key_npcs', [])
                lines.append("现有NPC (可以作为女主/配角):")
                for n in npcs:
                    if isinstance(n, dict):
                        lines.append(f"  npc_id: {n.get('npc_id', '')}")
                        lines.append(f"  名称: {n.get('name', '')}")
                        lines.append(f"  角色: {n.get('role', '')}")
                        lines.append(f"  势力: {n.get('faction_id', '')}")
                        lines.append(f"  性格: {n.get('personality', [])}")
                        lines.append(f"  背景: {n.get('background', '')}")
                        lines.append("")

                lines.append(f"势力关系: {factions.get('relation_map', {})}")
                lines.append(f"冲突点: {factions.get('conflict_points', [])}")
            else:
                lines.append(str(factions))
            lines.append("")

        # Atmosphere
        if "atmosphere" in steps:
            atm = steps["atmosphere"]
            lines.append("=== 氛围设定 ===")
            if isinstance(atm, dict):
                lines.append(f"整体基调: {atm.get('overall_mood', '')}")
                lines.append(f"视觉风格: {atm.get('visual_style', '')}")
            else:
                lines.append(str(atm))
            lines.append("")

        return "\n".join(lines)

    def _log_success(self, cast_arc: CastArc) -> None:
        """记录成功日志"""
        log.info("角色弧光生成成功:")
        log.info(f"  主角: {cast_arc.protagonist.character_name}")
        log.info(f"  女主: {len(cast_arc.heroines)}个")
        log.info(f"  配角: {len(cast_arc.supporting_cast)}个")
        log.info(f"  反派: {len(cast_arc.antagonists)}个")
        for heroine in cast_arc.heroines:
            log.info(f"  - {heroine.character_name}: {heroine.character_arc_type}弧光")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """验证输出"""
        # 检查protagonist
        protagonist = output.get("protagonist")
        if not isinstance(protagonist, dict):
            return "protagonist必须是对象"

        required_char_fields = ["character_id", "character_name", "role_type",
                                "initial_state", "surface_goal", "deep_need",
                                "character_arc_type", "final_state"]
        for field in required_char_fields:
            if not protagonist.get(field):
                return f"protagonist缺少{field}"

        # 检查heroines
        heroines = output.get("heroines")
        if heroines is not None:
            if not isinstance(heroines, list):
                return "heroines必须是数组"
            for i, h in enumerate(heroines):
                if not isinstance(h, dict):
                    return f"heroines[{i}]必须是对象"
                # 不再严格校验枚举值，只要是非空字符串即可
                arc_type = h.get("character_arc_type")
                if not arc_type or not isinstance(arc_type, str):
                    return f"heroines[{i}]的character_arc_type不能为空"

        # 检查supporting_cast
        supporting = output.get("supporting_cast")
        if supporting is not None and not isinstance(supporting, list):
            return "supporting_cast必须是数组"

        # 检查antagonists
        antagonists = output.get("antagonists")
        if antagonists is not None and not isinstance(antagonists, list):
            return "antagonists必须是数组"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        protagonist_id = f"protagonist_{uuid.uuid4().hex[:6]}"
        heroine_id = f"heroine_{uuid.uuid4().hex[:6]}"

        return {
            "cast_arc_id": f"cast_arc_fallback_{uuid.uuid4().hex[:8]}",
            "protagonist": {
                "character_id": protagonist_id,
                "character_name": "主角",
                "role_type": "protagonist",
                "faction_affiliation": None,
                "initial_state": "普通的学生",
                "surface_goal": "过上平静的生活",
                "inciting_incident": "遇到了那个特别的她",
                "deep_need": "找到真正的自我",
                "ghost_or_wound": "过去的孤独",
                "misbelief": "自己不值得被爱",
                "greatest_fear": "再次孤独",
                "growth_nodes": ["学会信任", "勇敢表达", "做出选择"],
                "character_arc_type": "positive",
                "final_state": "获得成长的主角",
                "arc_lesson": "爱需要勇气",
                "relationships": {heroine_id: "love_interest"},
                "secret": "",
                "bottom_line": "不背叛所爱之人"
            },
            "heroines": [
                {
                    "character_id": heroine_id,
                    "character_name": "女主角",
                    "role_type": "heroine",
                    "faction_affiliation": None,
                    "initial_state": "神秘的女孩",
                    "surface_goal": "完成使命",
                    "inciting_incident": "遇见主角",
                    "deep_need": "被理解",
                    "ghost_or_wound": "孤独的过去",
                    "misbelief": "没人能理解自己",
                    "greatest_fear": "被拒绝",
                    "growth_nodes": ["学会信任", "敞开心扉"],
                    "character_arc_type": "positive",
                    "final_state": "被爱温暖的女主",
                    "arc_lesson": "爱可以跨越一切",
                    "relationships": {protagonist_id: "love_interest"},
                    "secret": "其实是外星人",
                    "bottom_line": "不伤害主角"
                }
            ],
            "supporting_cast": [],
            "antagonists": [],
            "relationship_matrix": {},
            "arc_convergence_points": [],
            "character_constraints": [],
            "fallback": True
        }
