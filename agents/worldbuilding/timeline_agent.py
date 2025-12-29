"""
Timeline Agent
时间线/历史Agent - 构建世界历史时间线
"""
from typing import Dict, Any, List, Optional, Union
import uuid

from agents.base_agent import BaseAgent
from prompts.worldbuilding.timeline_prompt import (
    TIMELINE_SYSTEM_PROMPT,
    TIMELINE_HUMAN_PROMPT
)
from models.worldbuilding.timeline import WorldTimeline
from utils.logger import log


class TimelineAgent(BaseAgent):
    """
    时间线Agent

    功能:
    - 构建世界历史时间线
    - 定义过去的重要事件
    - 建立事件间的因果关系
    """

    # 类属性配置
    name = "TimelineAgent"
    system_prompt = TIMELINE_SYSTEM_PROMPT
    human_prompt_template = TIMELINE_HUMAN_PROMPT
    required_fields = ["current_year", "era_summary", "events"]
    output_model = WorldTimeline

    # 重要程度级别
    IMPORTANCE_LEVELS = ["background", "minor", "major", "critical"]

    def process(
        self,
        story_constraints: Dict[str, Any],
        world_setting: Dict[str, Any],
        key_elements: Dict[str, Any],
        user_idea: str = "",
        validate: bool = True
    ) -> WorldTimeline:
        """
        处理时间线生成

        Args:
            story_constraints: 故事约束条件
            world_setting: 世界观设定
            key_elements: 关键元素
            user_idea: 用户原始创意
            validate: 是否验证输出

        Returns:
            WorldTimeline: 世界时间线
        """
        if not world_setting:
            raise ValueError("world_setting不能为空")

        log.info("生成时间线...")

        try:
            # 提取关键元素信息
            key_items = [item.get("name", "") for item in key_elements.get("items", [])]
            key_locations = [loc.get("name", "") for loc in key_elements.get("locations", [])]
            orgs = [org.get("name", "") for org in key_elements.get("organizations", [])]

            result = self.run(
                genre=story_constraints.get("genre", ""),
                themes=", ".join(story_constraints.get("themes", [])),
                tone=story_constraints.get("tone", ""),
                era=world_setting.get("era", ""),
                location=world_setting.get("location", ""),
                world_type=world_setting.get("type", ""),
                core_conflict=world_setting.get("core_conflict_source", ""),
                world_description=world_setting.get("description", ""),
                key_items=", ".join(key_items) if key_items else "无",
                key_locations=", ".join(key_locations) if key_locations else "无",
                organizations=", ".join(orgs) if orgs else "无",
                user_idea=user_idea
            )

            if "timeline_id" not in result:
                result["timeline_id"] = f"timeline_{uuid.uuid4().hex[:8]}"

            timeline = WorldTimeline(**result)
            self._log_success(timeline)
            return timeline

        except Exception as e:
            log.error(f"TimelineAgent 处理失败: {e}")
            raise RuntimeError(f"时间线生成失败: {e}") from e

    def _log_success(self, timeline: WorldTimeline) -> None:
        """记录成功日志"""
        log.info("时间线生成成功:")
        log.info(f"  当前时间: {timeline.current_year}")
        log.info(f"  事件数量: {len(timeline.events)}")
        critical_events = timeline.get_critical_events()
        if critical_events:
            log.info(f"  关键事件: {', '.join([e.name for e in critical_events])}")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """验证输出"""
        # 检查current_year
        if not output.get("current_year"):
            return "current_year不能为空"

        # 检查era_summary
        if not output.get("era_summary"):
            return "era_summary不能为空"

        # 检查events
        events = output.get("events")
        if not isinstance(events, list):
            return "events必须是数组类型"
        if len(events) == 0:
            return "events不能为空"

        for i, event in enumerate(events):
            if not isinstance(event, dict):
                return f"events[{i}]必须是对象"

            required_fields = ["event_id", "name", "time_period", "description", "importance"]
            for field in required_fields:
                if not event.get(field):
                    return f"events[{i}]缺少{field}"

            importance = event.get("importance")
            if importance not in self.IMPORTANCE_LEVELS:
                return f"events[{i}]的importance必须是: {', '.join(self.IMPORTANCE_LEVELS)}"

            related = event.get("related_events")
            if related is not None and not isinstance(related, list):
                return f"events[{i}]的related_events必须是数组类型"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        return {
            "timeline_id": f"timeline_fallback_{uuid.uuid4().hex[:8]}",
            "current_year": "故事开始时",
            "era_summary": "普通的时代",
            "events": [
                {
                    "event_id": "event_default_1",
                    "name": "起始事件",
                    "time_period": "故事开始前",
                    "description": "故事的起始",
                    "cause": "",
                    "effect": "",
                    "importance": "background",
                    "related_events": []
                }
            ],
            "fallback": True
        }
