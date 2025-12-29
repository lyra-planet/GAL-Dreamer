"""
Story Premise Agent
故事前提 Agent - 提炼GAL的卖点/主题/主冲突/情感基调
"""
import json
import uuid
from typing import Dict, Any, List, Optional, Union

from agents.base_agent import BaseAgent
from prompts.story_outline.premise_prompt import (
    STORY_PREMISE_SYSTEM_PROMPT,
    STORY_PREMISE_HUMAN_PROMPT
)
from models.story_outline.premise import StoryPremise
from utils.logger import log


class StoryPremiseAgent(BaseAgent):
    """
    故事前提Agent

    功能:
    - 从世界观JSON中提炼卖点、主题、主冲突
    - 设定情感基调
    - 定义创作边界，防止后续发散
    """

    # 类属性配置
    name = "StoryPremiseAgent"
    system_prompt = STORY_PREMISE_SYSTEM_PROMPT
    human_prompt_template = STORY_PREMISE_HUMAN_PROMPT
    required_fields = ["hook", "core_question", "selling_points", "primary_genre",
                       "core_themes", "main_conflict_hook", "emotional_tone",
                       "emotional_keywords", "creative_boundaries"]
    output_model = StoryPremise

    # 情感基调类型
    EMOTIONAL_TONES = ["温馨", "治愈", "忧郁", "沉重", "悬疑", "紧张", "轻松", "悲喜交加", "其他"]

    def process(
        self,
        world_setting_json: Dict[str, Any],
        user_idea: str = "",
        fix_instructions: str = "",
        validate: bool = True
    ) -> StoryPremise:
        """
        处理故事前提生成

        Args:
            world_setting_json: 完整的世界观数据（从world_setting.json读取）
            user_idea: 用户原始创意
            fix_instructions: 修复指令（如果有）
            validate: 是否验证输出

        Returns:
            StoryPremise: 故事前提
        """
        if not world_setting_json:
            raise ValueError("world_setting_json不能为空")

        # 提取steps中的数据和user_idea
        steps = world_setting_json.get("steps", {})
        if not steps:
            raise ValueError("world_setting_json中缺少steps数据")

        # 如果没有传user_idea，从input中获取
        if not user_idea:
            user_idea = world_setting_json.get("input", {}).get("user_idea", "")

        log.info("提炼故事前提...")

        # 构建世界设字符串（用于prompt）
        world_setting_str = self._format_world_setting_for_prompt(steps)

        try:
            result = self.run(
                world_setting_json=world_setting_str,
                user_idea=user_idea,
                fix_instructions=fix_instructions or "无"
            )

            # 生成 premise_id
            if "premise_id" not in result:
                result["premise_id"] = f"premise_{uuid.uuid4().hex[:8]}"

            premise = StoryPremise(**result)
            self._log_success(premise)
            return premise

        except Exception as e:
            log.error(f"StoryPremiseAgent 处理失败: {e}")
            raise RuntimeError(f"故事前提生成失败: {e}") from e

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
                lines.append(f"必备: {intake.get('must_have', [])}")
                lines.append(f"禁止: {intake.get('forbidden', [])}")
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
                lines.append(f"描述: {world.get('description', '')}")
                if world.get('rules'):
                    lines.append(f"规则: {len(world.get('rules', []))}条")
            else:
                lines.append(str(world))
            lines.append("")

        # Key Elements
        if "key_element" in steps:
            elements = steps["key_element"]
            lines.append("=== 关键元素 ===")
            if isinstance(elements, dict):
                items = elements.get('items', [])
                locations = elements.get('locations', [])
                orgs = elements.get('organizations', [])
                lines.append(f"道具: {len(items)}个 - {[i.get('name') if isinstance(i, dict) else i for i in items]}")
                lines.append(f"地点: {len(locations)}个 - {[l.get('name') if isinstance(l, dict) else l for l in locations]}")
                lines.append(f"组织: {len(orgs)}个 - {[o.get('name') if isinstance(o, dict) else o for o in orgs]}")
            else:
                lines.append(str(elements))
            lines.append("")

        # Timeline
        if "timeline" in steps:
            timeline = steps["timeline"]
            lines.append("=== 时间线 ===")
            if isinstance(timeline, dict):
                lines.append(f"当前年份: {timeline.get('current_year', '')}")
                lines.append(f"时代概述: {timeline.get('era_summary', '')}")
                events = timeline.get('events', [])
                lines.append(f"关键事件: {len(events)}个")
                for e in events[:5]:
                    if isinstance(e, dict):
                        lines.append(f"  - {e.get('time_period', '')}: {e.get('name', '')} ({e.get('importance', '')})")
            else:
                lines.append(str(timeline))
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

        # NPC/Factions
        if "npc_faction" in steps:
            factions = steps["npc_faction"]
            lines.append("=== 势力/NPC ===")
            if isinstance(factions, dict):
                faction_list = factions.get('factions', [])
                npcs = factions.get('key_npcs', [])
                lines.append(f"势力: {len(faction_list)}个")
                for f in faction_list:
                    if isinstance(f, dict):
                        lines.append(f"  - {f.get('name', '')}: {f.get('influence_level', '')}")
                lines.append(f"关键NPC: {len(npcs)}个")
                for n in npcs:
                    if isinstance(n, dict):
                        lines.append(f"  - {n.get('name', '')}: {n.get('role', '')}")
            else:
                lines.append(str(factions))
            lines.append("")

        return "\n".join(lines)

    def _log_success(self, premise: StoryPremise) -> None:
        """记录成功日志"""
        log.info("故事前提生成成功:")
        log.info(f"  核心钩子: {premise.hook}")
        log.info(f"  核心问题: {premise.core_question}")
        log.info(f"  主类型: {premise.primary_genre}")
        log.info(f"  情感基调: {premise.emotional_tone}")
        log.info(f"  卖点: {len(premise.selling_points)}个")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """验证输出"""
        # 检查hook
        hook = output.get("hook")
        if not hook or not isinstance(hook, str) or not hook.strip():
            return "hook必须是非空字符串"

        # 检查core_question
        if not output.get("core_question"):
            return "core_question不能为空"

        # 检查selling_points
        selling_points = output.get("selling_points")
        if not isinstance(selling_points, list) or len(selling_points) == 0:
            return "selling_points必须是非空数组"

        # 检查emotional_tone
        tone = output.get("emotional_tone")
        if tone not in self.EMOTIONAL_TONES:
            return f"emotional_tone必须是以下之一: {', '.join(self.EMOTIONAL_TONES)}"

        # 检查core_themes
        themes = output.get("core_themes")
        if not isinstance(themes, list) or len(themes) < 2:
            return "core_themes必须包含至少2个主题"

        # 检查emotional_keywords
        keywords = output.get("emotional_keywords")
        if not isinstance(keywords, list) or len(keywords) == 0:
            return "emotional_keywords不能为空"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        return {
            "premise_id": f"premise_fallback_{uuid.uuid4().hex[:8]}",
            "hook": "一个关于爱与选择的故事",
            "core_question": "爱情是否值得牺牲一切？",
            "selling_points": ["独特的世界观", "深刻的角色成长", "多结局设计"],
            "primary_genre": "恋爱",
            "sub_genres": ["奇幻"],
            "core_themes": ["爱情", "选择", "成长"],
            "main_conflict_hook": "爱情与责任的冲突",
            "emotional_tone": "温馨",
            "emotional_keywords": ["温暖", "感动", "成长", "选择"],
            "target_audience": ["喜欢恋爱故事的玩家"],
            "forbidden_elements": [],
            "must_have_elements": [],
            "world_setting_references": [],
            "creative_boundaries": "保持与世界观一致",
            "fallback": True
        }


if __name__ == "__main__":
    # 测试Story Premise Agent
    agent = StoryPremiseAgent()

    # 模拟输入
    test_input = {
        "steps": {
            "story_intake": {
                "genre": "奇幻恋爱",
                "themes": ["爱情", "异界与现实的冲突"],
                "tone": "神秘而略带忧郁",
                "must_have": ["单女主", "多结局"],
                "forbidden": ["恐怖", "血腥"]
            },
            "worldbuilding": {
                "era": "现代",
                "location": "镜界与现实的交界",
                "type": "奇幻",
                "core_conflict_source": "主角需要在爱情和守护世界之间选择",
                "description": "一个现实与异界交错的世界"
            },
            "key_element": {
                "items": [{"name": "镜之碎片", "importance": "critical"}],
                "locations": [{"name": "镜之门"}],
                "organizations": [{"name": "镜界守护者"}]
            },
            "timeline": {
                "current_year": "现代",
                "era_summary": "镜界与现实界限逐渐模糊",
                "events": [
                    {"name": "封印仪式", "time_period": "古代", "importance": "critical"},
                    {"name": "主角进入镜界", "time_period": "故事开始前", "importance": "major"}
                ]
            },
            "atmosphere": {
                "overall_mood": "神秘而略带忧郁",
                "visual_style": "梦幻写实"
            },
            "npc_faction": {
                "factions": [
                    {"name": "镜界守护者", "influence_level": "local"},
                    {"name": "破碎灵魂", "influence_level": "local"}
                ],
                "key_npcs": [
                    {"name": "艾利斯", "role": "守护者领袖"},
                    {"name": "米拉", "role": "引导者"}
                ]
            }
        }
    }

    try:
        premise = agent.process(test_input)
        print("\n" + "=" * 50)
        print("Story Premise Agent 测试成功!")
        print("=" * 50)
        print(f"核心钩子: {premise.hook}")
        print(f"核心问题: {premise.core_question}")
        print(f"卖点: {premise.selling_points}")
        print(f"情感基调: {premise.emotional_tone}")
        print("=" * 50)
    except Exception as e:
        print(f"测试失败: {e}")
