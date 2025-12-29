"""
测试所有 8 个 Agent
逐个测试每个 Agent 的基本功能
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import log
from agents.story_intake_agent import StoryIntakeAgent
from agents.worldbuilding_agent import WorldbuildingAgent
from agents.cast_design_agent import CastDesignAgent
from agents.macro_plot_agent import MacroPlotAgent
from agents.route_design_agent import RouteDesignAgent
from agents.conflict_emotion_agent import ConflictEmotionAgent
from agents.consistency_agent import ConsistencyAgent
from agents.narrator_agent import NarratorAgent


def test_story_intake():
    """测试 1: Story Intake Agent"""
    print("\n" + "="*60)
    print("测试 1/8: Story Intake Agent")
    print("="*60)

    agent = StoryIntakeAgent()

    test_idea = """
    一个现代校园背景的恋爱故事。
    主角是一个普通高中生，突然班里来了一个神秘的转校生。
    这个转校生似乎隐瞒着什么秘密。
    随着故事发展，主角发现转校生实际上是在躲避什么。
    故事要有多条攻略线，每条线有不同的结局。
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
    print("测试 2/8: Worldbuilding Agent")
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


def test_cast_design(world, constraints):
    """测试 3: Cast Design Agent"""
    print("\n" + "="*60)
    print("测试 3/8: Cast Design Agent")
    print("="*60)

    if not world:
        print("⚠️ 跳过（前置测试失败）")
        return None

    agent = CastDesignAgent()

    try:
        cast = agent.process(
            world_setting=world.model_dump(),
            themes=constraints.themes,
            required_routes=3
        )
        print(f"✅ 成功!")
        print(f"   主角: {cast.protagonist.name}")
        print(f"   可攻略角色: {len(cast.heroines)}人")
        for h in cast.heroines:
            print(f"     - {h.name} ({h.personality_type})")
        return cast
    except Exception as e:
        print(f"❌ 失败: {e}")
        return None


def test_macro_plot(world, cast, constraints):
    """测试 4: Macro Plot Agent"""
    print("\n" + "="*60)
    print("测试 4/8: Macro Plot Agent")
    print("="*60)

    if not cast:
        print("⚠️ 跳过（前置测试失败）")
        return None

    agent = MacroPlotAgent()

    # 构建角色摘要
    cast_summary = f"主角: {cast.protagonist.name}\n"
    cast_summary += f"可攻略角色: {', '.join([h.name for h in cast.heroines])}"

    try:
        plot = agent.process(
            world_setting=world.model_dump(),
            cast_summary=cast_summary,
            themes=constraints.themes
        )
        print(f"✅ 成功!")
        print(f"   故事弧: {plot.story_arc}")
        print(f"   转折点数量: {len(plot.major_twists)}")
        return plot
    except Exception as e:
        print(f"❌ 失败: {e}")
        return None


def test_route_design(plot, cast):
    """测试 5: Route Design Agent"""
    print("\n" + "="*60)
    print("测试 5/8: Route Design Agent")
    print("="*60)

    if not plot:
        print("⚠️ 跳过（前置测试失败）")
        return None

    agent = RouteDesignAgent()

    try:
        routes = agent.process(
            macro_plot=plot.model_dump(),
            heroine_list=[h.model_dump() for h in cast.heroines]
        )
        print(f"✅ 成功!")
        print(f"   线路数量: {len(routes.routes)}")
        for route in routes.routes:
            print(f"     - {route.route_name}: {route.conflict_focus}")
        return routes
    except Exception as e:
        print(f"❌ 失败: {e}")
        return None


def test_conflict_emotion(routes, cast):
    """测试 6: Conflict & Emotion Agent"""
    print("\n" + "="*60)
    print("测试 6/8: Conflict & Emotion Agent")
    print("="*60)

    if not routes:
        print("⚠️ 跳过（前置测试失败）")
        return None

    agent = ConflictEmotionAgent()

    try:
        design = agent.process(
            route_plots=routes.model_dump(),
            character_states=cast.model_dump()
        )
        print(f"✅ 成功!")
        print(f"   冲突节点数量: {len(design.conflicts)}")
        for c in design.conflicts[:3]:
            print(f"     - {c.conflict_type}: {c.description[:40]}...")
        return design
    except Exception as e:
        print(f"❌ 失败: {e}")
        return None


def test_consistency(constraints, world, cast):
    """测试 7: Consistency Agent"""
    print("\n" + "="*60)
    print("测试 7/8: Consistency Agent")
    print("="*60)

    if not cast:
        print("⚠️ 跳过（前置测试失败）")
        return None

    agent = ConsistencyAgent()

    # 构建完整故事结构
    full_story = {
        "constraints": constraints.model_dump(),
        "world": world.model_dump(),
        "cast": {
            "protagonist": cast.protagonist.model_dump(),
            "heroines": [h.model_dump() for h in cast.heroines]
        }
    }

    try:
        report = agent.process(
            full_story_structure=full_story,
            world_rules=world.rules,
            character_profiles=cast.model_dump()
        )
        print(f"✅ 成功!")
        print(f"   通过审查: {'是' if report.valid else '否'}")
        print(f"   问题数量: {len(report.issues)}")
        return report
    except Exception as e:
        print(f"❌ 失败: {e}")
        return None


def test_narrator(cast):
    """测试 8: Narrator Agent"""
    print("\n" + "="*60)
    print("测试 8/8: Narrator Agent")
    print("="*60)

    if not cast:
        print("⚠️ 跳过（前置测试失败）")
        return None

    agent = NarratorAgent()

    # 创建测试场景
    scene = {
        "location": "教室",
        "time": "放学后",
        "scene_type": "对话场景",
        "characters_present": ["protagonist", "heroine_1"]
    }

    characters_dict = {
        "protagonist": {"name": cast.protagonist.name, "personality": cast.protagonist.personality},
        "heroine_1": {"name": cast.heroines[0].name, "personality": cast.heroines[0].personality}
    }

    try:
        text = agent.generate_scene_text(
            scene=scene,
            characters_dict=characters_dict,
            tone="温馨"
        )
        print(f"✅ 成功!")
        print(f"   生成文本长度: {len(text)}字符")
        print(f"   文本预览: {text[:100]}...")
        return text
    except Exception as e:
        print(f"❌ 失败: {e}")
        return None


def main():
    """运行所有测试"""
    # 日志已在导入时自动设置

    print("\n" + "="*60)
    print("开始测试 GAL-Dreamer 的 8 个 Agent")
    print("="*60)

    # 按顺序测试所有 Agent
    constraints = test_story_intake()
    world = test_worldbuilding(constraints)
    cast = test_cast_design(world, constraints)
    plot = test_macro_plot(world, cast, constraints)
    routes = test_route_design(plot, cast)
    conflict = test_conflict_emotion(routes, cast)
    report = test_consistency(constraints, world, cast)
    text = test_narrator(cast)

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    results = {
        "Story Intake Agent": constraints is not None,
        "Worldbuilding Agent": world is not None,
        "Cast Design Agent": cast is not None,
        "Macro Plot Agent": plot is not None,
        "Route Design Agent": routes is not None,
        "Conflict & Emotion Agent": conflict is not None,
        "Consistency Agent": report is not None,
        "Narrator Agent": text is not None,
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
