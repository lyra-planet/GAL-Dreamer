"""
测试 MainRouteAgent - 只生成共通线（主线）框架
"""
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.route_planning.main_route_agent import MainRouteAgent


def load_story_outline():
    """加载故事大纲数据"""
    story_outline_path = "/Users/lyra/Desktop/GAL-Dreamer/output/20251230_050843/story_outline.json"

    if not Path(story_outline_path).exists():
        print(f"错误: {story_outline_path} 不存在")
        return None

    print(f"加载故事大纲: {story_outline_path}")
    with open(story_outline_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_main_route_agent():
    """测试 MainRouteAgent"""
    print("\n" + "=" * 60)
    print("MainRouteAgent 测试 - 只生成共通线（主线）框架")
    print("=" * 60)

    story_outline = load_story_outline()
    if not story_outline:
        return False

    user_idea = story_outline.get("input", {}).get("user_idea", "")
    print(f"\n原始创意: {user_idea[:100]}...")
    print("=" * 60)

    agent = MainRouteAgent()

    try:
        result = agent.process(
            story_outline_data=story_outline,
            user_idea=user_idea
        )

        print("\n" + "=" * 60)
        print("✅ MainRouteAgent 测试成功!")
        print("=" * 60)

        # 打印详细结果
        result_dict = result.model_dump()
        print(f"\n📋 结构ID: {result_dict.get('structure_id')}")
        print(f"📋 来源大纲: {result_dict.get('source_outline')}")
        print(f"📋 预计总章节: {result_dict.get('total_estimated_chapters')}章")
        print(f"📋 共通线占比: {result_dict.get('common_ratio')*100:.0f}%")

        # 共通线框架
        common_fw = result_dict.get('common_route_framework', {})
        print(f"\n📁 共通线（主线）框架:")
        print(f"  章节数: {common_fw.get('chapter_count')}章")
        print(f"  目的: {common_fw.get('purpose')}")

        print(f"\n  共通线章节大纲:")
        for ch in common_fw.get('chapter_outlines', []):
            print(f"    [{ch.get('sequence_order')}] {ch.get('chapter_name')} ({ch.get('chapter_type')})")
            print(f"      概要: {ch.get('summary')}")
            print(f"      情感目标: {ch.get('emotional_goal')}")

        # 验证数据完整性
        print(f"\n📊 数据验证:")

        issues = []
        if not result_dict.get('structure_id'):
            issues.append("❌ structure_id 为空")
        if result_dict.get('total_estimated_chapters', 0) < 10:
            issues.append("⚠️ total_estimated_chapters 可能太少")
        if not (0.6 <= result_dict.get('common_ratio', 0) <= 0.9):
            issues.append("❌ common_ratio 不在合理范围 (0.6-0.9)")
        if not common_fw.get('chapter_count'):
            issues.append("❌ chapter_count 为空")
        if not common_fw.get('purpose'):
            issues.append("❌ purpose 为空")
        if not common_fw.get('chapter_outlines'):
            issues.append("❌ chapter_outlines 为空")

        chapter_count = common_fw.get('chapter_count', 0)
        outline_count = len(common_fw.get('chapter_outlines', []))
        if chapter_count != outline_count:
            issues.append(f"❌ chapter_count({chapter_count}) 与 chapter_outlines数量({outline_count})不一致")

        for i, ch in enumerate(common_fw.get('chapter_outlines', [])):
            if ch.get('chapter_type') != 'common':
                issues.append(f"❌ 第{i+1}章 chapter_type 不是 'common': {ch.get('chapter_type')}")
            if ch.get('associated_heroine') is not None:
                issues.append(f"❌ 第{i+1}章 associated_heroine 应该为null: {ch.get('associated_heroine')}")

        if issues:
            for issue in issues:
                print(f"  {issue}")
        else:
            print("  ✅ 所有数据验证通过!")

        print("\n" + "=" * 60)
        print("✅ 测试完成!")
        print("=" * 60)

        # 保存结果
        output_dir = project_root / "output" / "main_route_test"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "main_route_framework.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {output_file}")

        return len(issues) == 0

    except Exception as e:
        print(f"\n❌ MainRouteAgent 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_main_route_agent()
    exit(0 if success else 1)
