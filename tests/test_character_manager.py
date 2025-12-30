"""
角色管理器测试
测试从story_outline.json加载角色、创建新角色、更新状态等功能
"""
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime.character_manager import CharacterManager
from models.runtime.character import (
    RuntimeCharacter,
    HeroineCharacter,
    MoodType,
    CharacterGoal,
    CharacterItem
)


def test_load_from_outline():
    """测试从story_outline.json加载角色"""
    print("\n" + "=" * 60)
    print("测试1: 从 story_outline.json 加载角色")
    print("=" * 60)

    manager = CharacterManager(save_dir="test_data/characters")

    outline_path = "output/20251230_050843/story_outline.json"

    # 加载角色
    characters = manager.load_from_outline(outline_path)

    print(f"\n成功加载 {len(characters)} 个角色:")

    # 显示主角
    protagonist = manager.get_protagonist()
    if protagonist:
        print(f"\n[主角] {protagonist.character_name}")
        print(f"  ID: {protagonist.character_id}")
        print(f"  目标: {protagonist.surface_goal}")
        print(f"  深层需求: {protagonist.deep_need}")

    # 显示女主
    heroines = manager.get_heroines()
    print(f"\n[女主] 共 {len(heroines)} 位:")
    for heroine in heroines:
        print(f"  - {heroine.character_name}")
        print(f"    好感度: {heroine.affection_value}/100 ({heroine.affection_stage.value})")
        print(f"    目标: {heroine.surface_goal}")

    # 显示配角
    supporting = manager.get_supporting_cast()
    print(f"\n[配角] 共 {len(supporting)} 位:")
    for char in supporting[:5]:
        print(f"  - {char.character_name}")

    return manager, characters


def test_create_new_character(manager: CharacterManager):
    """测试创建新角色"""
    print("\n" + "=" * 60)
    print("测试2: 创建新角色")
    print("=" * 60)

    # 创建一个新的女主
    new_heroine = manager.create_character(
        character_id="heroine_new_001",
        name="月光",
        role_type="heroine",
        appearance={
            "hair": "银色长发",
            "eyes": "紫色",
            "height": "165cm",
            "style": "优雅神秘"
        },
        personality=["神秘", "温柔", "忧郁", "善解人意"],
        speaking_style={
            "tone": "轻柔",
            "catchphrase": "月亮会见证一切..."
        },
        background_story="来自月界的神秘少女，因意外来到人间，寻找回到故乡的方法。",
        origin="月界",
        surface_goal="找到返回月界的方法",
        deep_need="找到真正的归属，不再孤独",
        ghost_or_wound="曾被月界的人背叛，独自流亡",
        misbelief="没有人会真心对待异乡人",
        greatest_fear="永远无法回到故乡",
        growth_nodes=["学会信任人类", "找到心中的第二个故乡", "接受过去"],
        route_type="sweet",
        route_hook="神秘而温柔，像月光一样治愈人心",
        secret="她其实是月界公主",
        bottom_line="不背叛信任自己的人"
    )

    print(f"\n创建新女主: {new_heroine.character_name}")
    print(f"  ID: {new_heroine.character_id}")
    print(f"  外貌: {new_heroine.appearance}")
    print(f"  性格: {', '.join(new_heroine.personality)}")

    return new_heroine


def test_update_state(manager: CharacterManager, character_id: str):
    """测试更新角色状态"""
    print("\n" + "=" * 60)
    print("测试3: 更新角色状态")
    print("=" * 60)

    char = manager.get_character(character_id)
    if not char:
        print(f"角色不存在: {character_id}")
        return

    print(f"\n更新角色: {char.character_name}")

    # 更新心情
    manager.update_mood(character_id, MoodType.HAPPY, "遇到了开心的事", intensity=8)
    print(f"  心情更新: {char.current_state.current_mood.value}")
    print(f"  原因: {char.current_state.mood_reason}")

    # 更新好感度
    success, delta, new_stage = manager.update_affection(character_id, 15)
    print(f"  好感度变化: +{delta}")
    print(f"  当前好感度: {char.affection_value}/100")
    print(f"  新阶段: {new_stage}")

    # 添加目标
    manager.add_goal(
        character_id,
        "了解主角的过去",
        goal_type="short_term",
        priority=8
    )
    print(f"  添加目标: 了解主角的过去")

    # 添加物品
    manager.add_item(
        character_id,
        item_id="item_locket",
        name="月光吊坠",
        description="来自月界的神秘吊坠，散发着淡淡的光芒",
        item_type="key_item",
        importance="critical"
    )
    print(f"  添加物品: 月光吊坠")

    # 添加记忆
    manager.add_memory(
        character_id,
        "与主角初次相遇，他在月光下温柔地对自己说话",
        memory_type="conversation",
        importance="major"
    )
    print(f"  添加记忆: 初次相遇")

    # 显示当前状态
    print(f"\n当前状态:")
    print(f"  活跃目标: {len(char.get_active_goals())} 个")
    print(f"  身上物品: {len(char.inventory)} 件")
    print(f"  记忆数量: {len(char.memories)} 条")


def test_affection_ranking(manager: CharacterManager):
    """测试好感度排名"""
    print("\n" + "=" * 60)
    print("测试4: 好感度排名")
    print("=" * 60)

    ranking = manager.get_affection_ranking()

    print("\n好感度排名:")
    for i, (char_id, char_name, affection) in enumerate(ranking[:10], 1):
        char = manager.get_character(char_id)
        stage = char.affection_stage.value if char else "unknown"
        print(f"  {i}. {char_name}: {affection}/100 ({stage})")


def test_character_search(manager: CharacterManager):
    """测试角色查询功能"""
    print("\n" + "=" * 60)
    print("测试5: 角色查询")
    print("=" * 60)

    # 按心情查询
    happy_chars = manager.get_characters_by_mood(MoodType.HAPPY)
    print(f"\n开心的角色: {len(happy_chars)} 位")
    for char in happy_chars:
        print(f"  - {char.character_name}: {char.current_state.current_mood.value}")

    # 拥有指定物品的角色
    chars_with_locket = manager.get_characters_with_item("item_locket")
    print(f"\n拥有月光吊坠的角色: {len(chars_with_locket)} 位")
    for char in chars_with_locket:
        print(f"  - {char.character_name}")

    # 获取所有活跃角色
    active_chars = manager.get_active_characters()
    print(f"\n活跃角色: {len(active_chars)} 位")


def test_relationship_management(manager: CharacterManager):
    """测试关系管理"""
    print("\n" + "=" * 60)
    print("测试6: 关系管理")
    print("=" * 60)

    # 获取两个角色
    heroines = manager.get_heroines()
    if len(heroines) >= 2:
        char1 = heroines[0]
        char2 = heroines[1]

        # 设置她们之间的关系
        manager.set_relationship(
            char1.character_id,
            char2.character_id,
            relationship_type="friend",
            affection=60,
            trust=50
        )

        rel = char1.get_relationship(char2.character_id)
        if rel:
            print(f"\n{char1.character_name} -> {char2.character_name}:")
            print(f"  关系类型: {rel.relationship_type}")
            print(f"  好感度: {rel.affection_level}/100")
            print(f"  信任度: {rel.trust_level}/100")


def test_growth_nodes(manager: CharacterManager):
    """测试成长节点触发"""
    print("\n" + "=" * 60)
    print("测试7: 成长节点触发")
    print("=" * 60)

    heroine = manager.get_heroines()[0]
    print(f"\n角色: {heroine.character_name}")

    # 显示所有成长节点
    print(f"\n成长节点:")
    for i, node in enumerate(heroine.growth_nodes, 1):
        triggered = node in heroine.triggered_growth_nodes
        status = "✓" if triggered else " "
        print(f"  {status} {i}. {node}")

    # 触发一个成长节点
    if heroine.growth_nodes:
        node = heroine.growth_nodes[0]
        success = manager.trigger_growth_node(heroine.character_id, node)
        if success:
            print(f"\n已触发成长节点: {node}")


def test_save_and_load(manager: CharacterManager):
    """测试保存和加载"""
    print("\n" + "=" * 60)
    print("测试8: 保存和加载")
    print("=" * 60)

    # 保存所有角色
    manager.save_all()
    print(f"\n已保存所有角色到: {manager.save_dir}")

    # 创建新的管理器并加载
    new_manager = CharacterManager(save_dir="test_data/characters")
    new_manager._load_all_characters()

    print(f"从文件加载了 {len(new_manager._characters)} 个角色")

    # 验证数据一致性
    for char_id in manager._characters:
        old_char = manager.get_character(char_id)
        new_char = new_manager.get_character(char_id)

        if old_char and new_char:
            assert old_char.character_name == new_char.character_name
            assert old_char.affection_value == new_char.affection_value

    print("数据一致性验证通过!")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("角色管理器测试套件")
    print("=" * 60)

    try:
        # 测试1: 加载角色
        manager, characters = test_load_from_outline()

        # 测试2: 创建新角色
        new_heroine = test_create_new_character(manager)

        # 测试3: 更新状态
        if heroines := manager.get_heroines():
            test_update_state(manager, heroines[0].character_id)

        # 测试4: 好感度排名
        test_affection_ranking(manager)

        # 测试5: 角色查询
        test_character_search(manager)

        # 测试6: 关系管理
        test_relationship_management(manager)

        # 测试7: 成长节点
        if heroines := manager.get_heroines():
            test_growth_nodes(manager)

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
