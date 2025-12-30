"""
测试 RouteStructureAgent 单独模块（带时间槽位系统）
"""
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.route_planning.route_structure_agent import RouteStructureAgent


def load_story_outline():
    """加载故事大纲数据"""
    story_outline_path = "/Users/lyra/Desktop/GAL-Dreamer/output/20251230_050843/story_outline.json"

    if not Path(story_outline_path).exists():
        print(f"错误: {story_outline_path} 不存在")
        return None

    print(f"加载故事大纲: {story_outline_path}")
    with open(story_outline_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_route_structure_agent():
    """测试 RouteStructureAgent"""
    print("\n" + "=" * 60)
    print("RouteStructureAgent 单独测试（时间槽位系统）")
    print("=" * 60)

    story_outline = load_story_outline()
    if not story_outline:
        return False

    user_idea = story_outline.get("input", {}).get("user_idea", "")
    print(f"\n原始创意: {user_idea[:100]}...")
    print("=" * 60)

    agent = RouteStructureAgent()

    try:
        result = agent.process(
            story_outline_data=story_outline,
            user_idea=user_idea
        )

        print("\n" + "=" * 60)
        print("✅ RouteStructureAgent 测试成功!")
        print("=" * 60)

        # 打印详细结果
        result_dict = result.model_dump()
        print(f"\n📋 结构ID: {result_dict.get('structure_id')}")
        print(f"📋 总章节: {result_dict.get('total_estimated_chapters')}章")
        print(f"📋 共通线占比: {result_dict.get('common_ratio')*100:.0f}%")

        # ========== 时间槽位（新增） ==========
        print(f"\n⏰ 时间槽位:")
        for slot in result_dict.get('time_slots', []):
            print(f"  [{slot.get('slot_id')}] {slot.get('slot_name')} - {slot.get('time_period')}")
            print(f"    可用事件: {', '.join(slot.get('available_events', []))}")
            if slot.get('mutex_conditions'):
                print(f"    互斥条件: {', '.join(slot.get('mutex_conditions', []))}")

        # 共通线框架
        common_fw = result_dict.get('common_route_framework', {})
        print(f"\n📁 共通线框架:")
        print(f"  章节数: {common_fw.get('chapter_count')}章")
        print(f"  目的: {common_fw.get('purpose')}")

        print(f"\n  共通线章节大纲:")
        for ch in common_fw.get('chapter_outlines', []):
            slot_info = f" [槽位: {ch.get('time_slot_id')}]" if ch.get('time_slot_id') else ""
            print(f"    [{ch.get('sequence_order')}] {ch.get('chapter_name')}{slot_info}")
            print(f"      {ch.get('summary')}")

        print(f"\n  插曲章节:")
        for ch in common_fw.get('heroine_interlude_chapters', []):
            slot_info = f" [槽位: {ch.get('time_slot_id')}]" if ch.get('time_slot_id') else ""
            time_cost = f" [耗时: {ch.get('time_cost')}天]" if ch.get('time_cost') else ""
            print(f"    [{ch.get('sequence_order')}] {ch.get('chapter_name')} -> {ch.get('associated_heroine')}{slot_info}{time_cost}")
            print(f"      触发条件: {ch.get('trigger_conditions')}")
            if ch.get('mutex_with'):
                print(f"      互斥事件: {ch.get('mutex_with')}")

        print(f"\n  选择点:")
        for cp in common_fw.get('choice_points', []):
            print(f"    [{cp.get('point_id')}] {cp.get('point_name')}")
            print(f"      影响: {cp.get('affected_heroines')}")
            if cp.get('time_cost'):
                print(f"      时间消耗: {cp.get('time_cost')}")
            for choice in cp.get('choices', []):
                time_info = f" [{choice.get('time_cost')}天]" if choice.get('time_cost') else ""
                print(f"        - {choice.get('choice_text')}{time_info}")
                print(f"          好感度变化: {choice.get('affection_changes')}")
                if choice.get('flags_set'):
                    print(f"          设置Flag: {choice.get('flags_set')}")

        # 个人线框架
        print(f"\n📁 个人线框架:")
        for fw in result_dict.get('heroine_route_frameworks', []):
            print(f"  [{fw.get('heroine_id')}] {fw.get('heroine_name')} ({fw.get('route_type')})")
            print(f"    主题: {fw.get('theme')}")
            print(f"    插曲章节: {len(fw.get('interlude_chapters', []))}个")
            for ch in fw.get('interlude_chapters', []):
                slot_info = f" [槽位: {ch.get('time_slot_id')}]" if ch.get('time_slot_id') else ""
                time_cost = f" [耗时: {ch.get('time_cost')}天]" if ch.get('time_cost') else ""
                print(f"      - {ch.get('chapter_name')}{slot_info}{time_cost}")
                print(f"        触发: {ch.get('trigger_conditions')}")
                if ch.get('mutex_with'):
                    print(f"        互斥: {ch.get('mutex_with')}")
            ending = fw.get('ending_chapter')
            if ending:
                print(f"    结局章节: {ending.get('chapter_name')}")

        # 结局条件
        print(f"\n📁 结局条件:")
        for ec in result_dict.get('ending_conditions', []):
            print(f"  {ec.get('heroine_name')} ({ec.get('ending_type')}):")
            print(f"    需要好感度: {ec.get('required_affection')}")
            print(f"    必需Flag: {ec.get('required_flags', [])}")
            print(f"    互斥Flag: {ec.get('forbidden_flags', [])}")
            if ec.get('required_by_time'):
                print(f"    时间要求: {ec.get('required_by_time')}前达成")

        # Flag框架
        print(f"\n📁 Flag框架:")
        for flag in result_dict.get('flag_framework', []):
            print(f"  [{flag.get('flag_type')}] {flag.get('description')}")
            print(f"    影响: {', '.join(flag.get('affected_heroines', []))}")

        print("\n" + "=" * 60)
        print("✅ 测试完成!")
        print("=" * 60)

        # 保存结果
        output_dir = project_root / "output" / "route_structure_test"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "route_structure.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {output_file}")

        return True

    except Exception as e:
        print(f"\n❌ RouteStructureAgent 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_route_structure_agent()
    exit(0 if success else 1)
