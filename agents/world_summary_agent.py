"""
World Summary Agent
世界观摘要Agent - 用自然语言汇总描述整个世界观
"""
from typing import Dict, Any, List, Optional, Union
import uuid
import json

from .base_agent import BaseAgent
from prompts.world_summary_prompt import (
    WORLD_SUMMARY_SYSTEM_PROMPT,
    WORLD_SUMMARY_HUMAN_PROMPT
)
from models.world_summary import WorldSummary
from utils.logger import log


class WorldSummaryAgent(BaseAgent):
    """
    世界观摘要Agent

    功能:
    - 整合所有世界观数据
    - 生成自然语言的世界观摘要
    - 标注可攻略角色
    - 为后续剧情提供方向
    """

    # 类属性配置
    name = "WorldSummaryAgent"
    system_prompt = WORLD_SUMMARY_SYSTEM_PROMPT
    human_prompt_template = WORLD_SUMMARY_HUMAN_PROMPT
    required_fields = [
        "world_overview",
        "setting_description",
        "key_rules",
        "key_elements_summary",
        "timeline_summary",
        "atmosphere_description",
        "factions_summary",
        "story_potential"
    ]
    output_model = WorldSummary

    def process(
        self,
        story_constraints: Dict[str, Any],
        world_setting: Dict[str, Any],
        key_elements: Dict[str, Any],
        timeline: Dict[str, Any],
        atmosphere: Dict[str, Any],
        factions: Dict[str, Any],
        user_idea: str = "",
        validate: bool = True
    ) -> WorldSummary:
        """
        处理世界观摘要生成

        Args:
            story_constraints: 故事约束条件
            world_setting: 世界观设定
            key_elements: 关键元素
            timeline: 时间线
            atmosphere: 氛围设定
            factions: 势力设定
            user_idea: 用户原始创意
            validate: 是否验证输出

        Returns:
            WorldSummary: 世界观摘要
        """
        log.info("生成世界观摘要...")

        # 参数检查
        for name, value in [
            ("world_setting", world_setting),
            ("key_elements", key_elements),
            ("timeline", timeline),
            ("atmosphere", atmosphere),
            ("factions", factions),
        ]:
            if not value:
                raise ValueError(f"{name}不能为空")

        try:
            # 构建完整的输入数据
            world_rules = world_setting.get("rules", [])
            key_items = key_elements.get("items", [])
            key_locations = key_elements.get("locations", [])
            organizations = key_elements.get("organizations", [])
            terms = key_elements.get("terms", [])

            events = timeline.get("events", [])
            scene_presets = atmosphere.get("scene_presets", [])

            factions_list = factions.get("factions", [])
            key_npcs = factions.get("key_npcs", [])
            relation_map = factions.get("relation_map", {})

            result = self.run(
                user_idea=user_idea,
                genre=story_constraints.get("genre", ""),
                themes=", ".join(story_constraints.get("themes", [])),
                tone=story_constraints.get("tone", ""),
                # 世界观
                era=world_setting.get("era", ""),
                location=world_setting.get("location", ""),
                world_type=world_setting.get("type", ""),
                core_conflict=world_setting.get("core_conflict_source", ""),
                world_description=world_setting.get("description", ""),
                world_rules=json.dumps(world_rules, ensure_ascii=False),
                # 关键元素
                key_items=json.dumps(key_items, ensure_ascii=False),
                key_locations=json.dumps(key_locations, ensure_ascii=False),
                organizations=json.dumps(organizations, ensure_ascii=False),
                terms=json.dumps(terms, ensure_ascii=False),
                # 时间线
                current_year=timeline.get("current_year", ""),
                era_summary=timeline.get("era_summary", ""),
                events=json.dumps(events, ensure_ascii=False),
                # 氛围
                overall_mood=atmosphere.get("overall_mood", ""),
                visual_style=atmosphere.get("visual_style", ""),
                scene_presets=json.dumps(scene_presets, ensure_ascii=False),
                # 势力
                factions_json=json.dumps(factions_list, ensure_ascii=False),
                key_npcs=json.dumps(key_npcs, ensure_ascii=False),
                relation_map=json.dumps(relation_map, ensure_ascii=False),
                conflict_points=", ".join(factions.get("conflict_points", []))
            )

            if "summary_id" not in result:
                result["summary_id"] = f"summary_{uuid.uuid4().hex[:8]}"

            summary = WorldSummary(**result)
            self._log_success(summary)
            return summary

        except Exception as e:
            log.error(f"WorldSummaryAgent 处理失败: {e}")
            raise RuntimeError(f"世界观摘要生成失败: {e}") from e

    def _log_success(self, summary: WorldSummary) -> None:
        """记录成功日志"""
        log.info("世界观摘要生成成功:")
        log.info(f"  概览: {summary.world_overview[:50]}...")
        log.info(f"  可攻略角色: {len(summary.available_heroines)}个")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """验证输出 - Pydantic验证由BaseAgent自动完成"""
        # 只做额外的自定义验证
        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        return {
            "summary_id": f"summary_fallback_{uuid.uuid4().hex[:8]}",
            "world_overview": "世界观摘要生成失败",
            "setting_description": "无法生成摘要",
            "key_rules": "无法生成规则摘要",
            "key_elements_summary": "无法生成元素摘要",
            "timeline_summary": "无法生成时间线摘要",
            "atmosphere_description": "无法生成氛围描述",
            "factions_summary": "无法生成势力摘要",
            "story_potential": "无法生成故事潜力分析",
            "available_heroines": [],
            "fallback": True
        }


if __name__ == "__main__":
    # 测试 WorldSummaryAgent
    agent = WorldSummaryAgent()

    test_data = {
        "story_constraints": {
            "genre": "恋爱",
            "themes": ["青春", "成长"],
            "tone": "温馨"
        },
        "world_setting": {
            "era": "现代",
            "location": "高中",
            "type": "现实",
            "core_conflict_source": "青春的选择",
            "description": "普通的高中校园",
            "rules": [{"rule_id": "r1", "description": "规则1"}]
        },
        "key_elements": {
            "items": [{"item_id": "i1", "name": "道具1"}],
            "locations": [{"location_id": "l1", "name": "地点1"}],
            "organizations": [],
            "terms": []
        },
        "timeline": {
            "current_year": "2024年",
            "era_summary": "普通的时代",
            "events": []
        },
        "atmosphere": {
            "overall_mood": "温馨",
            "visual_style": "清新治愈",
            "scene_presets": []
        },
        "factions": {
            "factions": [],
            "key_npcs": [],
            "relation_map": {},
            "conflict_points": []
        },
        "user_idea": "一个发生在高中的青春恋爱故事"
    }

    try:
        summary = agent.process(**test_data)
        print("\n" + "=" * 50)
        print("WorldSummaryAgent 测试成功!")
        print("=" * 50)
        print(f"概览: {summary.world_overview}")
        print(f"可攻略角色: {len(summary.available_heroines)}个")
        print("=" * 50)
    except Exception as e:
        print(f"测试失败: {e}")
