"""
Agents模块初始化

提供:
- StoryIntakeAgent: 故事理解Agent
- WorldbuildingAgent: 世界观构建Agent
- KeyElementAgent: 关键元素Agent
- TimelineAgent: 时间线/历史Agent
- AtmosphereAgent: 氛围/基调Agent
- NpcFactionAgent: NPC势力Agent
- WorldConsistencyAgent: 一致性检查Agent
- WorldFixerAgent: 世界观修复Agent
- WorldSummaryAgent: 世界观摘要Agent
- BaseAgent: Agent基类(用于自定义Agent)
"""
from .base_agent import BaseAgent, AgentConfig
from .story_intake_agent import StoryIntakeAgent
from .worldbuilding_agent import WorldbuildingAgent
from .key_element_agent import KeyElementAgent
from .timeline_agent import TimelineAgent
from .atmosphere_agent import AtmosphereAgent
from .npc_faction_agent import NpcFactionAgent
from .world_consistency_agent import WorldConsistencyAgent
from .world_fixer_agent import WorldFixerAgent
from .world_summary_agent import WorldSummaryAgent

__all__ = [
    "BaseAgent",
    "AgentConfig",
    "StoryIntakeAgent",
    "WorldbuildingAgent",
    "KeyElementAgent",
    "TimelineAgent",
    "AtmosphereAgent",
    "NpcFactionAgent",
    "WorldConsistencyAgent",
    "WorldFixerAgent",
    "WorldSummaryAgent",
]
