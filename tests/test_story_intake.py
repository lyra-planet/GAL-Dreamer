"""
Story Intake Agent 测试脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.story_intake_agent import StoryIntakeAgent
from utils.logger import log


def test_story_intake():
    """测试Story Intake Agent"""

    print("\n" + "="*60)
    print("🧪 测试 Story Intake Agent")
    print("="*60 + "\n")

    # 创建Agent
    log.info("创建Story Intake Agent...")
    agent = StoryIntakeAgent()

    # 测试用例1: 校园恋爱故事
    test_cases = [
        {
            "name": "校园恋爱故事",
            "idea": """
            一个现代校园背景的故事。
            主角是一个普通高中生,突然班里来了一个转校生。
            这个转校生似乎隐瞒了什么秘密。
            随着故事发展,主角发现转校生实际上是在躲避什么。
            故事要有多条攻略线,每条线有不同的结局。
            """
        },
        {
            "name": "奇幻冒险故事",
            "idea": """
            一个剑与魔法的世界。
            主角是一个年轻的冒险者,在一次任务中意外获得了神秘力量。
            这份力量既可以拯救世界,也可能毁灭一切。
            主角需要组建队伍,揭开古老秘密。
            要有多种族角色,多个阵营可以选择。
            """
        }
    ]

    # 运行测试
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试用例 {i}: {test_case['name']}")
        print(f"{'='*60}\n")

        print(f"输入创意:")
        print(f"{test_case['idea']}\n")

        try:
            constraints = agent.process(test_case['idea'])

            print(f"\n✅ 测试通过!\n")
            print(f"提取结果:")
            print(f"  题材(genre): {constraints.genre}")
            print(f"  主题(themes): {', '.join(constraints.themes)}")
            print(f"  基调(tone): {constraints.tone}")
            print(f"  必备元素(must_have): {', '.join(constraints.must_have)}")
            if constraints.forbidden:
                print(f"  禁止元素(forbidden): {', '.join(constraints.forbidden)}")
            else:
                print(f"  禁止元素(forbidden): 无")

            results.append({
                "case": test_case['name'],
                "status": "✅ 通过",
                "genre": constraints.genre,
                "themes": constraints.themes
            })

        except Exception as e:
            print(f"\n❌ 测试失败: {e}\n")
            import traceback
            traceback.print_exc()  # 打印完整堆栈
            results.append({
                "case": test_case['name'],
                "status": f"❌ 失败: {e}",
            })

    # 打印总结
    print(f"\n{'='*60}")
    print("📊 测试总结")
    print(f"{'='*60}\n")

    passed = sum(1 for r in results if "✅" in r['status'])
    total = len(results)

    for result in results:
        print(f"{result['status']} - {result['case']}")

    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")

    print(f"{'='*60}\n")

    return passed == total


if __name__ == "__main__":
    success = test_story_intake()
    sys.exit(0 if success else 1)
