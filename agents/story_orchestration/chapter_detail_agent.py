"""
Chapter Detail Agent
GAL游戏剧情细化 Agent - 根据章节大纲生成具体的场景和对话
"""
import uuid
import json
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from agents.base_agent import BaseAgent
from prompts.story_orchestration.chapter_detail_prompt import (
    CHAPTER_DETAIL_SYSTEM_PROMPT,
    CHAPTER_DETAIL_HUMAN_PROMPT
)
from pydantic import BaseModel, Field
from utils.config import config
from utils.logger import log
from utils.json_utils import safe_parse_json


class SceneEvent(BaseModel):
    """场景事件"""
    type: str = Field(..., description="事件类型: narration/dialogue/action")
    speaker: Optional[str] = Field(None, description="说话者角色ID")
    content: str = Field(..., description="内容")
    emotion: Optional[str] = Field(None, description="表情")
    action: Optional[str] = Field(None, description="动作")


class Scene(BaseModel):
    """一幕"""
    scene: int = Field(..., description="幕号")
    title: str = Field(..., description="标题")
    location: str = Field(..., description="场景")
    time_of_day: str = Field(..., description="时间段")
    background: str = Field(..., description="场景背景描述")
    narration: str = Field(..., description="开场旁白")
    events: List[SceneEvent] = Field(default_factory=list, description="事件列表")


class ChapterDetail(BaseModel):
    """章节详情"""
    chapter: int = Field(..., description="章节号")
    chapter_id: str = Field(..., description="章节ID")
    characters: List[Dict[str, str]] = Field(default_factory=list, description="本章节出场角色列表")
    scenes: List[Scene] = Field(default_factory=list, description="场景列表")


class ChapterDetailAgent(BaseAgent):
    """
    章节详情Agent

    根据章节规划生成具体的游戏剧本内容
    """
    name = "ChapterDetailAgent"
    system_prompt = CHAPTER_DETAIL_SYSTEM_PROMPT
    human_prompt_template = CHAPTER_DETAIL_HUMAN_PROMPT
    required_fields = ["scenes"]
    output_model = ChapterDetail

    def __init__(self):
        super().__init__()
        self.generated_chapters = {}  # 存储已生成的章节

    def process(
        self,
        chapter_plan: Dict[str, Any],
        route_strategy_data: Dict[str, Any],
        story_outline_data: Dict[str, Any],
        world_setting_data: Dict[str, Any],
        previous_chapter: Optional[Dict[str, Any]] = None,
        user_idea: str = ""
    ) -> ChapterDetail:
        """
        生成章节详情

        Args:
            chapter_plan: 当前章节规划（从route_strategy.json中获取）
            route_strategy_data: 完整路线战略数据（包含所有章节规划）
            story_outline_data: 故事大纲数据
            world_setting_data: 世界观设定数据
            previous_chapter: 前一章节详情（可选）
            user_idea: 用户创意

        Returns:
            章节详情
        """
        if not chapter_plan:
            raise ValueError("chapter_plan不能为空")
        if not route_strategy_data:
            raise ValueError("route_strategy_data不能为空")
        if not story_outline_data:
            raise ValueError("story_outline_data不能为空")
        if not world_setting_data:
            raise ValueError("world_setting_data不能为空")

        steps = story_outline_data.get("steps", {})
        if not steps:
            raise ValueError("story_outline_data中缺少steps数据")

        if not user_idea:
            user_idea = story_outline_data.get("input", {}).get("user_idea", "")

        chapter_num = chapter_plan.get("chapter", 0)
        chapter_id = chapter_plan.get("id", "")
        log.info(f"生成第{chapter_num}章详情 ({chapter_id})...")

        # 构建故事数据（只传递需要的部分）
        relevant_data = {
            "premise": steps.get("premise", {}),
            "cast_arc": steps.get("cast_arc", {}),
            "conflict_map": steps.get("conflict_engine", {}).get("map", {})
        }
        steps_json = json.dumps(relevant_data, ensure_ascii=False, separators=(',', ':'))

        # 提取完整路线战略（所有章节概览）
        route_strategy = route_strategy_data.get("steps", {}).get("route_strategy", {})
        all_chapters = route_strategy.get("chapters", [])
        major_conflicts = route_strategy.get("major_conflicts", [])
        main_plot_summary = route_strategy.get("main_plot_summary", "")

        # 格式化完整路线战略（简要版，节省token）
        full_route_strategy = self._format_full_route_strategy(all_chapters, major_conflicts, main_plot_summary)

        # 提取locations
        key_elements = world_setting_data.get("key_elements", {})
        if isinstance(key_elements, dict):
            locations = key_elements.get("locations", [])
        else:
            locations = []

        # 提取scene_presets
        atmosphere = world_setting_data.get("atmosphere", {})
        if isinstance(atmosphere, dict):
            scene_presets = atmosphere.get("scene_presets", [])
        else:
            scene_presets = []

        # 提取character_list
        cast_arc = steps.get("cast_arc", {})
        character_list = self._format_character_list(cast_arc)

        # 格式化数据
        chapter_plan_json = json.dumps(chapter_plan, ensure_ascii=False, indent=2)
        locations_json = self._format_locations(locations)
        scene_presets_json = self._format_scene_presets(scene_presets)

        # 格式化前一章节
        previous_chapter_json = "[]"  # 默认为空
        if previous_chapter:
            previous_chapter_json = self._format_previous_chapter(previous_chapter)

        try:
            result = self.run(
                user_idea=user_idea,
                steps_data=steps_json,
                full_route_strategy=full_route_strategy,
                chapter_plan=chapter_plan_json,
                locations=locations_json,
                scene_presets=scene_presets_json,
                character_list=character_list,
                previous_chapter=previous_chapter_json
            )

            # 添加元数据
            result["chapter"] = chapter_num
            result["chapter_id"] = chapter_id

            detail = ChapterDetail(**result)

            # 保存已生成的章节
            self.generated_chapters[chapter_id] = detail

            self._log_success(detail)
            return detail

        except Exception as e:
            log.error(f"ChapterDetailAgent 生成第{chapter_num}章失败: {e}")
            raise RuntimeError(f"章节详情生成失败: {e}") from e

    def _format_locations(self, locations: list) -> str:
        """格式化场景列表"""
        if not locations:
            return "[]"
        location_list = []
        for loc in locations:
            location_list.append({
                "location_id": loc.get("location_id", ""),
                "name": loc.get("name", ""),
                "description": loc.get("description", ""),
                "atmosphere": loc.get("atmosphere", "")
            })
        return json.dumps(location_list, ensure_ascii=False, indent=2)

    def _format_scene_presets(self, scene_presets: list) -> str:
        """格式化场景预设列表"""
        if not scene_presets:
            return "[]"
        preset_list = []
        for preset in scene_presets:
            preset_list.append({
                "scene_type": preset.get("scene_type", ""),
                "visual_style": preset.get("visual_style", ""),
                "mood": preset.get("mood", ""),
                "color_palette": preset.get("color_palette", [])
            })
        return json.dumps(preset_list, ensure_ascii=False, indent=2)

    def _format_character_list(self, cast_arc: dict) -> str:
        """格式化角色列表"""
        if not cast_arc:
            return "[]"

        character_list = []

        # 主角
        protagonist = cast_arc.get("protagonist", {})
        if protagonist:
            character_list.append({
                "character_id": protagonist.get("character_id", "protagonist_main"),
                "character_name": protagonist.get("character_name", ""),
                "role_type": "protagonist",
                "personality": protagonist.get("surface_goal", ""),
                "initial_state": protagonist.get("initial_state", "")
            })

        # 女主
        for heroine in cast_arc.get("heroines", []):
            character_list.append({
                "character_id": heroine.get("character_id", ""),
                "character_name": heroine.get("character_name", ""),
                "role_type": "heroine",
                "personality": heroine.get("surface_goal", ""),
                "initial_state": heroine.get("initial_state", "")
            })

        # 配角
        for supporting in cast_arc.get("supporting_cast", []):
            character_list.append({
                "character_id": supporting.get("character_id", ""),
                "character_name": supporting.get("character_name", ""),
                "role_type": "supporting",
                "personality": supporting.get("surface_goal", ""),
                "initial_state": supporting.get("initial_state", "")
            })

        # 反派
        for antagonist in cast_arc.get("antagonists", []):
            character_list.append({
                "character_id": antagonist.get("character_id", ""),
                "character_name": antagonist.get("character_name", ""),
                "role_type": "antagonist",
                "personality": antagonist.get("surface_goal", ""),
                "initial_state": antagonist.get("initial_state", "")
            })

        return json.dumps(character_list, ensure_ascii=False, indent=2)

    def _format_full_route_strategy(self, all_chapters: list, major_conflicts: list, main_plot_summary: str) -> str:
        """格式化完整路线战略（简要版，用于了解整体结构）"""
        # 只保留关键信息，节省token
        summary = {
            "main_plot_summary": main_plot_summary,
            "total_chapters": len(all_chapters),
            "major_conflicts": [
                {
                    "name": mc.get("name", ""),
                    "position_chapter": mc.get("position_chapter", "")
                }
                for mc in major_conflicts
            ],
            "chapters_overview": [
                {
                    "chapter": ch.get("chapter", 0),
                    "id": ch.get("id", ""),
                    "title": ch.get("title", ""),
                    "story_phase": ch.get("story_phase", ""),
                    "location": ch.get("location", ""),
                    "time_of_day": ch.get("time_of_day", ""),
                    "characters": ch.get("characters", []),
                    "goal": ch.get("goal", ""),
                    "mood": ch.get("mood", "")
                }
                for ch in all_chapters
            ]
        }
        return json.dumps(summary, ensure_ascii=False, indent=2)

    def _format_previous_chapter(self, prev_chapter: Dict[str, Any]) -> str:
        """格式化前一章节（只提供简要信息）"""
        if not prev_chapter:
            return "[]"

        # 只提供前一章的最后一幕，作为承接参考
        scenes = prev_chapter.get("scenes", [])
        if not scenes:
            return "[]"

        last_scene = scenes[-1]
        summary = {
            "chapter": prev_chapter.get("chapter", 0),
            "chapter_id": prev_chapter.get("chapter_id", ""),
            "last_scene": {
                "title": last_scene.get("title", ""),
                "location": last_scene.get("location", ""),
                "ending_narration": last_scene.get("events", [])[-3:] if last_scene.get("events") else []
            }
        }

        return json.dumps(summary, ensure_ascii=False, indent=2)

    def _log_success(self, detail: ChapterDetail) -> None:
        """记录成功日志"""
        log.info(f"第{detail.chapter}章详情生成成功:")
        log.info(f"  章节ID: {detail.chapter_id}")
        log.info(f"  场景数: {len(detail.scenes)}")
        total_events = sum(len(scene.events) for scene in detail.scenes)
        log.info(f"  事件数: {total_events}")

    def get_previous_chapter(self, current_chapter_id: str) -> Optional[Dict[str, Any]]:
        """获取前一章节（按顺序）"""
        # 这里假设chapter_id格式为common_ch1, common_ch2等
        try:
            chapter_num = int(current_chapter_id.replace("common_ch", ""))
            prev_num = chapter_num - 1
            if prev_num < 1:
                return None
            prev_id = f"common_ch{prev_num}"
            prev_chapter = self.generated_chapters.get(prev_id)
            # 转换为字典
            if prev_chapter and hasattr(prev_chapter, "model_dump"):
                return prev_chapter.model_dump()
            return prev_chapter
        except (ValueError, AttributeError):
            return None

    def validate_output(self, output: Dict[str, Any]) -> bool | str:
        """验证输出"""
        scenes = output.get("scenes")
        if not isinstance(scenes, list) or not scenes:
            return "scenes必须是非空数组"

        for idx, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                return f"scenes[{idx}]必须是对象"
            if "scene" not in scene:
                return f"scenes[{idx}]缺少scene字段"
            if "events" not in scene:
                return f"scenes[{idx}]缺少events字段"
            events = scene.get("events")
            if not isinstance(events, list):
                return f"scenes[{idx}].events必须是数组"

        return True

    def clear(self):
        """清除已生成的章节数据"""
        self.generated_chapters.clear()

    def get_all_chapters(self) -> List[ChapterDetail]:
        """获取所有已生成的章节"""
        return list(self.generated_chapters.values())
