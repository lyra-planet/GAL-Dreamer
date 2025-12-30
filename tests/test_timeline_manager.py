"""
时间线管理器测试
测试从worldbuilding.json和story_outline.json加载时间线、添加事件、更新状态等功能
"""
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime.timeline_manager import TimelineManager
from models.runtime.timeline import (
    TimelineEventType,
    EventImportance
)


def test_load_from_worldbuilding():
    """测试从worldbuilding.json加载时间线"""
    print("\n" + "=" * 60)
    print("测试1: 从 worldbuilding.json 加载时间线")
    print("=" * 60)

    manager = TimelineManager(save_dir="test_data/timeline")

    # 假设world_setting.json在同一目录
    worldbuilding_path = "output/20251230_050843/world_setting.json"

    try:
        # 尝试加载
        with open(worldbuilding_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        timeline_data = data.get("steps", {}).get("timeline", {})
        timeline = manager.load_from_worldbuilding(worldbuilding_path)

        print(f"\n时间线ID: {timeline.timeline_id}")
        print(f"当前年份: {timeline.current_year}")
        print(f"时代概述: {timeline.era_summary}")
        print(f"历史事件: {len(timeline.historical_events)} 个")

        for event in timeline.historical_events:
            print(f"  - {event.event_name} ({event.in_story_time})")
            print(f"    {event.description[:80]}...")

        return manager, timeline

    except FileNotFoundError:
        print(f"  world_setting.json 不存在，跳过此测试")
        # 创建一个空的时间线
        timeline = manager.load_or_create()
        print(f"\n创建新时间线: {timeline.timeline_id}")
        return manager, timeline


def test_load_from_outline(manager: TimelineManager):
    """测试从story_outline.json加载大纲节点"""
    print("\n" + "=" * 60)
    print("测试2: 从 story_outline.json 加载大纲节点")
    print("=" * 60)

    outline_path = "output/20251230_050843/story_outline.json"

    try:
        nodes = manager.load_from_outline(outline_path)

        print(f"\n加载了 {len(nodes)} 个大纲节点:")

        for i, node in enumerate(nodes[:10]):
            print(f"\n  {i+1}. {node.node_name}")
            print(f"     类型: {node.node_type}")
            print(f"     情感强度: {node.emotional_intensity}/10")
            print(f"     进度: {node.progress_value:.1%}")
            print(f"     描述: {node.description[:80]}...")

    except FileNotFoundError:
        print("  story_outline.json 不存在，跳过此测试")


def test_add_events(manager: TimelineManager):
    """测试添加事件"""
    print("\n" + "=" * 60)
    print("测试3: 添加事件")
    print("=" * 60)

    timeline = manager.get_timeline()

    # 添加相遇事件
    meeting_event = manager.add_meeting_event(
        character_id="heroine_001",
        character_name="小飞翔",
        location="精灵林",
        description="在精灵林的阳光下，遇到了一个活泼的身影"
    )
    print(f"\n添加相遇事件: {meeting_event.event_name}")

    # 添加选择事件
    choice_event = manager.add_event_from_choice(
        choice_id="choice_001",
        choice_description="帮助受伤的精灵",
        chosen_option="伸出援手",
        affected_characters=["heroine_001"],
        consequences=["与小飞翔建立了初步的联系", "获得了精灵守望者的关注"]
    )
    print(f"添加选择事件: {choice_event.event_name}")

    # 添加关系变化事件
    relation_event = manager.add_relationship_event(
        character_id="heroine_001",
        character_name="小飞翔",
        change_type="increase",
        change_value=10,
        description="帮助让小飞翔对主角产生了好感"
    )
    print(f"添加关系事件: {relation_event.event_name}")

    # 添加关键剧情事件
    story_event = manager.add_event(
        name="精灵之戒觉醒",
        description="在紧急情况下，主角的精灵之戒突然觉醒，释放出强大的力量",
        event_type=TimelineEventType.MILESTONE,
        importance=EventImportance.CRITICAL,
        characters=["protagonist_main", "heroine_001"],
        location="精灵林",
        consequences=["主角的多精灵联系被证实", "精灵守望者决定介入调查"],
        flags=["spirit_戒指_觉醒", "守望者_关注"]
    )
    print(f"添加关键事件: {story_event.event_name}")

    # 显示摘要
    summary = manager.get_timeline_summary()
    print(f"\n时间线摘要:")
    print(f"  总事件数: {summary['total_events']}")
    print(f"  已发生: {summary['passed_events']}")
    print(f"  即将来临: {summary['upcoming_events']}")

    return [meeting_event, choice_event, relation_event, story_event]


def test_event_management(manager: TimelineManager, events):
    """测试事件管理"""
    print("\n" + "=" * 60)
    print("测试4: 事件管理")
    print("=" * 60)

    # 标记事件已发生
    for event in events[:2]:
        manager.mark_event_passed(event.event_id)
        print(f"标记事件已发生: {event.event_name}")

    # 获取已发生的事件
    passed = manager.get_passed_events()
    print(f"\n已发生的事件: {len(passed)} 个")
    for event in passed:
        print(f"  - {event.event_name}")

    # 获取关键事件
    critical = manager.get_critical_events()
    print(f"\n关键事件: {len(critical)} 个")
    for event in critical:
        print(f"  - [{event.importance.value}] {event.event_name}")

    # 获取涉及特定角色的事件
    char_events = manager.get_events_by_character("heroine_001")
    print(f"\n涉及小飞翔的事件: {len(char_events)} 个")
    for event in char_events:
        print(f"  - {event.event_name}")


def test_node_management(manager: TimelineManager):
    """测试节点管理"""
    print("\n" + "=" * 60)
    print("测试5: 节点管理")
    print("=" * 60)

    # 获取当前节点
    current = manager.get_current_node()
    if current:
        print(f"\n当前节点: {current.node_name}")
        print(f"  类型: {current.node_type}")
        print(f"  进度: {current.progress_value:.1%}")

    # 获取下一个节点
    next_node = manager.get_next_node()
    if next_node:
        print(f"\n下一个节点: {next_node.node_name}")

    # 推进到下一个节点
    if next_node:
        manager.advance_to_next_node()
        print(f"\n已推进到: {next_node.node_name}")

        # 再次获取当前节点
        current = manager.get_current_node()
        print(f"当前剧情进度: {manager.get_story_progress():.1%}")


def test_time_progression(manager: TimelineManager):
    """测试时间推进"""
    print("\n" + "=" * 60)
    print("测试6: 时间推进")
    print("=" * 60)

    # 显示当前时间
    current_time = manager.get_current_time()
    print(f"\n当前时间: {current_time['description']}")

    # 推进时间
    manager.advance_time(days=1, scenes=2, time_of_day="傍晚")
    current_time = manager.get_current_time()
    print(f"推进后: {current_time['description']}")

    # 推进章节
    new_chapter = manager.advance_chapter()
    current_time = manager.get_current_time()
    print(f"\n推进到第 {new_chapter} 章")
    print(f"当前时间: {current_time['description']}")


def test_conflict_progress(manager: TimelineManager):
    """测试冲突进度"""
    print("\n" + "=" * 60)
    print("测试7: 冲突进度管理")
    print("=" * 60)

    # 更新冲突进度
    manager.update_conflict_progress("conflict_main_1", 0.3)
    manager.update_conflict_progress("conflict_main_2", 0.5)
    manager.update_conflict_progress("conflict_main_3", 0.2)

    print(f"\n冲突进度:")
    print(f"  conflict_main_1: {manager.get_conflict_progress('conflict_main_1'):.1%}")
    print(f"  conflict_main_2: {manager.get_conflict_progress('conflict_main_2'):.1%}")
    print(f"  conflict_main_3: {manager.get_conflict_progress('conflict_main_3'):.1%}")

    print(f"\n当前危机等级: {manager.get_escalation_level()}/10")


def test_save_and_load(manager: TimelineManager):
    """测试保存和加载"""
    print("\n" + "=" * 60)
    print("测试8: 保存和加载")
    print("=" * 60)

    # 保存
    manager.save()
    print(f"\n已保存时间线到: {manager.save_dir}")

    # 重新加载
    timeline_id = manager.get_timeline().timeline_id
    new_manager = TimelineManager(save_dir="test_data/timeline")
    loaded_timeline = new_manager._load_timeline_file(timeline_id)

    if loaded_timeline:
        print(f"重新加载成功: {loaded_timeline.timeline_id}")
        print(f"  事件数: {len(loaded_timeline.events)}")
        print(f"  节点数: {len(loaded_timeline.timeline_nodes)}")
        print(f"  当前章节: {loaded_timeline.current_chapter}")

        # 验证数据一致性
        assert loaded_timeline.timeline_id == manager.get_timeline().timeline_id
        assert len(loaded_timeline.events) == len(manager.get_timeline().events)
        print("数据一致性验证通过!")
    else:
        print("重新加载失败")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("时间线管理器测试套件")
    print("=" * 60)

    try:
        # 测试1: 加载时间线
        manager, timeline = test_load_from_worldbuilding()

        # 测试2: 加载大纲节点
        test_load_from_outline(manager)

        # 测试3: 添加事件
        events = test_add_events(manager)

        # 测试4: 事件管理
        test_event_management(manager, events)

        # 测试5: 节点管理
        test_node_management(manager)

        # 测试6: 时间推进
        test_time_progression(manager)

        # 测试7: 冲突进度
        test_conflict_progress(manager)

        # 测试8: 保存和加载
        test_save_and_load(manager)

        print("\n" + "=" * 60)
        print("所有测试完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
