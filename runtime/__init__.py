"""
Runtime模块初始化

提供实时运行时的核心组件：
- CharacterManager: 角色管理器
- TimelineManager: 时间线管理器
- RuntimeStateManager: 运行时状态管理器（待实现）
"""
from .character_manager import CharacterManager
from .timeline_manager import TimelineManager

__all__ = [
    "CharacterManager",
    "TimelineManager",
]
