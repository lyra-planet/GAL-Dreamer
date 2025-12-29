"""
测试所有 Agent (世界观生成)
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import log
from agents.story_intake_agent import StoryIntakeAgent
from agents.worldbuilding_agent import WorldbuildingAgent


def test_story_intake():
    """测试 1: Story Intake Agent"""
    print("\n" + "="*60)
    print("测试 1/2: Story Intake Agent")
    print("="*60)

    agent = StoryIntakeAgent()

    test_idea = """
    一个现代校园背景的恋爱故事。
    主角是一个普通高中生，突然班里来了一个神秘的转校生。
    这个转校生似乎隐瞒着什么秘密。
    """

    try:
        constraints = agent.process(test_idea)
        print(f"✅ 成功!")
        print(f"   题材: {constraints.genre}")
        print(f"   主题: {constraints.themes}")
        print(f"   基调: {constraints.tone}")
        return constraints
    except Exception as e:
        print(f"❌ 失败: {e}")
        return None


def test_worldbuilding(constraints):
    """测试 2: Worldbuilding Agent"""
    print("\n" + "="*60)
    print("测试 2/2: Worldbuilding Agent")
    print("="*60)

    if not constraints:
        print("⚠️ 跳过（前置测试失败）")
        return None

    agent = WorldbuildingAgent()

    try:
        world = agent.process(
            story_constraints=constraints.model_dump(),
            genre=constraints.genre,
            themes=constraints.themes
        )
        print(f"✅ 成功!")
        print(f"   时代: {world.era}")
        print(f"   地点: {world.location}")
        print(f"   类型: {world.type}")
        return world
    except Exception as e:
        print(f"❌ 失败: {e}")
        return None


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始测试 GAL-Dreamer 的 Agent (世界观生成)")
    print("="*60)

    # 按顺序测试所有 Agent
    constraints = test_story_intake()
    world = test_worldbuilding(constraints)

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    results = {
        "Story Intake Agent": constraints is not None,
        "Worldbuilding Agent": world is not None,
    }

    for name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")

    passed = sum(results.values())
    total = len(results)
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
