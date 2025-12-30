"""
完整故事规划 Agent
根据大纲生成 10-20 章完整故事，支持动态调整
"""
from typing import Any, Dict, Union, List
from agents.base_agent import BaseAgent
from models.runtime.story_plan import StoryDirection
from prompts.story_orchestration.story_planner_prompt import (
    get_story_planner_prompts,
    STORY_PLANNER_SYSTEM_PROMPT,
    STORY_PLANNER_HUMAN_PROMPT,
    STORY_PLANNER_ADJUST_PROMPT
)


class StoryPlannerAgent(BaseAgent):
    """完整故事规划 Agent"""

    name = "StoryPlannerAgent"
    system_prompt = STORY_PLANNER_SYSTEM_PROMPT
    human_prompt_template = STORY_PLANNER_HUMAN_PROMPT
    required_fields = ["plan_id", "chapters"]
    output_model = StoryDirection

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """验证输出格式"""
        if "chapters" not in output:
            return "缺少 chapters 字段"

        chapters = output["chapters"]
        if not isinstance(chapters, list) or len(chapters) < 10:
            return "chapters 必须至少包含 10 章"

        valid_moods = {"sweet", "suspense", "tension", "buffer"}

        for i, chapter in enumerate(chapters):
            required_fields = ["chapter_number", "title", "goal", "mood", "key_events"]
            for field in required_fields:
                if field not in chapter:
                    return f"章节 {i+1} 缺少 {field} 字段"

            # 验证 mood（不区分大小写）
            mood = chapter.get("mood", "")
            if mood.lower() not in valid_moods:
                return f"章节 {i+1} 的 mood 必须是 sweet/suspense/tension/buffer 之一"

            # 验证 key_events
            key_events = chapter.get("key_events", [])
            if not isinstance(key_events, list) or len(key_events) == 0:
                return f"章节 {i+1} 的 key_events 必须是非空列表"

            # 章节号必须连续
            if chapter.get("chapter_number") != i + 1:
                return f"章节 {i+1} 的 chapter_number 应该是 {i+1}"

        return True

    def adjust_story(
        self,
        original_plan: Dict[str, Any],
        completed_chapters: List[Dict[str, Any]],
        timeline_history: List[Dict[str, Any]],
        character_states: Dict[str, Any],
        player_choices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """根据当前状态调整后续故事

        Args:
            original_plan: 原始故事规划
            completed_chapters: 已完成的章节
            timeline_history: 当前时间线历史
            character_states: 当前角色状态
            player_choices: 玩家的选择记录

        Returns:
            调整后的故事规划
        """
        import json
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=self._config.system_prompt),
            HumanMessage(content=STORY_PLANNER_ADJUST_PROMPT.format(
                original_plan=json.dumps(original_plan, ensure_ascii=False, indent=2),
                completed_chapters=json.dumps(completed_chapters, ensure_ascii=False, indent=2),
                timeline_history=json.dumps(timeline_history, ensure_ascii=False, indent=2),
                character_states=json.dumps(character_states, ensure_ascii=False, indent=2),
                player_choices=json.dumps(player_choices, ensure_ascii=False, indent=2)
            ))
        ]

        response = self._llm.invoke(messages)
        result = self._extract_json(response.content)

        # 验证调整后的规划
        validation_result = self._validate_output(result)
        if validation_result is True:
            return result
        else:
            # 尝试修复
            return self._fix_json_output(result, str(validation_result))
