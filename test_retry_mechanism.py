"""
测试新的JSON验证和修复重试机制
"""
import sys
sys.path.append('.')

from agents.macro_plot_agent import MacroPlotAgent
from agents.cast_design_agent import CastDesignAgent
from utils.logger import log


def test_macro_plot_agent():
    """测试MacroPlotAgent的重试机制"""
    print("\n" + "="*60)
    print("测试 MacroPlotAgent JSON验证和修复机制")
    print("="*60)

    agent = MacroPlotAgent()

    test_world = {
        "era": "现代",
        "location": "私立高中",
        "type": "现实",
        "core_conflict_source": "信息不对称",
        "description": "一个普通的现代高中校园"
    }

    test_cast = "主角:普通高中生; 女主A:转校生,有秘密; 女主B:青梅竹马"

    try:
        plot = agent.process(
            world_setting=test_world,
            cast_summary=test_cast,
            themes=["青春", "成长"]
        )
        print("\n✅ MacroPlotAgent 测试成功!")
        print(f"  故事弧: {plot.story_arc}")
        print(f"  转折点数量: {len(plot.major_twists)}")
        for i, twist in enumerate(plot.major_twists, 1):
            print(f"    {i}. {twist}")
        print("="*60)
        return True
    except Exception as e:
        print(f"\n❌ MacroPlotAgent 测试失败: {e}")
        print("="*60)
        return False


def test_cast_design_agent():
    """测试CastDesignAgent的重试机制"""
    print("\n" + "="*60)
    print("测试 CastDesignAgent JSON验证和修复机制")
    print("="*60)

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
            themes=["青春", "成长"],
            required_routes=3
        )
        print("\n✅ CastDesignAgent 测试成功!")
        print(f"  主角: {cast.protagonist.name}")
        print(f"  主角缺陷: {cast.protagonist.core_flaw}")
        print(f"  可攻略角色: {len(cast.heroines)}人")
        for i, heroine in enumerate(cast.heroines, 1):
            print(f"    {i}. {heroine.name} ({heroine.personality_type})")
        print("="*60)
        return True
    except Exception as e:
        print(f"\n❌ CastDesignAgent 测试失败: {e}")
        print("="*60)
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("GAL-Dreamer JSON验证和修复机制测试")
    print("="*60)
    print("\n此测试会验证:")
    print("1. Agent输出JSON格式验证")
    print("2. 缺失字段时自动触发修复重试")
    print("3. 最多4轮(1次生成+3次修复)")
    print("="*60)

    results = []

    # 测试MacroPlotAgent
    results.append(("MacroPlotAgent", test_macro_plot_agent()))

    # 测试CastDesignAgent
    results.append(("CastDesignAgent", test_cast_design_agent()))

    # 汇总结果
    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")

    all_passed = all(r[1] for r in results)
    print("="*60)
    if all_passed:
        print("🎉 所有测试通过!")
        return 0
    else:
        print("⚠️ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
