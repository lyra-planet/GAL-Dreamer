"""
测试完整故事规划 - 使用真实 LLM API
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.story_orchestration.story_planner_agent import StoryPlannerAgent
from pipelines.story_orchestration.story_orchestration_pipeline import StoryOrchestrationPipeline


def test_generate_full_story():
    """测试生成完整 15 章故事"""
    print("=== 测试生成完整 15 章故事 ===\n")

    # 加载故事大纲
    outline_path = "/Users/lyra/Desktop/GAL-Dreamer/output/20251230_050843/story_outline.json"
    with open(outline_path, 'r', encoding='utf-8') as f:
        outline_data = json.load(f)

    # 提取必要信息
    outline = outline_data.get("steps", {}).get("premise", {})
    cast_arc = outline_data.get("steps", {}).get("cast_arc", {})
    conflict_engine = outline_data.get("steps", {}).get("conflict_engine", {})

    # 构建角色列表
    characters = []
    if cast_arc.get("protagonist"):
        protagonist = cast_arc["protagonist"]
        characters.append({
            "character_id": protagonist.get("character_id"),
            "name": protagonist.get("character_name"),
            "role": "protagonist",
            "initial_state": protagonist.get("initial_state"),
            "growth_nodes": protagonist.get("growth_nodes", [])
        })

    for heroine in cast_arc.get("heroines", []):
        characters.append({
            "character_id": heroine.get("character_id"),
            "name": heroine.get("character_name"),
            "role": "heroine",
            "initial_state": heroine.get("initial_state"),
            "growth_nodes": heroine.get("growth_nodes", [])
        })

    # 构建冲突列表
    conflicts = []
    conflict_map = conflict_engine.get("map", {})
    for conflict in conflict_map.get("main_conflicts", []):
        conflicts.append({
            "conflict_id": conflict.get("conflict_id"),
            "name": conflict.get("conflict_name"),
            "type": conflict.get("conflict_type"),
            "description": conflict.get("opposing_forces")
        })

    print(f"故事前提: {outline.get('hook', '')}")
    print(f"角色数量: {len(characters)}")
    print(f"冲突数量: {len(conflicts)}")
    print()

    # 创建 Pipeline
    pipeline = StoryOrchestrationPipeline()

    print("开始生成完整故事规划...\n")

    try:
        # 生成完整故事
        story_direction = pipeline.generate_full_story(
            outline=outline,
            world_setting=outline_data.get("steps", {}),
            characters=characters,
            conflicts=conflicts,
            chapter_count=15
        )

        print("\n" + "=" * 60)
        print("完整故事规划生成成功!")
        print("=" * 60)
        print(f"规划ID: {story_direction.plan_id}")
        print(f"章节数: {len(story_direction.chapters)}")
        print(f"情感曲线: {story_direction.emotional_arc}")
        print()

        # 打印每章摘要
        for chapter in story_direction.chapters:
            print(f"--- 第{chapter.chapter_number}章: {chapter.title} ---")
            print(f"目标: {chapter.goal}")
            print(f"情绪: {chapter.mood}")
            print(f"关键事件: {len(chapter.key_events)} 个")
            if chapter.reveal:
                print(f"揭示: {', '.join(chapter.reveal[:2])}...")
            if chapter.has_choice:
                print(f"选择点: {chapter.choice_condition}")
            print()

        return story_direction

    except Exception as e:
        print(f"生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_generate_full_story()
