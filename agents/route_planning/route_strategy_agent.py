"""
Route Strategy Agent
路线战略规划 Agent - 提供整体路线架构的战略意见
"""
import uuid
import json
import re
from typing import Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from agents.base_agent import BaseAgent
from prompts.route_planning.route_strategy_prompt import (
    ROUTE_STRATEGY_SYSTEM_PROMPT,
    ROUTE_STRATEGY_HUMAN_PROMPT
)


def _format_locations(locations: list) -> str:
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
    import json
    return json.dumps(location_list, ensure_ascii=False, indent=2)


def _format_scene_presets(scene_presets: list) -> str:
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
    import json
    return json.dumps(preset_list, ensure_ascii=False, indent=2)


def _format_character_list(cast_arc: dict) -> str:
    """格式化角色列表"""
    if not cast_arc:
        return "[]"

    character_list = []

    # 添加主角
    protagonist = cast_arc.get("protagonist", {})
    if protagonist:
        character_list.append({
            "character_id": protagonist.get("character_id", "protagonist_main"),
            "character_name": protagonist.get("character_name", ""),
            "role_type": "protagonist"
        })

    # 添加女主
    for heroine in cast_arc.get("heroines", []):
        character_list.append({
            "character_id": heroine.get("character_id", ""),
            "character_name": heroine.get("character_name", ""),
            "role_type": "heroine"
        })

    # 添加配角
    for supporting in cast_arc.get("supporting_cast", []):
        character_list.append({
            "character_id": supporting.get("character_id", ""),
            "character_name": supporting.get("character_name", ""),
            "role_type": "supporting"
        })

    # 添加反派
    for antagonist in cast_arc.get("antagonists", []):
        character_list.append({
            "character_id": antagonist.get("character_id", ""),
            "character_name": antagonist.get("character_name", ""),
            "role_type": "antagonist"
        })

    return json.dumps(character_list, ensure_ascii=False, indent=2)


from pydantic import BaseModel, Field
from utils.config import config
from utils.logger import log
from utils.json_utils import safe_parse_json


class MajorConflict(BaseModel):
    """大冲突"""
    conflict_id: str = Field(..., description="冲突ID")
    name: str = Field(..., description="冲突名称")
    position_chapter: str = Field(..., description="发生章节范围（如 '5-8'）")
    description: str = Field(..., description="冲突描述")


class RouteStrategy(BaseModel):
    """路线战略意见"""
    strategy_id: str = Field(..., description="战略ID")
    source_outline: str = Field(..., description="来源大纲ID")
    strategy_text: str = Field(..., description="战略意见文本")
    recommended_chapters: int = Field(default=27, description="推荐章节数")
    heroine_count: int = Field(default=3, description="女主数量")
    main_plot_summary: str = Field(default="", description="主线一句话概要")
    major_conflicts: List[Dict[str, Any]] = Field(default_factory=list, description="大冲突列表")
    chapters: List[Dict[str, Any]] = Field(default_factory=list, description="章节规划数组")


class RouteStrategyAgent(BaseAgent):
    """
    路线战略规划Agent

    提供整体路线架构的战略意见，不涉及具体章节设计
    """
    name = "RouteStrategyAgent"
    system_prompt = ROUTE_STRATEGY_SYSTEM_PROMPT
    human_prompt_template = ROUTE_STRATEGY_HUMAN_PROMPT
    required_fields = ["strategy_text"]
    output_model = None  # 自然语言输出，不需要结构化模型

    def process(
        self,
        story_outline_data: Dict[str, Any],
        world_setting_data: Dict[str, Any] = None,
        user_idea: str = ""
    ) -> RouteStrategy:
        """处理路线战略规划

        Args:
            story_outline_data: 故事大纲数据（从story_outline.json加载）
            world_setting_data: 世界观设定数据（从world_setting.json加载，可选）
            user_idea: 用户创意
        """
        if not story_outline_data:
            raise ValueError("story_outline_data不能为空")

        steps = story_outline_data.get("steps", {})
        if not steps:
            raise ValueError("story_outline_data中缺少steps数据")

        if not user_idea:
            user_idea = story_outline_data.get("input", {}).get("user_idea", "")

        log.info("规划路线战略...")

        # 只加载需要的部分：premise、cast_arc、conflict_engine.map
        relevant_data = {
            "premise": steps.get("premise", {}),
            "cast_arc": steps.get("cast_arc", {}),
            "conflict_map": steps.get("conflict_engine", {}).get("map", {})
        }
        steps_json = json.dumps(relevant_data, ensure_ascii=False, separators=(',', ':'))

        # 从world_setting_data中提取locations和scene_presets
        locations = []
        scene_presets = []

        if world_setting_data:
            # 从world_setting中提取locations
            key_elements = world_setting_data.get("key_elements", {})
            if isinstance(key_elements, str):
                # 如果是字符串，尝试解析
                # 这里简化处理，直接跳过
                pass
            else:
                locations = key_elements.get("locations", [])

            # 从world_setting中提取scene_presets
            atmosphere = world_setting_data.get("atmosphere", {})
            if isinstance(atmosphere, str):
                pass
            else:
                scene_presets = atmosphere.get("scene_presets", [])

        # 从story_outline中提取character_list
        cast_arc = steps.get("cast_arc", {})
        character_list = _format_character_list(cast_arc)

        # 格式化locations和scene_presets
        locations_json = _format_locations(locations)
        scene_presets_json = _format_scene_presets(scene_presets)

        try:
            # 调用LLM获取响应
            strategy_text = self._run_raw(
                user_idea=user_idea,
                steps_data=steps_json,
                locations=locations_json,
                scene_presets=scene_presets_json,
                character_list=character_list
            )

            # 解析响应中的JSON部分
            json_data = self._extract_json_from_response(strategy_text)
            recommended_chapters = json_data.get("recommended_chapters", 27)
            heroine_count = json_data.get("heroine_count", 3)
            main_plot_summary = json_data.get("main_plot_summary", "")
            major_conflicts = json_data.get("major_conflicts", [])
            chapters = json_data.get("chapters", [])

            strategy_id = f"route_strategy_{uuid.uuid4().hex[:8]}"
            source_outline = steps.get("conflict_engine", {}).get("map", {}).get("conflict_map_id", "")

            strategy = RouteStrategy(
                strategy_id=strategy_id,
                source_outline=source_outline,
                strategy_text=strategy_text,
                recommended_chapters=recommended_chapters,
                heroine_count=heroine_count,
                main_plot_summary=main_plot_summary,
                major_conflicts=major_conflicts,
                chapters=chapters
            )

            self._log_success(strategy)
            return strategy

        except Exception as e:
            log.error(f"RouteStrategyAgent 失败: {e}")
            raise RuntimeError(f"路线战略规划失败: {e}") from e

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """从响应中提取JSON数据"""
        # 方法1: 找到第一个 { 和最后一个 }，作为完整的JSON
        start_idx = response.find('{')
        if start_idx == -1:
            return self._get_default_json()

        # 从起始位置开始，找到匹配的结束 }
        brace_count = 0
        in_string = False
        escape_next = False
        end_idx = -1

        for i in range(start_idx, len(response)):
            char = response[i]

            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break

        if end_idx == -1:
            return self._get_default_json()

        json_str = response[start_idx:end_idx]
        try:
            parsed = safe_parse_json(json_str)
            log.info(f"成功提取JSON，包含字段: {list(parsed.keys())}")
            return parsed
        except Exception as e:
            log.warning(f"JSON解析失败: {e}，尝试使用默认值")

        return self._get_default_json()

    def _get_default_json(self) -> Dict[str, Any]:
        """返回默认JSON值"""
        return {
            "recommended_chapters": 27,
            "heroine_count": 3,
            "main_plot_summary": "",
            "major_conflicts": [],
            "chapters": []
        }

    def _run_raw(self, **kwargs) -> str:
        """直接运行LLM获取文本输出（非JSON格式）"""
        # 创建一个不带JSON格式要求的LLM
        text_llm = ChatOpenAI(
            model=config.LLM_MODEL,
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.LLM_MAX_TOKENS,
            timeout=config.LLM_TIMEOUT,
        )

        human_prompt = self.human_prompt_template.format(**kwargs)
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=human_prompt)
        ]

        response = text_llm.invoke(messages)
        return response.content

    def _log_success(self, strategy: RouteStrategy) -> None:
        """记录成功日志"""
        log.info("路线战略生成成功:")
        log.info(f"  战略ID: {strategy.strategy_id}")
        log.info(f"  来源大纲: {strategy.source_outline}")
        log.info(f"  推荐章节数: {strategy.recommended_chapters}")
        log.info(f"  女主数量: {strategy.heroine_count}")
        log.info(f"  主线概要: {strategy.main_plot_summary}")
        log.info(f"  章节数: {len(strategy.chapters)}")