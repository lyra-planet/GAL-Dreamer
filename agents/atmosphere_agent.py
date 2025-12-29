"""
Atmosphere Agent
氛围/基调Agent - 定义世界的整体氛围和基调
"""
from typing import Dict, Any, List, Optional, Union
import uuid

from .base_agent import BaseAgent
from prompts.atmosphere_prompt import (
    ATMOSPHERE_SYSTEM_PROMPT,
    ATMOSPHERE_HUMAN_PROMPT
)
from models.atmosphere import WorldAtmosphere
from utils.logger import log


class AtmosphereAgent(BaseAgent):
    """
    氛围Agent

    功能:
    - 定义整体情绪基调
    - 设计视觉风格
    - 设定色彩方案
    - 生成场景氛围预设
    - 提供音效/音乐指导
    """

    # 类属性配置
    name = "AtmosphereAgent"
    system_prompt = ATMOSPHERE_SYSTEM_PROMPT
    human_prompt_template = ATMOSPHERE_HUMAN_PROMPT
    required_fields = ["overall_mood", "visual_style", "color_scheme"]
    output_model = WorldAtmosphere

    def process(
        self,
        story_constraints: Dict[str, Any],
        world_setting: Dict[str, Any],
        key_elements: Dict[str, Any],
        timeline: Dict[str, Any],
        user_idea: str = "",
        validate: bool = True
    ) -> WorldAtmosphere:
        """
        处理氛围生成

        Args:
            story_constraints: 故事约束条件
            world_setting: 世界观设定
            key_elements: 关键元素
            timeline: 时间线(必选)
            user_idea: 用户原始创意
            validate: 是否验证输出

        Returns:
            WorldAtmosphere: 世界氛围设定
        """
        if not world_setting:
            raise ValueError("world_setting不能为空")
        if not timeline:
            raise ValueError("timeline不能为空")

        log.info("生成氛围设定...")

        try:
            # 提取关键场景信息
            locations = key_elements.get("locations", [])
            locations_desc = "\n".join([
                f"- {loc.get('name', '')}: {loc.get('description', '')}"
                for loc in locations[:5]
            ]) if locations else "无"

            # 提取时间线信息
            events = timeline.get("events", [])
            critical_events = [e for e in events if e.get("importance") == "critical"]
            if critical_events:
                timeline_summary = "关键历史事件: " + ", ".join([
                    e.get("name", "") for e in critical_events[:3]
                ])
            else:
                timeline_summary = "历史背景: " + timeline.get("era_summary", "无特殊历史")

            result = self.run(
                genre=story_constraints.get("genre", ""),
                themes=", ".join(story_constraints.get("themes", [])),
                tone=story_constraints.get("tone", ""),
                era=world_setting.get("era", ""),
                location=world_setting.get("location", ""),
                world_type=world_setting.get("type", ""),
                world_description=world_setting.get("description", ""),
                key_locations_desc=locations_desc,
                timeline_summary=timeline_summary,
                user_idea=user_idea
            )

            if "atmosphere_id" not in result:
                result["atmosphere_id"] = f"atmosphere_{uuid.uuid4().hex[:8]}"

            atmosphere = WorldAtmosphere(**result)
            self._log_success(atmosphere)
            return atmosphere

        except Exception as e:
            log.error(f"AtmosphereAgent 处理失败: {e}")
            raise RuntimeError(f"氛围生成失败: {e}") from e

    def _log_success(self, atmosphere: WorldAtmosphere) -> None:
        """记录成功日志"""
        log.info("氛围设定生成成功:")
        log.info(f"  整体基调: {atmosphere.overall_mood}")
        log.info(f"  视觉风格: {atmosphere.visual_style}")
        log.info(f"  场景预设: {len(atmosphere.scene_presets)}个")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """验证输出"""
        # 检查overall_mood
        if not output.get("overall_mood"):
            return "overall_mood不能为空"

        # 检查visual_style
        if not output.get("visual_style"):
            return "visual_style不能为空"

        # 检查color_scheme
        color_scheme = output.get("color_scheme")
        if not isinstance(color_scheme, dict):
            return "color_scheme必须是对象类型"

        # 检查scene_presets
        presets = output.get("scene_presets")
        if presets is not None:
            if not isinstance(presets, list):
                return "scene_presets必须是数组类型"
            for i, preset in enumerate(presets):
                if not isinstance(preset, dict):
                    return f"scene_presets[{i}]必须是对象"
                if not preset.get("scene_type"):
                    return f"scene_presets[{i}]缺少scene_type"
                if not preset.get("visual_style"):
                    return f"scene_presets[{i}]缺少visual_style"
                if not preset.get("mood"):
                    return f"scene_presets[{i}]缺少mood"

                palette = preset.get("color_palette")
                if palette is not None and not isinstance(palette, list):
                    return f"scene_presets[{i}]的color_palette必须是数组类型"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        return {
            "atmosphere_id": f"atmosphere_fallback_{uuid.uuid4().hex[:8]}",
            "overall_mood": "平静",
            "visual_style": "简约",
            "color_scheme": {
                "primary": "白色",
                "secondary": "灰色",
                "accent": "蓝色",
                "background": "浅灰色"
            },
            "scene_presets": [
                {
                    "scene_type": "通用",
                    "visual_style": "简约",
                    "mood": "平静",
                    "color_palette": ["白色", "灰色"],
                    "sound_hint": ""
                }
            ],
            "audio_guidelines": "",
            "fallback": True
        }
