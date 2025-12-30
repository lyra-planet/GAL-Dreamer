"""
测试 Route Planning Pipeline - 完整Pipeline测试
"""
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipelines.route_planning.route_planning_pipeline import RoutePlanningPipeline


def load_story_outline():
    """加载指定的故事大纲数据"""
    story_outline_path = "/Users/lyra/Desktop/GAL-Dreamer/output/20251230_050843/story_outline.json"

    if not Path(story_outline_path).exists():
        print(f"错误: {story_outline_path} 不存在")
        return None

    print(f"加载故事大纲: {story_outline_path}")
    with open(story_outline_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_full_pipeline():
    """测试完整的Route Planning Pipeline"""
    print("\n" + "=" * 60)
    print("GAL-Dreamer Route Planning Pipeline 完整测试")
    print("=" * 60)

    story_outline = load_story_outline()
    if not story_outline:
        return False

    user_idea = story_outline.get("input", {}).get("user_idea", "")
    print(f"\n原始创意: {user_idea[:80]}...")
    print("=" * 60)

    pipeline = RoutePlanningPipeline()
    try:
        result = pipeline.generate(
            story_outline_data=story_outline,
            output_dir=str(project_root / "output"),
            show_progress=True
        )

        print("\n" + "=" * 60)
        print("✅ RoutePlanningPipeline 测试成功!")
        print("=" * 60)

        final = result["final_output"]
        structure = final["route_structure"]
        mood = final.get("mood_summary", {})

        print(f"\n📋 路线结构:")
        print(f"  总章节: {structure['total_chapters']}章")
        print(f"  共通线: {structure['common_chapters_count']}章")
        print(f"  个人路线: {structure['heroine_routes_count']}条")
        for route in final.get('heroine_routes_summary', []):
            print(f"    - {route['heroine_name']}: {route['chapters_count']}章 ({route['route_type']})")
            print(f"      主题: {route['route_theme']}, 结局: {route['endings_count']}个")
        if final.get('true_route_summary'):
            tr = final['true_route_summary']
            print(f"  真路线: {tr['chapters_count']}章")
            print(f"    解锁: {', '.join(tr['unlock_conditions'])}")

        if mood:
            print(f"\n🎭 情绪分布: {mood.get('mood_distribution', {})}")
            print(f"  共通线场景: {mood.get('common_scenes_count', 0)}个")

        # 显示详细的路由信息
        common_route = result["steps"]["common_route"]
        if hasattr(common_route, "model_dump"):
            common_dict = common_route.model_dump()
        else:
            common_dict = common_route

        print(f"\n📁 共通线章节详情:")
        for ch in common_dict.get("chapters", []):
            print(f"  - {ch.get('chapter_name')}: {ch.get('summary', '')[:60]}...")

        # 显示个人线详情
        print(f"\n📁 个人线详情:")
        for key, value in result["steps"].items():
            if key.startswith("heroine_route_"):
                if hasattr(value, "model_dump"):
                    route_dict = value.model_dump()
                else:
                    route_dict = value
                print(f"  {route_dict.get('heroine_name')}: {len(route_dict.get('chapters', []))}章")
                for ch in route_dict.get("chapters", []):
                    print(f"    - {ch.get('chapter_name')}: {ch.get('summary', '')[:60]}...")

        print("\n" + "=" * 60)
        print("✅ 全部测试通过!")
        print("=" * 60)

        return True
    except Exception as e:
        print(f"\n❌ RoutePlanningPipeline 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_full_pipeline()
    exit(0 if success else 1)
