"""
Narrator Agent
Galgame文本生成 Agent
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from prompts.narrator_prompt import (
    NARRATOR_SYSTEM_PROMPT,
    NARRATOR_HUMAN_PROMPT
)
from utils.logger import log


class NarratorAgent(BaseAgent):
    """Galgame文本生成Agent - 将结构转化为游戏文本"""

    def __init__(self):
        """初始化Narrator Agent"""
        # Narrator不需要结构化输出，因为输出的是自然语言文本
        super().__init__(
            name="NarratorAgent",
            system_prompt=NARRATOR_SYSTEM_PROMPT,
            human_prompt_template=NARRATOR_HUMAN_PROMPT,
            use_structured_output=False  # 不使用JSON输出
        )

    def process(self, scene_structure: Dict[str, Any], character_actions: List[Dict[str, Any]], tone: str, characters: List[str]) -> str:
        """
        生成Galgame风格文本

        Args:
            scene_structure: 场景结构
            character_actions: 角色行为列表
            tone: 整体基调
            characters: 在场角色列表

        Returns:
            str: 生成的Galgame文本
        """
        log.info(f"生成场景文本，基调: {tone}")

        # 格式化角色行为
        actions_str = self._format_actions(character_actions)

        # 格式化在场角色
        chars_str = ", ".join(characters)

        # 运行Agent - 传入原始数据，让 LangChain 处理格式化
        result = self.run(
            scene_structure=scene_structure,
            character_actions=actions_str,
            tone=tone,
            characters=chars_str
        )

        # Narrator返回的是文本，不是字典
        if isinstance(result, dict):
            # 如果意外返回了字典，提取文本内容
            narrative_text = result.get("text", result.get("narrative", str(result)))
        else:
            narrative_text = str(result)

        log.info(f"文本生成成功，长度: {len(narrative_text)}字符")

        return narrative_text

    def _format_actions(self, actions: List[Dict[str, Any]]) -> str:
        """格式化角色行为"""
        if not actions:
            return "无特殊动作"

        formatted = []
        for action in actions:
            if isinstance(action, dict):
                action_type = action.get("action_type", "unknown")
                content = action.get("content", "")
                character = action.get("character", "")
                formatted.append(f"- {character}: {action_type} - {content}")
            else:
                formatted.append(f"- {action}")

        return "\n".join(formatted)

    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        Narrator输出验证（重写，因为输出是文本）

        Args:
            output: Agent输出

        Returns:
            是否有效
        """
        # Narrator输出文本，只要非空即可
        if isinstance(output, str):
            return len(output.strip()) > 0
        if isinstance(output, dict):
            return bool(output)
        return True

    def generate_scene_text(self, scene: Dict[str, Any], characters_dict: Dict[str, Dict[str, Any]], tone: str = "温馨") -> str:
        """
        生成单个场景的文本（便捷方法）

        Args:
            scene: 场景信息，包含location, time, characters_present等
            characters_dict: 角色字典，key为角色ID，value为角色信息
            tone: 整体基调

        Returns:
            str: 生成的场景文本
        """
        scene_structure = {
            "location": scene.get("location", "未知地点"),
            "time": scene.get("time", "未知时间"),
            "scene_type": scene.get("scene_type", "对话场景")
        }

        # 提取在场角色
        characters_present = scene.get("characters_present", [])
        character_names = []
        for char_id in characters_present:
            if char_id in characters_dict:
                char_info = characters_dict[char_id]
                if isinstance(char_info, dict):
                    character_names.append(char_info.get("name", char_id))
                else:
                    character_names.append(str(char_id))
            else:
                character_names.append(char_id)

        # 如果有预定义的动作
        character_actions = scene.get("actions", [])

        return self.process(
            scene_structure=scene_structure,
            character_actions=character_actions,
            tone=tone,
            characters=character_names
        )


if __name__ == "__main__":
    # 测试Narrator Agent
    agent = NarratorAgent()

    test_scene = {
        "location": "教室",
        "time": "放学后",
        "scene_type": "对话场景",
        "characters_present": ["protagonist", "heroine_a"]
    }

    test_characters = {
        "protagonist": {"name": "春人", "personality": ["普通"]},
        "heroine_a": {"name": "樱", "personality": ["温柔", "内向"]}
    }

    try:
        text = agent.generate_scene_text(
            scene=test_scene,
            characters_dict=test_characters,
            tone="温馨"
        )
        print("\n" + "="*50)
        print("Narrator Agent 测试成功!")
        print("="*50)
        print(text)
        print("="*50)
    except Exception as e:
        print(f"测试失败: {e}")
