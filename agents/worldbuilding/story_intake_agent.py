"""
Story Intake Agent
故事理解/需求翻译 Agent - 提取用户故事创意中的约束条件
"""
from typing import Dict, Any, List, Optional, Union

from agents.base_agent import BaseAgent
from prompts.worldbuilding.story_intake_prompt import (
    STORY_INTAKE_SYSTEM_PROMPT,
    STORY_INTAKE_HUMAN_PROMPT
)
from models.story import StoryConstraints
from utils.logger import log


class StoryIntakeAgent(BaseAgent):
    """
    故事理解Agent

    功能:
    - 解析用户输入的故事创意
    - 提取故事约束条件(题材、主题、基调、必备元素、禁止元素)
    """

    # 类属性配置
    name = "StoryIntakeAgent"
    system_prompt = STORY_INTAKE_SYSTEM_PROMPT
    human_prompt_template = STORY_INTAKE_HUMAN_PROMPT
    required_fields = ["genre", "themes", "tone", "must_have", "forbidden"]

    def process(self, user_idea: str, validate: bool = True) -> StoryConstraints:
        """
        处理用户的故事创意

        Args:
            user_idea: 用户输入的故事创意文本
            validate: 是否验证输出(默认True)

        Returns:
            StoryConstraints: 故事约束条件

        Raises:
            ValueError: 输入为空时
            RuntimeError: 处理失败时
        """
        if not user_idea or not user_idea.strip():
            raise ValueError("用户创意不能为空")

        user_idea = user_idea.strip()
        log.info(f"处理用户创意: {self._truncate(user_idea, 50)}...")

        try:
            result = self.run(user_idea=user_idea)
            constraints = StoryConstraints(**result)

            self._log_success(constraints)
            return constraints

        except Exception as e:
            log.error(f"StoryIntakeAgent 处理失败: {e}")
            raise RuntimeError(f"故事理解失败: {e}") from e

    def _truncate(self, text: str, max_length: int) -> str:
        """截断文本"""
        return text[:max_length] if len(text) > max_length else text

    def _log_success(self, constraints: StoryConstraints) -> None:
        """记录成功日志"""
        log.info("提取约束成功:")
        log.info(f"  题材: {constraints.genre}")
        log.info(f"  主题: {', '.join(constraints.themes)}")
        log.info(f"  基调: {constraints.tone}")
        log.info(f"  必备元素: {', '.join(constraints.must_have) or '无'}")
        if constraints.forbidden:
            log.info(f"  禁止元素: {', '.join(constraints.forbidden)}")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """
        验证输出是否有效

        Args:
            output: Agent输出

        Returns:
            True: 验证通过
            str: 验证失败的错误信息
        """
        # 检查genre
        genre = output.get("genre")
        if not genre or not isinstance(genre, str) or not genre.strip():
            return "genre必须是非空字符串"

        # 检查themes
        themes = output.get("themes")
        if not isinstance(themes, list):
            return "themes必须是数组类型"
        if len(themes) == 0:
            return "themes不能为空，至少需要1个主题"
        if not all(isinstance(t, str) for t in themes):
            return "themes中的所有元素必须是字符串"

        # 检查tone
        tone = output.get("tone")
        if not tone or not isinstance(tone, str) or not tone.strip():
            return "tone必须是非空字符串"

        # 检查must_have
        must_have = output.get("must_have")
        if not isinstance(must_have, list):
            return "must_have必须是数组类型"
        if not all(isinstance(m, str) for m in must_have):
            return "must_have中的所有元素必须是字符串"

        # 检查forbidden
        forbidden = output.get("forbidden")
        if forbidden is not None and not isinstance(forbidden, list):
            return "forbidden必须是数组类型"
        if forbidden and not all(isinstance(f, str) for f in forbidden):
            return "forbidden中的所有元素必须是字符串"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        return {
            "genre": "恋爱",
            "themes": ["青春", "成长"],
            "tone": "温馨",
            "must_have": [],
            "forbidden": [],
            "fallback": True
        }


if __name__ == "__main__":
    # 测试Story Intake Agent
    agent = StoryIntakeAgent()

    test_idea = """
    一个现代校园背景的故事。
    主角是一个普通高中生，突然班里来了一个转校生。
    这个转校生似乎隐瞒了什么秘密。
    随着故事发展，主角发现转校生实际上是在躲避什么。
    故事要有多条攻略线，每条线有不同的结局。
    """

    try:
        constraints = agent.process(test_idea)
        print("\n" + "=" * 50)
        print("Story Intake Agent 测试成功!")
        print("=" * 50)
        print(f"题材: {constraints.genre}")
        print(f"主题: {constraints.themes}")
        print(f"基调: {constraints.tone}")
        print(f"必备元素: {constraints.must_have}")
        print(f"禁止元素: {constraints.forbidden}")
        print("=" * 50)
    except Exception as e:
        print(f"测试失败: {e}")
