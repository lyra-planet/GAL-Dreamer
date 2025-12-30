"""
测试模块化主线规划流程
"""
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.route_planning.module_strategy_agent import ModuleStrategyAgent
from agents.route_planning.modular_main_route_agent import ModularMainRouteAgent


def create_test_story_outline():
    """创建测试用故事大纲"""
    return {
        "structure_id": "test_outline_001",
        "input": {
            "user_idea": """
            故事背景：现代都市校园
            主角：一名转校生，拥有能看到他人"情感颜色"的能力
            主要角色：
            -女主A：校园偶像，外表开朗但内心孤独，情感颜色是深蓝色
            -女主B：文学社社长，安静内向，喜欢推理小说，情感颜色是淡绿色
            -女主C：运动健将，直率热情，隐藏着家庭问题，情感颜色是橙红色
            核心冲突：主角发现三种特殊颜色会在特定情况下融合，引发神秘现象
            """
        },
        "steps": {
            "premise": {
                "premise_id": "test_premise",
                "genre": "现代校园恋爱",
                "theme": "理解与共鸣",
                "core_conflict": "情感颜色的秘密"
            },
            "cast_arc": {
                "heroines": [
                    {
                        "id": "heroine_001",
                        "name": "雪乃",
                        "archetype": "外表开朗内心孤独",
                        "emotional_color": "深蓝色"
                    },
                    {
                        "id": "heroine_002",
                        "name": "文香",
                        "archetype": "安静内向",
                        "emotional_color": "淡绿色"
                    },
                    {
                        "id": "heroine_003",
                        "name": "葵",
                        "archetype": "直率热情",
                        "emotional_color": "橙红色"
                    }
                ]
            },
            "conflict_engine": {
                "map": {
                    "conflict_map_id": "test_conflict_map"
                }
            }
        }
    }


def test_module_strategy():
    """测试四模块策略生成"""
    print("=" * 60)
    print("测试 1: 四模块策略生成")
    print("=" * 60)

    agent = ModuleStrategyAgent()
    story_outline = create_test_story_outline()

    try:
        strategy = agent.process(
            story_outline_data=story_outline,
            user_idea=story_outline["input"]["user_idea"],
            total_chapters=27
        )

        print("\n✅ 四模块策略生成成功!")
        print(f"  策略ID: {strategy.strategy_id}")
        print(f"  总章节数: {strategy.total_chapters}")
        print(f"  模块数: {len(strategy.modules)}")

        for module in strategy.modules:
            print(f"\n  [{module['module_name']}] {module.get('module_type', '')}")
            print(f"    章节范围: 第{module.get('chapter_range', {}).get('start', '?')}章到第{module.get('chapter_range', {}).get('end', '?')}章")

        return strategy

    except Exception as e:
        print(f"\n❌ 四模块策略生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_modular_main_route(strategy=None):
    """测试模块化主线生成"""
    print("\n" + "=" * 60)
    print("测试 2: 模块化主线框架生成")
    print("=" * 60)

    agent = ModularMainRouteAgent()
    story_outline = create_test_story_outline()

    if not strategy:
        print("  跳过：需要先成功生成四模块策略")
        return None

    try:
        # 测试生成第一个模块（起）
        print("\n--- 生成'起'模块 ---")
        module_strategy = {
            "module_name": "起",
            "module_type": "introduction",
            "chapter_range": {"start": 1, "end": 5},
            "main_plot": "世界观介绍、角色登场、核心悬念铺垫",
            "branch_design": "初期角色互动事件",
            "key_choices": "初次接触各角色的选择点",
            "affection_range": "0-20"
        }

        module_framework = agent.process_module(
            story_outline_data=story_outline,
            module_name="起",
            module_type="introduction",
            chapter_start=1,
            chapter_end=5,
            module_strategy=module_strategy,
            user_idea=story_outline["input"]["user_idea"]
        )

        print("\n✅ '起'模块生成成功!")
        print(f"  模块名称: {module_framework.module_name}")
        print(f"  章节范围: 第{module_framework.chapter_range['start']}-{module_framework.chapter_range['end']}章")
        print(f"  章节数: {len(module_framework.chapters)}")
        print(f"  分支数: {len(module_framework.branches)}")

        # 显示章节概要
        for ch in module_framework.chapters:
            print(f"    {ch.get('id', '')}: {ch.get('summary', '')}")

        # 测试生成第二个模块（承）
        print("\n--- 生成'承'模块 ---")
        module_strategy_2 = {
            "module_name": "承",
            "module_type": "development",
            "chapter_range": {"start": 6, "end": 15},
            "main_plot": "角色关系深入发展，角色弧光展开",
            "branch_design": "角色专属事件加深关系",
            "key_choices": "影响关系走向的关键选择",
            "affection_range": "20-50"
        }

        global_state = {
            "heroine_001": {"initial": 0, "min": 0, "max": 100, "description": "雪乃好感度"},
            "heroine_002": {"initial": 0, "min": 0, "max": 100, "description": "文香好感度"},
            "heroine_003": {"initial": 0, "min": 0, "max": 100, "description": "葵好感度"}
        }

        module_framework_2 = agent.process_module(
            story_outline_data=story_outline,
            module_name="承",
            module_type="development",
            chapter_start=6,
            chapter_end=15,
            module_strategy=module_strategy_2,
            global_state=global_state,
            global_branches=module_framework.branches,
            user_idea=story_outline["input"]["user_idea"]
        )

        print("\n✅ '承'模块生成成功!")
        print(f"  模块名称: {module_framework_2.module_name}")
        print(f"  章节范围: 第{module_framework_2.chapter_range['start']}-{module_framework_2.chapter_range['end']}章")
        print(f"  章节数: {len(module_framework_2.chapters)}")
        print(f"  分支数: {len(module_framework_2.branches)}")

        # 测试获取所有章节
        all_chapters = agent.get_all_chapters()
        print(f"\n📊 总共生成 {len(all_chapters)} 章")

        return agent

    except Exception as e:
        print(f"\n❌ 模块化主线生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("GAL-Dreamer 模块化主线规划测试")
    print("=" * 60)

    # 测试1: 四模块策略
    strategy = test_module_strategy()

    # 测试2: 模块化主线
    modular_agent = test_modular_main_route(strategy)

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

    if strategy and modular_agent:
        print("✅ 所有测试通过!")
        return 0
    else:
        print("⚠️ 部分测试未通过")
        return 1


if __name__ == "__main__":
    exit(main())
