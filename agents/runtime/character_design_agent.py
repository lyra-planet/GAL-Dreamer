"""
角色设计 Agent
支持半路创建新角色，或根据剧情需要动态生成角色
"""
import json
import uuid
from typing import Dict, Any, List, Optional, Union

from agents.base_agent import BaseAgent
from prompts.runtime.character_design_prompt import (
    CHARACTER_DESIGN_SYSTEM_PROMPT,
    CHARACTER_DESIGN_HUMAN_PROMPT
)
from models.runtime.character import RuntimeCharacter, HeroineCharacter, ProtagonistCharacter
from utils.logger import log


class CharacterDesignAgent(BaseAgent):
    """
    角色设计Agent

    功能:
    - 根据剧情需要动态生成新角色
    - 设计角色的外观、性格、背景
    - 确保新角色与世界观一致
    """

    name = "CharacterDesignAgent"
    system_prompt = CHARACTER_DESIGN_SYSTEM_PROMPT
    human_prompt_template = CHARACTER_DESIGN_HUMAN_PROMPT
    required_fields = [
        "character_name", "role_type", "personality",
        "background_story", "surface_goal", "deep_need"
    ]

    def design(
        self,
        design_request: str,
        world_context: Dict[str, Any],
        existing_characters: Dict[str, Any],
        role_hint: Optional[str] = None,
        is_heroine: bool = False,
        is_antagonist: bool = False,
    ) -> RuntimeCharacter:
        """
        设计一个新角色

        Args:
            design_request: 设计需求描述
            world_context: 世界观上下文
            existing_characters: 现有角色信息（避免重复）
            role_hint: 角色类型提示
            is_heroine: 是否为可攻略女主
            is_antagonist: 是否为反派

        Returns:
            设计好的角色
        """
        log.info(f"CharacterDesignAgent 设计新角色... 需求: {design_request[:50]}...")

        # 构建上下文
        world_str = self._format_world_context(world_context)
        existing_str = self._format_existing_characters(existing_characters)

        # 确定角色类型
        if is_heroine:
            role_type = "heroine"
        elif is_antagonist:
            role_type = "antagonist"
        elif role_hint:
            role_type = role_hint
        else:
            role_type = "supporting"

        result = self.run(
            design_request=design_request,
            world_context=world_str,
            existing_characters=existing_str,
            role_type=role_type
        )

        # 生成ID
        result["character_id"] = f"char_{uuid.uuid4().hex[:8]}"

        # 根据类型创建模型
        if role_type == "heroine":
            character = HeroineCharacter(**result)
        elif role_type == "protagonist":
            character = ProtagonistCharacter(**result)
        else:
            character = RuntimeCharacter(**result)

        self._log_success(character)
        return character

    def refine(
        self,
        character: RuntimeCharacter,
        refinement_request: str,
        context: Dict[str, Any]
    ) -> RuntimeCharacter:
        """
        完善现有角色

        Args:
            character: 现有角色
            refinement_request: 完善需求
            context: 上下文信息

        Returns:
            完善后的角色
        """
        log.info(f"CharacterDesignAgent 完善角色: {character.character_name}")

        # 获取当前角色数据
        current_data = character.model_dump()

        result = self.run(
            design_request=refinement_request,
            world_context=self._format_world_context(context),
            existing_characters="",  # 不需要
            role_type=character.role_type,
            current_character_data=json.dumps(current_data, ensure_ascii=False, indent=2),
            is_refinement=True
        )

        # 更新角色数据（保留ID和关键信息）
        result["character_id"] = character.character_id
        result["created_at"] = character.created_at

        # 根据类型创建模型
        if character.role_type == "heroine":
            updated = HeroineCharacter(**result)
        elif character.role_type == "protagonist":
            updated = ProtagonistCharacter(**result)
        else:
            updated = RuntimeCharacter(**result)

        log.info(f"角色完善完成: {character.character_name}")
        return updated

    def _format_world_context(self, context: Dict[str, Any]) -> str:
        """格式化世界观上下文"""
        lines = ["=== 世界观背景 ==="]

        # 从story_outline提取
        premise = context.get("premise", {})
        if premise:
            lines.append(f"故事核心: {premise.get('hook', '')}")
            lines.append(f"类型: {premise.get('primary_genre', '')}")
            lines.append(f"主题: {', '.join(premise.get('core_themes', []))}")
            lines.append(f"情感基调: {premise.get('emotional_tone', '')}")

        # 世界观设定
        world_setting = context.get("world_setting", {})
        if world_setting:
            lines.append(f"\n时代: {world_setting.get('era', '')}")
            lines.append(f"地点: {world_setting.get('location', '')}")
            lines.append(f"类型: {world_setting.get('type', '')}")

        # 势力信息
        factions = context.get("factions", {})
        if factions:
            lines.append(f"\n势力:")
            for faction in factions.get("factions", [])[:5]:
                lines.append(f"  - {faction.get('name', '')}: {faction.get('description', '')}")

        return "\n".join(lines)

    def _format_existing_characters(self, characters: Dict[str, Any]) -> str:
        """格式化现有角色"""
        if not characters:
            return "=== 现有角色 ===\n(无)"

        lines = ["=== 现有角色 ==="]

        for char_id, char_data in characters.items():
            name = char_data.get("character_name", "未知")
            role = char_data.get("role_type", "unknown")
            personality = char_data.get("personality", [])
            goal = char_data.get("surface_goal", "")

            lines.append(f"\n[{name}] ({role})")
            if personality:
                lines.append(f"  性格: {', '.join(personality)}")
            if goal:
                lines.append(f"  目标: {goal}")

        return "\n".join(lines)

    def _log_success(self, character: RuntimeCharacter) -> None:
        """记录成功日志"""
        log.info("角色设计成功:")
        log.info(f"  ID: {character.character_id}")
        log.info(f"  姓名: {character.character_name}")
        log.info(f"  类型: {character.role_type}")
        log.info(f"  性格: {', '.join(character.personality)}")
        log.info(f"  目标: {character.surface_goal}")
        log.info(f"  深层需求: {character.deep_need}")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """验证输出"""
        # 检查必填字段
        required = ["character_name", "role_type", "personality", "background_story"]
        for field in required:
            if not output.get(field):
                return f"缺少必填字段: {field}"

        # 检查role_type
        valid_roles = ["protagonist", "heroine", "supporting", "antagonist", "minor"]
        if output.get("role_type") not in valid_roles:
            return f"role_type必须是以下之一: {', '.join(valid_roles)}"

        # 检查personality是列表
        personality = output.get("personality")
        if not isinstance(personality, list) or len(personality) == 0:
            return "personality必须是非空列表"

        # 检查好感度相关字段范围
        affection = output.get("affection_value", 50)
        if not isinstance(affection, int) or affection < 0 or affection > 100:
            return "affection_value必须是0-100的整数"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        return {
            "character_id": f"char_fallback_{uuid.uuid4().hex[:8]}",
            "character_name": "神秘角色",
            "role_type": "supporting",
            "appearance": {
                "hair": "未知",
                "eyes": "未知",
                "height": "中等",
                "style": "普通"
            },
            "personality": ["神秘", "温和"],
            "speaking_style": {
                "tone": "平静",
                "catchphrase": ""
            },
            "background_story": "一位神秘的过客",
            "origin": "未知",
            "surface_goal": "完成自己的使命",
            "deep_need": "找到归属",
            "ghost_or_wound": "过去的经历",
            "misbelief": "没有人能理解",
            "greatest_fear": "孤独",
            "growth_nodes": [],
            "arc_type": "flat",
            "secret": "无",
            "bottom_line": "不伤害无辜",
            "affection_value": 50,
            "trust_level": 50,
            "fallback": True
        }


if __name__ == "__main__":
    # 测试角色设计Agent
    agent = CharacterDesignAgent()

    # 模拟上下文
    world_context = {
        "premise": {
            "hook": "在一所隐藏着幻想精灵的高中里，与四位精灵展开恋爱旅程",
            "primary_genre": "恋爱",
            "core_themes": ["爱", "成长"],
            "emotional_tone": "温馨"
        },
        "world_setting": {
            "era": "现代",
            "location": "星之丘学园",
            "type": "幻想校园"
        },
        "factions": {
            "factions": [
                {"name": "精灵守望者", "description": "维护精灵与人类平衡的组织"},
                {"name": "幻想研究社", "description": "研究精灵现象的社团"}
            ]
        }
    }

    existing_characters = {
        "heroine_001": {
            "character_name": "小飞翔",
            "role_type": "heroine",
            "personality": ["活泼", "好动", "缺乏自信"],
            "surface_goal": "获得主角的认可"
        },
        "heroine_002": {
            "character_name": "EO",
            "role_type": "heroine",
            "personality": ["冷静", "理智", "封闭"],
            "surface_goal": "保持独立"
        }
    }

    try:
        # 设计一个新配角
        new_character = agent.design(
            design_request="需要一位神秘的转校生，实际上是精灵守望者的秘密探员，暗中观察主角",
            world_context=world_context,
            existing_characters=existing_characters,
            role_hint="supporting"
        )

        print("\n" + "=" * 50)
        print("角色设计测试成功!")
        print("=" * 50)
        print(f"ID: {new_character.character_id}")
        print(f"姓名: {new_character.character_name}")
        print(f"类型: {new_character.role_type}")
        print(f"性格: {', '.join(new_character.personality)}")
        print(f"目标: {new_character.surface_goal}")
        print(f"深层需求: {new_character.deep_need}")
        print(f"背景: {new_character.background_story}")
        print("=" * 50)

    except Exception as e:
        print(f"测试失败: {e}")
