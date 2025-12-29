"""
Story Intake Agent
故事理解/需求翻译 Agent
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from prompts.story_intake_prompt import (
    STORY_INTAKE_SYSTEM_PROMPT,
    STORY_INTAKE_HUMAN_PROMPT
)
from models.story import StoryConstraints
from utils.logger import log


class StoryIntakeAgent(BaseAgent):
    """故事理解Agent - 提取故事约束条件"""

    def __init__(self):
        """初始化Story Intake Agent"""
        super().__init__(
            name="StoryIntakeAgent",
            system_prompt=STORY_INTAKE_SYSTEM_PROMPT,
            human_prompt_template=STORY_INTAKE_HUMAN_PROMPT
        )

    def _get_required_fields(self) -> List[str]:
        """返回必填字段列表"""
        return ["genre", "themes", "tone", "must_have", "forbidden"]

    def process(self, user_idea: str) -> StoryConstraints:
        """
        处理用户的故事创意

        Args:
            user_idea: 用户输入的故事创意文本

        Returns:
            StoryConstraints: 故事约束条件
        """
        log.info(f"处理用户创意: {user_idea[:50]}...")

        # 运行Agent (带自动验证和修复)
        result = self.run(user_idea=user_idea)

        # 转换为StoryConstraints对象
        constraints = StoryConstraints(**result)

        log.info(f"提取约束成功:")
        log.info(f"  题材: {constraints.genre}")
        log.info(f"  主题: {', '.join(constraints.themes)}")
        log.info(f"  基调: {constraints.tone}")
        log.info(f"  必备元素: {', '.join(constraints.must_have)}")
        if constraints.forbidden:
            log.info(f"  禁止元素: {', '.join(constraints.forbidden)}")

        return constraints

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

        # 检查genre不为空
        if not output.get("genre"):
            return "genre不能为空"

        # 检查themes是列表且不为空
        themes = output.get("themes")
        if not isinstance(themes, list):
            return "themes必须是数组类型"
        if len(themes) == 0:
            return "themes不能为空，至少需要1个主题"

        # 检查must_have是列表
        if not isinstance(output.get("must_have"), list):
            return "must_have必须是数组类型"

        # 检查forbidden是列表
        if not isinstance(output.get("forbidden"), list):
            return "forbidden必须是数组类型"

        return True


if __name__ == "__main__":
    # 测试Story Intake Agent
    agent = StoryIntakeAgent()

    test_idea = """
    一个现代校园背景的故事。
    主角是一个普通高中生,突然班里来了一个转校生。
    这个转校生似乎隐瞒了什么秘密。
    随着故事发展,主角发现转校生实际上是在躲避什么。
    故事要有多条攻略线,每条线有不同的结局。
    """

    try:
        constraints = agent.process(test_idea)
        print("\n" + "="*50)
        print("Story Intake Agent 测试成功!")
        print("="*50)
        print(f"题材: {constraints.genre}")
        print(f"主题: {constraints.themes}")
        print(f"基调: {constraints.tone}")
        print(f"必备元素: {constraints.must_have}")
        print(f"禁止元素: {constraints.forbidden}")
        print("="*50)
    except Exception as e:
        print(f"测试失败: {e}")
