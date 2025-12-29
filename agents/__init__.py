"""
Agents模块初始化

提供子模块:
- worldbuilding: 世界观构建相关Agents
- BaseAgent: Agent基类(用于自定义Agent)
"""
from .base_agent import BaseAgent, AgentConfig

__all__ = [
    "BaseAgent",
    "AgentConfig",
]
