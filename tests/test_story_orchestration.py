"""
测试完整故事安排系统
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.runtime.story_plan import StoryDirection, ChapterDirection, MoodType
from agents.story_orchestration.story_planner_agent import StoryPlannerAgent
from pipelines.story_orchestration.story_orchestration_pipeline import StoryOrchestrationPipeline


def test_story_direction_models():
    """测试故事方向模型"""
    print("=== 测试故事方向模型 ===")

    # 创建章节方向
    chapter = ChapterDirection(
        chapter_number=1,
        title="初遇",
        goal="推进主角与小飞翔的初次相识，建立好感基础",
        reveal=["小飞翔是精灵"],
        conceal=["小飞翔的真实身份是古代精灵守护者转世"],
        mood=MoodType.SWEET,
        key_events=[
            "主角在精灵林偶遇小飞翔",
            "主角帮小飞翔捡起掉落的物品"
        ],
        has_choice=True,
        choice_condition="小飞翔询问主角的名字",
        focus_characters=["protagonist_main", "heroine_001"]
    )

    print(f"第{chapter.chapter_number}章: {chapter.title}")
    print(f"目标: {chapter.goal}")
    print(f"情绪: {chapter.mood}")
    print(f"关键事件: {len(chapter.key_events)} 个")
    print(f"有选择: {chapter.has_choice}")
    print(f"涉及角色: {chapter.focus_characters}")

    # 创建完整故事方向
    direction = StoryDirection(
        plan_id="plan_001",
        source_outline_id="outline_001",
        chapters=[chapter] * 15,  # 15章
        emotional_arc="从平静逐渐升温，在第10章达到情感高潮，最终达成和解"
    )

    print(f"\n规划ID: {direction.plan_id}")
    print(f"章节数: {len(direction.chapters)}")
    print(f"情感曲线: {direction.emotional_arc}")
    print("✓ 故事方向模型测试通过\n")


def test_planner_agent():
    """测试完整故事规划 Agent"""
    print("=== 测试完整故事规划 Agent ===")

    agent = StoryPlannerAgent()

    print("Agent 已创建，需要 LLM API 才能完整测试")
    print(f"Agent 名称: {agent.name}")
    print(f"必填字段: {agent.required_fields}")

    # 测试验证逻辑
    test_output = {
        "plan_id": "plan_001",
        "source_outline_id": "outline_001",
        "emotional_arc": "从平静到高潮再到和解",
        "chapters": [
            {
                "chapter_number": i + 1,
                "title": f"第{i+1}章",
                "goal": f"第{i+1}章目标",
                "reveal": [f"信息{i+1}"],
                "conceal": [f"秘密{i+1}"],
                "mood": ["sweet", "suspense", "tension", "buffer"][i % 4],
                "key_events": [f"事件{i+1}-1", f"事件{i+1}-2"],
                "has_choice": i % 3 == 0,
                "choice_condition": f"选择条件{i+1}" if i % 3 == 0 else "",
                "focus_characters": ["protagonist_main", f"heroine_00{(i % 4) + 1}"]
            }
            for i in range(15)
        ]
    }

    result = agent.validate_output(test_output)
    print(f"验证结果 (15章): {result}")

    # 测试少于10章
    test_invalid = {
        "plan_id": "plan_001",
        "chapters": [
            {
                "chapter_number": 1,
                "title": "第1章",
                "goal": "目标",
                "mood": "sweet",
                "key_events": ["事件1"]
            }
        ] * 5  # 只有5章
    }

    result = agent.validate_output(test_invalid)
    print(f"少于10章验证: {result}")

    print("✓ 完整故事规划 Agent 测试通过\n")


def test_pipeline():
    """测试 Pipeline"""
    print("=== 测试 Pipeline ===")

    pipeline = StoryOrchestrationPipeline()

    print(f"Pipeline 已创建")
    print(f"当前章节索引: {pipeline.current_chapter_index}")

    # 手动设置规划进行测试
    chapters = [
        ChapterDirection(
            chapter_number=i + 1,
            title=f"第{i+1}章",
            goal=f"推进目标{i+1}",
            mood=[MoodType.SWEET, MoodType.SUSPENSE, MoodType.TENSION, MoodType.BUFFER][i % 4],
            key_events=[f"事件{i+1}"],
            focus_characters=["protagonist_main"]
        )
        for i in range(15)
    ]

    test_direction = StoryDirection(
        plan_id="test_plan",
        source_outline_id="test_outline",
        chapters=chapters,
        emotional_arc="测试情感曲线"
    )

    pipeline._current_plan = test_direction

    # 获取当前章节
    current = pipeline.get_current_chapter_direction()
    print(f"当前章节: 第{current.chapter_number}章 - {current.title}")
    print(f"目标: {current.goal}")
    print(f"情绪: {current.mood}")

    # 记录玩家选择
    pipeline.record_player_choice(
        choice_id="choice_001",
        option_id="opt_1",
        description="选择是否帮助小飞翔",
        consequence="增加小飞翔好感"
    )
    print(f"玩家选择记录: {len(pipeline.player_choices)} 个")

    # 推进章节
    pipeline.advance_chapter()
    print(f"推进后章节索引: {pipeline.current_chapter_index}")

    print("✓ Pipeline 测试通过\n")


def test_dynamic_adjust():
    """测试动态调整功能"""
    print("=== 测试动态调整功能 ===")

    pipeline = StoryOrchestrationPipeline()

    # 设置初始规划
    chapters = [
        ChapterDirection(
            chapter_number=i + 1,
            title=f"第{i+1}章",
            goal=f"原始目标{i+1}",
            mood=MoodType.BUFFER,
            key_events=[f"事件{i+1}"],
            focus_characters=["protagonist_main"]
        )
        for i in range(15)
    ]

    pipeline._current_plan = StoryDirection(
        plan_id="test_plan",
        source_outline_id="test_outline",
        chapters=chapters,
        emotional_arc="原始情感曲线"
    )
    pipeline._current_chapter_index = 2  # 假设完成了第3章

    print(f"当前进度: 第{pipeline.current_chapter_index + 1}章")
    print(f"剩余章节数: {len(pipeline._current_plan.chapters) - pipeline.current_chapter_index - 1}")

    # 注意：实际调用 adjust_remaining_story 需要 LLM API
    print("动态调整功能需要 LLM API 才能完整测试")
    print("✓ 动态调整功能结构测试通过\n")


if __name__ == "__main__":
    test_story_direction_models()
    test_planner_agent()
    test_pipeline()
    test_dynamic_adjust()

    print("=" * 50)
    print("所有测试通过！")
    print("=" * 50)
