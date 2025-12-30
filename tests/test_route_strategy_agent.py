"""
测试 RouteStrategyAgent - 路线战略规划
"""
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.route_planning.route_strategy_agent import RouteStrategyAgent


def load_story_outline():
    """加载故事大纲数据"""
    story_outline_path = "/Users/lyra/Desktop/GAL-Dreamer/output/20251230_050843/story_outline.json"

    if not Path(story_outline_path).exists():
        print(f"错误: {story_outline_path} 不存在")
        return None

    print(f"加载故事大纲: {story_outline_path}")
    with open(story_outline_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_route_strategy_agent():
    """测试 RouteStrategyAgent"""
    print("\n" + "=" * 60)
    print("RouteStrategyAgent 测试 - 路线战略规划")
    print("=" * 60)

    story_outline = load_story_outline()
    if not story_outline:
        return False

    user_idea = story_outline.get("input", {}).get("user_idea", "")
    print(f"\n原始创意: {user_idea[:100]}...")
    print("=" * 60)

    agent = RouteStrategyAgent()

    try:
        result = agent.process(
            story_outline_data=story_outline,
            user_idea=user_idea
        )

        print("\n" + "=" * 60)
        print("✅ RouteStrategyAgent 测试成功!")
        print("=" * 60)

        print(f"\n📋 战略ID: {result.strategy_id}")
        print(f"📋 来源大纲: {result.source_outline}")

        print(f"\n📝 路线战略意见:")
        print("=" * 60)
        print(result.strategy_text)
        print("=" * 60)

        # 保存结果
        output_dir = project_root / "output" / "route_strategy_test"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "route_strategy.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"战略ID: {result.strategy_id}\n")
            f.write(f"来源大纲: {result.source_outline}\n\n")
            f.write(result.strategy_text)
        print(f"\n结果已保存到: {output_file}")

        return True

    except Exception as e:
        print(f"\n❌ RouteStrategyAgent 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_route_strategy_agent()
    exit(0 if success else 1)
