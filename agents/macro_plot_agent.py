"""
Macro Plot Agent
大剧情结构 Agent
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from prompts.macro_plot_prompt import (
    MACRO_PLOT_SYSTEM_PROMPT,
    MACRO_PLOT_HUMAN_PROMPT
)
from models.plot import MacroPlot
from utils.logger import log


class MacroPlotAgent(BaseAgent):
    """大剧情结构Agent - 构建完整故事骨架"""

    def __init__(self):
        """初始化Macro Plot Agent"""
        super().__init__(
            name="MacroPlotAgent",
            system_prompt=MACRO_PLOT_SYSTEM_PROMPT,
            human_prompt_template=MACRO_PLOT_HUMAN_PROMPT
        )

    def _get_required_fields(self) -> List[str]:
        """返回必填字段列表"""
        return ["acts", "major_twists", "story_arc", "climax_point"]

    def process(self, world_setting: Dict[str, Any], cast_summary: str, themes: list) -> MacroPlot:
        """
        处理大剧情结构设计

        Args:
            world_setting: 世界观设定
            cast_summary: 角色设定摘要
            themes: 主题列表

        Returns:
            MacroPlot: 大剧情结构
        """
        log.info("构建大剧情结构")

        # 运行Agent (带自动验证和修复)
        result = self.run(
            world_setting=world_setting,
            cast_summary=cast_summary,
            themes=", ".join(themes)
        )

        # 转换为MacroPlot对象
        macro_plot = MacroPlot(**result)

        log.info(f"大剧情结构构建成功:")
        log.info(f"  故事弧: {macro_plot.story_arc}")
        log.info(f"  转折点数量: {len(macro_plot.major_twists)}")

        return macro_plot

    def validate_output(self, output: Dict[str, Any]):
        """
        验证输出格式（不修复）

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

        # 检查acts是字典且包含四个幕
        acts = output.get("acts")
        if not isinstance(acts, dict):
            return "acts必须是字典类型"
        required_acts = ["act1", "act2", "act3", "act4"]
        missing_acts = [act for act in required_acts if act not in acts]
        if missing_acts:
            return f"acts缺少必填的幕: {', '.join(missing_acts)}"

        # 检查major_twists是列表且至少3个
        twists = output.get("major_twists")
        if not isinstance(twists, list):
            return "major_twists必须是数组类型"
        if len(twists) < 3:
            return f"major_twists至少需要3个转折点，当前只有{len(twists)}个"

        # 检查story_arc和climax_point不为空
        if not output.get("story_arc"):
            return "story_arc不能为空"
        if not output.get("climax_point"):
            return "climax_point不能为空"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """
        当Agent失败时返回安全默认值
        """
        return {
            "acts": {
                "act1": "故事开端，介绍主角和世界设定",
                "act2": "冲突逐渐显现，角色关系发展",
                "act3": "真相揭露，冲突达到高潮",
                "act4": "解决冲突，角色成长，故事收尾"
            },
            "major_twists": [
                "主角发现隐藏的真相",
                "关键角色身份揭晓",
                "最终选择带来转机"
            ],
            "story_arc": "一个关于成长与选择的故事",
            "climax_point": "主角面临重大抉择的时刻"
        }


if __name__ == "__main__":
    # 测试Macro Plot Agent
    agent = MacroPlotAgent()

    test_world = {
        "era": "现代",
        "location": "私立高中",
        "type": "现实",
        "description": "一个普通的高中校园"
    }

    test_cast = "主角:普通高中生; 女主A:转校生,有秘密; 女主B:青梅竹马"

    try:
        plot = agent.process(
            world_setting=test_world,
            cast_summary=test_cast,
            themes=["青春", "成长"]
        )
        print("\n" + "="*50)
        print("Macro Plot Agent 测试成功!")
        print("="*50)
        print(f"故事弧: {plot.story_arc}")
        print(f"第一幕: {plot.acts['act1']}")
        print(f"高潮: {plot.climax_point}")
        print("="*50)
    except Exception as e:
        print(f"测试失败: {e}")
