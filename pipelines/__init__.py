"""
Pipelines模块初始化

提供子模块:
- worldbuilding: 世界观构建相关Pipelines
- MainPipeline: 主入口Pipeline
"""
from .main_pipeline import MainPipeline

__all__ = [
    "MainPipeline",
]
