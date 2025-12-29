"""
测试 Story Outline Pipeline - 完整Pipeline测试
"""
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipelines.story_outline.story_outline_pipeline import StoryOutlinePipeline


def load_world_setting():
    """加载指定的世界观数据"""
    world_setting_path = "/Users/lyra/Desktop/GAL-Dreamer/output/20251230_032943/world_setting.json"

    if not Path(world_setting_path).exists():
        print(f"错误: {world_setting_path} 不存在")
        return None

    print(f"加载世界观数据: {world_setting_path}")
    with open(world_setting_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_full_pipeline():
    """测试完整的Story Outline Pipeline"""
    print("\n" + "=" * 60)
    print("GAL-Dreamer Story Outline Pipeline 完整测试")
    print("=" * 60)

    world_setting = load_world_setting()
    if not world_setting:
        return False

    user_idea = world_setting.get("input", {}).get("user_idea", "")
    print(f"\n原始创意: {user_idea[:80]}...")
    print("=" * 60)

    pipeline = StoryOutlinePipeline()
    try:
        result = pipeline.generate(
            world_setting_data=world_setting,
            output_dir=str(project_root / "output"),
            show_progress=True
        )

        print("\n" + "=" * 60)
        print("✅ StoryOutlinePipeline 测试成功!")
        print("=" * 60)

        final = result["final_output"]
        premise = final["story_premise"]
        chars = final["character_arcs"]
        conflict = final["conflict_engine"]

        print(f"\n📖 故事前提:")
        print(f"  核心钩子: {premise['hook']}")
        print(f"  核心问题: {premise['core_question']}")
        print(f"  主类型: {premise['primary_genre']}")
        print(f"  情感基调: {premise['emotional_tone']}")

        print(f"\n👥 角色弧光:")
        print(f"  主角: {chars['protagonist']['name']} ({chars['protagonist']['arc_type']}弧光)")
        print(f"  女主: {chars['heroines_count']}个")
        for h in chars['heroines']:
            print(f"    - {h['name']}: {h['arc_type']}弧光")

        print(f"\n⚔️ 矛盾引擎:")
        print(f"  主冲突: {conflict['main_conflicts_count']}个")
        for mc in conflict.get('main_conflicts', []):
            print(f"    - {mc['name']} ({mc['type']})")
        print(f"  次要冲突: {conflict['secondary_conflicts_count']}个")
        print(f"  危机节点: {conflict['escalation_nodes_count']}个")

        print("\n" + "=" * 60)
        print("✅ 全部测试通过!")
        print("=" * 60)

        return True
    except Exception as e:
        print(f"\n❌ StoryOutlinePipeline 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_full_pipeline()
    exit(0 if success else 1)
