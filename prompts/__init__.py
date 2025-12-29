"""
Prompt模板初始化
"""
from .story_intake_prompt import STORY_INTAKE_PROMPT
from .worldbuilding_prompt import WORLDBUILDING_PROMPT
from .cast_design_prompt import CAST_DESIGN_PROMPT
from .macro_plot_prompt import MACRO_PLOT_PROMPT
from .route_design_prompt import ROUTE_DESIGN_PROMPT
from .conflict_emotion_prompt import CONFLICT_EMOTION_PROMPT
from .consistency_prompt import CONSISTENCY_PROMPT
from .narrator_prompt import NARRATOR_PROMPT

__all__ = [
    "STORY_INTAKE_PROMPT",
    "WORLDBUILDING_PROMPT",
    "CAST_DESIGN_PROMPT",
    "MACRO_PLOT_PROMPT",
    "ROUTE_DESIGN_PROMPT",
    "CONFLICT_EMOTION_PROMPT",
    "CONSISTENCY_PROMPT",
    "NARRATOR_PROMPT",
]
