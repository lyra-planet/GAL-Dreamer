"""
测试 HeroineRouteAgent 单独模块
"""
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.route_planning.heroine_route_agent import HeroineRouteAgent


def load_story_outline():
    """加载故事大纲数据"""
    story_outline_path = "/Users/lyra/Desktop/GAL-Dreamer/output/20251230_050843/story_outline.json"

    if not Path(story_outline_path).exists():
        print(f"错误: {story_outline_path} 不存在")
        return None

    print(f"加载故事大纲: {story_outline_path}")
    with open(story_outline_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_heroine_route_agent():
    """测试 HeroineRouteAgent"""
    print("\n" + "=" * 60)
    print("HeroineRouteAgent 单独测试")
    print("=" * 60)

    story_outline = load_story_outline()
    if not story_outline:
        return False

    # 模拟 route_framework（新架构）
    route_framework = {
        "heroine_id": "heroine_001",
        "heroine_name": "小飞翔",
        "route_type": "sweet",
        "theme": "找回自我，实现内在价值",
        "interlude_chapters": [
            {
                "chapter_id": "heroine_001_interlude_1",
                "chapter_name": "小飞翔的孤独时刻",
                "sequence_order": 4,
                "summary": "小飞翔独自一人时，流露出内心的脆弱与挣扎。",
                "emotional_goal": "展示小飞翔的脆弱面，建立情感连接"
            }
        ],
        "ending_chapter": {
            "chapter_id": "heroine_001_ending",
            "chapter_name": "小飞翔的救赎",
            "sequence_order": 99,
            "chapter_type": "ending",
            "associated_heroine": "heroine_001",
            "summary": "在小飞翔路线的最后，她终于找到了自我价值。",
            "emotional_goal": "完成小飞翔的弧光收束"
        }
    }

    # 模拟 heroine_arc
    heroine_arc = {
        "character_id": "heroine_001",
        "character_name": "小飞翔",
        "character_arc_type": "成长弧光",
        "initial_state": "迷茫、缺乏自信",
        "deep_need": "被认可、找到自我价值",
        "final_state": "自信、实现自我价值",
        "arc_lesson": "真正的价值来自于内心，而非他人的评价"
    }

    user_idea = story_outline.get("input", {}).get("user_idea", "")
    print(f"\n原始创意: {user_idea[:80]}...")
    print(f"测试女主: {route_framework['heroine_name']}")
    print("=" * 60)

    agent = HeroineRouteAgent()

    try:
        result = agent.process(
            story_outline_data=story_outline,
            route_framework=route_framework,
            heroine_arc=heroine_arc,
            user_idea=user_idea
        )

        print("\n" + "=" * 60)
        print("✅ HeroineRouteAgent 测试成功!")
        print("=" * 60)

        # 打印详细结果
        result_dict = result.model_dump()
        print(f"\n📁 {result_dict.get('heroine_name')} ({result_dict.get('route_type')})")
        print(f"📋 主题: {result_dict.get('route_theme')}")

        print(f"\n📁 插曲章节 ({len(result_dict.get('interlude_chapters', []))}个):")
        for ch in result_dict.get('interlude_chapters', []):
            print(f"  [{ch.get('sequence_order')}] {ch.get('chapter_name')}")
            print(f"    类型: {ch.get('chapter_type')}")
            print(f"    概要: {ch.get('summary')}")
            print(f"    开场: {ch.get('opening_scene', '')[:60]}...")
            print(f"    主要事件: {', '.join(ch.get('main_events', []))}")

        ending = result_dict.get('ending_chapter')
        if ending:
            print(f"\n📁 结局章节:")
            print(f"  {ending.get('chapter_name')}")
            print(f"    类型: {ending.get('chapter_type')}")
            print(f"    概要: {ending.get('summary')}")
            print(f"    开场: {ending.get('opening_scene', '')[:60]}...")

        conditions = result_dict.get('ending_conditions', {})
        print(f"\n📁 结局条件:")
        print(f"  需要好感度: {conditions.get('required_affection')}")
        print(f"  必需Flag: {conditions.get('required_flags', [])}")
        print(f"  互斥Flag: {conditions.get('forbidden_flags', [])}")

        print(f"\n📁 核心冲突:")
        print(f"  议题: {result_dict.get('personal_conflict')}")
        print(f"  解决: {result_dict.get('conflict_resolution')}")
        print(f"  主线交汇: {result_dict.get('main_story_intersection')}")

        print(f"\n📁 结局摘要: {result_dict.get('ending_summary')}")

        print("\n" + "=" * 60)
        print("✅ 测试完成!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ HeroineRouteAgent 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_heroine_route_agent()
    exit(0 if success else 1)
