"""
Worldbuilding Agent
世界观构建 Agent
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from prompts.worldbuilding_prompt import (
    WORLDBUILDING_SYSTEM_PROMPT,
    WORLDBUILDING_HUMAN_PROMPT
)
from models.world import WorldSetting
from utils.logger import log


class WorldbuildingAgent(BaseAgent):
    """世界观构建Agent - 构建世界背景和规则"""

    def __init__(self):
        """初始化Worldbuilding Agent"""
        super().__init__(
            name="WorldbuildingAgent",
            system_prompt=WORLDBUILDING_SYSTEM_PROMPT,
            human_prompt_template=WORLDBUILDING_HUMAN_PROMPT
        )

    def _get_required_fields(self) -> List[str]:
        """返回必填字段列表"""
        return ["era", "location", "type", "rules", "core_conflict_source", "description"]

    def process(self, story_constraints: Dict[str, Any], genre: str, themes: list) -> WorldSetting:
        """
        处理世界观构建

        Args:
            story_constraints: 故事约束条件
            genre: 题材
            themes: 主题列表

        Returns:
            WorldSetting: 世界观设定
        """
        log.info(f"构建世界观，题材: {genre}")

        # 运行Agent (带自动验证和修复)
        result = self.run(
            story_constraints=story_constraints,
            genre=genre,
            themes=", ".join(themes)
        )

        # 转换为WorldSetting对象
        world_setting = WorldSetting(**result)

        log.info(f"世界观构建成功:")
        log.info(f"  时代: {world_setting.era}")
        log.info(f"  地点: {world_setting.location}")
        log.info(f"  类型: {world_setting.type}")
        log.info(f"  核心冲突来源: {world_setting.core_conflict_source}")

        return world_setting

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

        # 检查规则是列表且不为空
        rules = output.get("rules")
        if not isinstance(rules, list):
            return "rules必须是数组类型"
        if len(rules) == 0:
            return "rules不能为空，至少需要1条规则"

        return True


if __name__ == "__main__":
    # 测试Worldbuilding Agent
    agent = WorldbuildingAgent()

    test_constraints = {
        "genre": "恋爱",
        "themes": ["青春", "成长"],
        "tone": "温馨",
        "must_have": ["多女主", "多结局"],
        "forbidden": ["超自然"]
    }

    try:
        world = agent.process(
            story_constraints=test_constraints,
            genre="恋爱",
            themes=["青春", "成长"]
        )
        print("\n" + "="*50)
        print("Worldbuilding Agent 测试成功!")
        print("="*50)
        print(f"时代: {world.era}")
        print(f"地点: {world.location}")
        print(f"类型: {world.type}")
        print(f"描述: {world.description}")
        print("="*50)
    except Exception as e:
        print(f"测试失败: {e}")
