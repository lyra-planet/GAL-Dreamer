"""
Npc Faction Agent
NPC势力Agent - 设计世界中的势力体系和NPC
"""
from typing import Dict, Any, List, Optional, Union
import uuid

from agents.base_agent import BaseAgent
from prompts.worldbuilding.faction_prompt import (
    FACTION_SYSTEM_PROMPT,
    FACTION_HUMAN_PROMPT
)
from models.worldbuilding.faction import WorldFactions
from utils.logger import log


class NpcFactionAgent(BaseAgent):
    """
    NPC势力Agent

    功能:
    - 设计势力/派系
    - 建立势力关系网络
    - 生成关键NPC
    - 定义势力冲突点
    """

    # 类属性配置
    name = "NpcFactionAgent"
    system_prompt = FACTION_SYSTEM_PROMPT
    human_prompt_template = FACTION_HUMAN_PROMPT
    required_fields = ["factions", "key_npcs"]
    output_model = WorldFactions

    # 影响力级别
    INFLUENCE_LEVELS = ["local", "regional", "national", "global"]
    # 关系类型
    RELATION_TYPES = ["allied", "neutral", "rival", "hostile", "unknown"]
    # 态度类型
    STANCE_TYPES = ["friendly", "neutral", "hostile", "variable"]

    def process(
        self,
        story_constraints: Dict[str, Any],
        world_setting: Dict[str, Any],
        key_elements: Dict[str, Any],
        timeline: Dict[str, Any],
        atmosphere: Dict[str, Any],
        user_idea: str = "",
        validate: bool = True
    ) -> WorldFactions:
        """
        处理势力体系生成

        Args:
            story_constraints: 故事约束条件
            world_setting: 世界观设定
            key_elements: 关键元素
            timeline: 时间线(必选)
            atmosphere: 氛围设定(必选)
            user_idea: 用户原始创意
            validate: 是否验证输出

        Returns:
            WorldFactions: 世界势力体系
        """
        if not world_setting:
            raise ValueError("world_setting不能为空")
        if not timeline:
            raise ValueError("timeline不能为空")
        if not atmosphere:
            raise ValueError("atmosphere不能为空")

        log.info("生成势力体系...")

        try:
            # 提取组织信息
            orgs = key_elements.get("organizations", [])
            orgs_desc = "\n".join([
                f"- {org.get('name', '')}: {org.get('description', '')} (目的: {org.get('purpose', '')})"
                for org in orgs
            ]) if orgs else "无特殊组织"

            # 提取时间线信息
            timeline_summary = "历史背景: " + timeline.get("era_summary", "无特殊历史")

            # 提取氛围信息
            mood_info = f"整体基调: {atmosphere.get('overall_mood', '')}"
            visual_style = f"视觉风格: {atmosphere.get('visual_style', '')}"

            result = self.run(
                genre=story_constraints.get("genre", ""),
                themes=", ".join(story_constraints.get("themes", [])),
                tone=story_constraints.get("tone", ""),
                era=world_setting.get("era", ""),
                location=world_setting.get("location", ""),
                world_type=world_setting.get("type", ""),
                core_conflict=world_setting.get("core_conflict_source", ""),
                world_description=world_setting.get("description", ""),
                organizations_desc=orgs_desc,
                timeline_summary=timeline_summary,
                mood_info=mood_info,
                visual_style=visual_style,
                user_idea=user_idea
            )

            if "factions_id" not in result:
                result["factions_id"] = f"factions_{uuid.uuid4().hex[:8]}"

            factions = WorldFactions(**result)
            self._log_success(factions)
            return factions

        except Exception as e:
            log.error(f"NpcFactionAgent 处理失败: {e}")
            raise RuntimeError(f"势力体系生成失败: {e}") from e

    def _log_success(self, factions: WorldFactions) -> None:
        """记录成功日志"""
        log.info("势力体系生成成功:")
        log.info(f"  势力数量: {len(factions.factions)}")
        log.info(f"  关键NPC: {len(factions.key_npcs)}个")
        log.info(f"  冲突点: {len(factions.conflict_points)}个")

        for faction in factions.factions:
            log.info(f"  - {faction.name} ({faction.influence_level})")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """验证输出"""
        # 检查factions
        factions = output.get("factions")
        if not isinstance(factions, list):
            return "factions必须是数组类型"
        if len(factions) == 0:
            return "factions不能为空"

        faction_ids = set()
        for i, faction in enumerate(factions):
            if not isinstance(faction, dict):
                return f"factions[{i}]必须是对象"

            required_fields = ["faction_id", "name", "description", "philosophy", "influence_level"]
            for field in required_fields:
                if not faction.get(field):
                    return f"factions[{i}]缺少{field}"

            faction_id = faction.get("faction_id")
            if faction_id in faction_ids:
                return f"factions[{i}]的faction_id重复: {faction_id}"
            faction_ids.add(faction_id)

            influence = faction.get("influence_level")
            if influence not in self.INFLUENCE_LEVELS:
                return f"factions[{i}]的influence_level必须是: {', '.join(self.INFLUENCE_LEVELS)}"

            # 检查relations
            relations = faction.get("relations")
            if relations is not None:
                if not isinstance(relations, list):
                    return f"factions[{i}]的relations必须是数组类型"
                for j, rel in enumerate(relations):
                    if not isinstance(rel, dict):
                        return f"factions[{i}].relations[{j}]必须是对象"
                    rel_type = rel.get("relation_type", "neutral")
                    if rel_type not in self.RELATION_TYPES:
                        return f"factions[{i}].relations[{j}]的relation_type必须是: {', '.join(self.RELATION_TYPES)}"

        # 检查key_npcs
        npcs = output.get("key_npcs")
        if npcs is not None:
            if not isinstance(npcs, list):
                return "key_npcs必须是数组类型"
            for i, npc in enumerate(npcs):
                if not isinstance(npc, dict):
                    return f"key_npcs[{i}]必须是对象"

                if not npc.get("npc_id"):
                    return f"key_npcs[{i}]缺少npc_id"
                if not npc.get("name"):
                    return f"key_npcs[{i}]缺少name"
                if not npc.get("role"):
                    return f"key_npcs[{i}]缺少role"
                if not npc.get("faction_id"):
                    return f"key_npcs[{i}]缺少faction_id"

                stance = npc.get("stance_toward_player", "neutral")
                if stance not in self.STANCE_TYPES:
                    return f"key_npcs[{i}]的stance_toward_player必须是: {', '.join(self.STANCE_TYPES)}"

        # 检查relation_map
        relation_map = output.get("relation_map")
        if relation_map is not None and not isinstance(relation_map, dict):
            return "relation_map必须是对象类型"

        # 检查conflict_points
        conflict_points = output.get("conflict_points")
        if conflict_points is not None and not isinstance(conflict_points, list):
            return "conflict_points必须是数组类型"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        return {
            "factions_id": f"factions_fallback_{uuid.uuid4().hex[:8]}",
            "factions": [
                {
                    "faction_id": "faction_default",
                    "name": "普通群体",
                    "description": "普通的群体",
                    "philosophy": "普通的生活",
                    "influence_level": "local",
                    "member_count": 10,
                    "relations": []
                }
            ],
            "key_npcs": [
                {
                    "npc_id": "npc_default_1",
                    "name": "普通NPC",
                    "role": "普通人",
                    "faction_id": "faction_default",
                    "personality": ["普通"],
                    "background": "普通的背景",
                    "stance_toward_player": "neutral"
                }
            ],
            "relation_map": {},
            "conflict_points": [],
            "fallback": True
        }
