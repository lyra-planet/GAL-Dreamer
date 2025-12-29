"""
Cast Design Agent
角色群像设计 Agent
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from prompts.cast_design_prompt import (
    CAST_DESIGN_SYSTEM_PROMPT,
    CAST_DESIGN_HUMAN_PROMPT
)
from models.character import CharacterProfile
from utils.logger import log


class CastDesignAgent(BaseAgent):
    """角色群像设计Agent - 设计所有角色"""

    def __init__(self):
        """初始化Cast Design Agent"""
        super().__init__(
            name="CastDesignAgent",
            system_prompt=CAST_DESIGN_SYSTEM_PROMPT,
            human_prompt_template=CAST_DESIGN_HUMAN_PROMPT
        )

    def _get_required_fields(self) -> List[str]:
        """返回必填字段列表"""
        return ["protagonist", "heroines", "side_characters", "character_relationships"]

    def process(self, world_setting: Dict[str, Any], themes: list, required_routes: int = 3) -> CharacterProfile:
        """
        处理角色群像设计

        Args:
            world_setting: 世界观设定
            themes: 主题列表
            required_routes: 需要的可攻略线路数量

        Returns:
            CharacterProfile: 角色群像设定
        """
        log.info(f"设计角色群像，线路数量: {required_routes}")

        # 运行Agent (带自动验证和修复)
        result = self.run(
            world_setting=world_setting,
            themes=", ".join(themes),
            required_routes=str(required_routes)
        )

        # 转换为CharacterProfile对象
        cast_profile = CharacterProfile(**result)

        log.info(f"角色群像设计成功:")
        log.info(f"  主角: {cast_profile.protagonist.name}")
        log.info(f"  可攻略角色: {len(cast_profile.heroines)}人")
        log.info(f"  配角: {len(cast_profile.side_characters)}人")

        return cast_profile

    def validate_output(self, output: Dict[str, Any]):
        """
        验证输出是否有效（只验证不修复）

        Args:
            output: Agent输出

        Returns:
            True: 验证通过
            str: 验证失败的错误信息
        """
        # 先调用父类的基础验证
        base_result = super().validate_output(output)
        if base_result is not True:
            return base_result

        # 检查主角设定是字典
        protagonist = output.get("protagonist")
        if not isinstance(protagonist, dict):
            return "protagonist必须是字典类型"

        # 检查主角必填字段
        protagonist_required = ["character_id", "name", "personality", "background", "appearance", "motivation", "core_flaw"]
        for field in protagonist_required:
            if field not in protagonist:
                return f"protagonist缺少必填字段: {field}"
            # 检查字段是否为空值
            if protagonist[field] is None or protagonist[field] == "":
                return f"protagonist.{field}值为空，需要填充内容"

        # 检查可攻略角色是列表且至少2个
        heroines = output.get("heroines")
        if not isinstance(heroines, list):
            return "heroines必须是数组类型"
        if len(heroines) < 2:
            return f"heroines至少需要2个角色，当前只有{len(heroines)}个"

        # 检查每个heroine的必填字段
        for i, heroine in enumerate(heroines):
            if not isinstance(heroine, dict):
                return f"heroines[{i}]必须是字典类型"
            heroine_required = ["character_id", "name", "personality", "background", "appearance", "motivation",
                               "personality_type", "first_impression", "relationship_start", "voice_tone"]
            for field in heroine_required:
                if field not in heroine:
                    # 打印调试信息
                    log.debug(f"heroines[{i}]缺少字段 {field}, 当前有字段: {list(heroine.keys())}")
                    return f"heroines[{i}]缺少必填字段: {field}"
                # 检查字段是否为空值
                if heroine[field] is None or heroine[field] == "":
                    log.debug(f"heroines[{i}].{field}值为空")
                    return f"heroines[{i}].{field}值为空，需要填充内容"

        # 检查配角列表
        side_characters = output.get("side_characters")
        if not isinstance(side_characters, list):
            return "side_characters必须是数组类型"

        # 检查每个side_character的必填字段
        for i, char in enumerate(side_characters):
            if not isinstance(char, dict):
                return f"side_characters[{i}]必须是字典类型"
            side_required = ["character_id", "name", "personality", "background", "appearance", "motivation",
                            "importance", "story_function"]
            for field in side_required:
                if field not in char:
                    log.debug(f"side_characters[{i}]缺少字段 {field}, 当前有字段: {list(char.keys())}")
                    return f"side_characters[{i}]缺少必填字段: {field}"
                # 检查字段是否为空值
                if char[field] is None or char[field] == "":
                    log.debug(f"side_characters[{i}].{field}值为空")
                    return f"side_characters[{i}].{field}值为空，需要填充内容"

        return True


if __name__ == "__main__":
    # 测试Cast Design Agent
    agent = CastDesignAgent()

    test_world = {
        "era": "现代",
        "location": "私立高中",
        "type": "现实",
        "core_conflict_source": "信息不对称",
        "description": "一个普通的现代高中校园"
    }

    try:
        cast = agent.process(
            world_setting=test_world,
            themes=["青春", "成长", "选择"],
            required_routes=3
        )
        print("\n" + "="*50)
        print("Cast Design Agent 测试成功!")
        print("="*50)
        print(f"主角: {cast.protagonist.name}")
        print(f"可攻略角色: {[h.name for h in cast.heroines]}")
        print(f"配角: {[s.name for s in cast.side_characters]}")
        print("="*50)
    except Exception as e:
        print(f"测试失败: {e}")
