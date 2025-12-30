"""
完整故事安排 Pipeline
生成 10-20 章完整故事，支持根据玩家选择动态调整
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from agents.story_orchestration.story_planner_agent import StoryPlannerAgent
from models.runtime.story_plan import StoryDirection, ChapterDirection
from runtime.timeline_manager import TimelineManager
from runtime.character_manager import CharacterManager
from utils.logger import log


class StoryOrchestrationPipeline:
    """完整故事安排 Pipeline - 生成 10-20 章完整故事，支持动态调整"""

    def __init__(
        self,
        save_dir: str = "runtime_data",
        planner_agent: Optional[StoryPlannerAgent] = None
    ):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

        self.planner = planner_agent or StoryPlannerAgent()
        self.timeline_manager = TimelineManager(save_dir)
        # CharacterManager 默认用 runtime_data/characters 子目录
        self.character_manager = CharacterManager(f"{save_dir}/characters")

        self._current_plan: Optional[StoryDirection] = None
        self._current_chapter_index: int = 0
        self._player_choices: List[Dict[str, Any]] = []

    def generate_full_story(
        self,
        outline: Dict[str, Any],
        world_setting: Dict[str, Any],
        characters: List[Dict[str, Any]],
        conflicts: List[Dict[str, Any]] = None,
        chapter_count: int = 15
    ) -> StoryDirection:
        """生成完整 10-20 章故事规划"""
        log.info(f"开始生成完整故事规划 ({chapter_count} 章)...")

        # 确保 timeline 已初始化
        if self.timeline_manager._timeline is None:
            self.timeline_manager.load_or_create()

        # 获取当前时间线历史
        timeline_history = self.timeline_manager.get_all_history()

        # 获取当前角色状态
        character_states = self._get_character_states()

        # 调用规划 Agent
        result = self.planner.run(
            outline=json.dumps(outline, ensure_ascii=False),
            world_setting=json.dumps(world_setting, ensure_ascii=False),
            characters=json.dumps(characters, ensure_ascii=False),
            conflicts=json.dumps(conflicts or [], ensure_ascii=False),
            timeline_history=json.dumps(timeline_history, ensure_ascii=False),
            character_states=json.dumps(character_states, ensure_ascii=False),
            chapter_count=chapter_count
        )

        self._current_plan = StoryDirection(**result)
        self._save_plan()

        log.info(f"完整故事规划生成完成，共 {len(self._current_plan.chapters)} 章")
        log.info(f"情感曲线: {self._current_plan.emotional_arc}")

        return self._current_plan

    def get_current_chapter_direction(self) -> Optional[ChapterDirection]:
        """获取当前章节的方向"""
        if not self._current_plan:
            return None
        if self._current_chapter_index >= len(self._current_plan.chapters):
            return None
        return self._current_plan.chapters[self._current_chapter_index]

    def record_player_choice(
        self,
        choice_id: str,
        option_id: str,
        description: str,
        consequence: str = ""
    ) -> None:
        """记录玩家选择"""
        choice_record = {
            "chapter": self._current_chapter_index + 1,
            "choice_id": choice_id,
            "option_id": option_id,
            "description": description,
            "consequence": consequence
        }
        self._player_choices.append(choice_record)
        log.info(f"记录玩家选择: {description} -> {option_id}")

    def adjust_remaining_story(self) -> StoryDirection:
        """根据当前状态调整剩余章节规划

        在每章结束后调用，根据：
        - 当前进度
        - 时间线历史
        - 角色状态
        - 玩家选择

        动态调整剩余章节
        """
        if not self._current_plan:
            raise RuntimeError("没有可调整的故事规划")

        log.info(f"调整剩余故事规划 (当前章节: {self._current_chapter_index + 1})...")

        # 获取已完成章节
        completed_chapters = [
            chapter.model_dump()
            for chapter in self._current_plan.chapters[:self._current_chapter_index + 1]
        ]

        # 获取当前时间线历史
        timeline_history = self.timeline_manager.get_all_history()

        # 获取当前角色状态
        character_states = self._get_character_states()

        # 调用 Agent 调整
        adjusted = self.planner.adjust_story(
            original_plan=self._current_plan.model_dump(),
            completed_chapters=completed_chapters,
            timeline_history=timeline_history,
            character_states=character_states,
            player_choices=self._player_choices
        )

        self._current_plan = StoryDirection(**adjusted)
        self._save_plan()

        log.info(f"故事规划已调整，剩余 {len(self._current_plan.chapters) - self._current_chapter_index - 1} 章")

        return self._current_plan

    def advance_chapter(self) -> bool:
        """推进到下一章"""
        if not self._current_plan:
            return False
        if self._current_chapter_index + 1 >= len(self._current_plan.chapters):
            return False
        self._current_chapter_index += 1
        return True

    def _get_character_states(self) -> Dict[str, Any]:
        """获取所有角色的当前状态"""
        all_characters = self.character_manager.get_all_characters()
        states = {}
        for char_id, char in all_characters.items():
            states[char_id] = {
                "id": char.character_id,
                "name": char.character_name,
                "mood": char.current_mood.value if char.current_mood else "",
                "affection": char.affection_stage.value if char.affection_stage else "",
                "goals": [g.description for g in char.goals]
            }
        return states

    def _save_plan(self):
        """保存规划"""
        if self._current_plan:
            plan_file = self.save_dir / "story_direction.json"
            with open(plan_file, 'w', encoding='utf-8') as f:
                json.dump(
                    self._current_plan.model_dump(),
                    f,
                    ensure_ascii=False,
                    indent=2
                )

    def load_plan(self, plan_path: str = None) -> StoryDirection:
        """加载已保存的规划"""
        if plan_path is None:
            plan_path = self.save_dir / "story_direction.json"

        with open(plan_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self._current_plan = StoryDirection(**data)
        return self._current_plan

    @property
    def current_plan(self) -> Optional[StoryDirection]:
        """获取当前规划"""
        return self._current_plan

    @property
    def current_chapter_index(self) -> int:
        """获取当前章节索引"""
        return self._current_chapter_index

    @property
    def player_choices(self) -> List[Dict[str, Any]]:
        """获取玩家选择记录"""
        return self._player_choices.copy()
