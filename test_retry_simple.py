"""
简单的重试机制测试 - 直接运行即可
"""
import sys
sys.path.append('.')

from agents.macro_plot_agent import MacroPlotAgent
from utils.logger import log


def main():
    print("\n" + "="*60)
    print("GAL-Dreamer JSON验证和修复机制测试")
    print("="*60)
    print("\n测试流程:")
    print("1. Agent生成JSON")
    print("2. 验证JSON格式")
    print("3. 如果验证失败，自动让LLM修复(最多4轮)")
    print("="*60)

    agent = MacroPlotAgent()

    print("\n【必填字段】")
    required_fields = agent._get_required_fields()
    print(f"  {', '.join(required_fields)}")

    test_world = {
        "era": "现代",
        "location": "私立高中",
        "type": "现实",
        "core_conflict_source": "信息不对称",
        "description": "一个普通的现代高中校园"
    }

    test_cast = "主角:普通高中生; 女主A:转校生,有秘密; 女主B:青梅竹马"

    print("\n【开始测试】")
    print("-"*60)

    try:
        plot = agent.process(
            world_setting=test_world,
            cast_summary=test_cast,
            themes=["青春", "成长"]
        )

        print("\n" + "="*60)
        print("✅ 测试成功!")
        print("="*60)
        print(f"故事弧: {plot.story_arc}")
        print(f"高潮点: {plot.climax_point}")
        print(f"转折点数量: {len(plot.major_twists)}")
        for i, twist in enumerate(plot.major_twists, 1):
            print(f"  {i}. {twist}")
        print("\n四幕结构:")
        for act_name, act_content in plot.acts.items():
            print(f"  {act_name}: {act_content[:50]}...")
        print("="*60)

    except Exception as e:
        print("\n" + "="*60)
        print("❌ 测试失败!")
        print("="*60)
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
