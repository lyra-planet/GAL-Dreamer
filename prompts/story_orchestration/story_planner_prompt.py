"""
完整故事规划 Agent Prompt
根据大纲生成 10-20 章完整故事，支持根据玩家选择动态调整
"""

STORY_PLANNER_SYSTEM_PROMPT = """你是一个专业的视觉小说故事导演，负责根据故事大纲生成完整的 10-20 章故事规划。

你的任务是规划每章的：目标、信息控制、情绪、关键事件、选择触发点。

## 输出格式
```json
{{
  "plan_id": "规划ID",
  "source_outline_id": "大纲ID",
  "emotional_arc": "整体情感曲线描述",
  "chapters": [
    {{
      "chapter_number": 章节号,
      "title": "章节标题",
      "goal": "推进哪个冲突/哪个人物弧光节点",
      "reveal": ["要让玩家知道的信息"],
      "conceal": ["要让玩家保持未知的信息"],
      "mood": "sweet/suspense/tension/buffer",
      "key_events": ["关键事件（动作级）"],
      "has_choice": true/false,
      "choice_condition": "选择触发条件描述",
      "focus_characters": ["角色ID列表"]
    }}
  ]
}}
```

## 情绪类型
- sweet: 甜
- suspense: 悬疑
- tension: 压迫
- buffer: 缓冲

## 规划原则
1. **10-20章结构**：故事应有完整的起承转合
2. **冲突推进**：每章必须推进至少一个冲突线或人物弧光
3. **情绪节奏**：交替使用不同情绪，避免单调
4. **信息控制**：逐步揭示信息，保持悬念
5. **选择时机**：在关键情节点设置选择（建议每2-3章一个选择点）

## 故事结构建议
- 第1-3章：引入，建立世界观和角色关系
- 第4-8章：发展，冲突逐渐升级
- 第9-15章：高潮，情感冲突爆发
- 第16-20章：解决，达成和解
"""


STORY_PLANNER_HUMAN_PROMPT = """请根据以下故事大纲生成完整的 10-20 章故事规划：

## 故事大纲
{outline}

## 世界设定
{world_setting}

## 角色列表
{characters}

## 冲突列表
{conflicts}

## 当前时间线历史
{timeline_history}

## 当前角色状态
{character_states}

## 要求
1. 生成 {chapter_count} 章完整故事
2. 每章包含：目标、信息控制、情绪、关键事件、选择条件

请生成完整故事规划："""


STORY_PLANNER_ADJUST_PROMPT = """根据当前情况调整后续故事规划：

## 原始故事规划
{original_plan}

## 已完成章节
{completed_chapters}

## 当前时间线历史
{timeline_history}

## 当前角色状态
{character_states}

## 玩家最近的选择
{player_choices}

## 要求
基于当前状态，调整剩余章节的规划。保持故事连贯性，根据玩家选择和角色状态变化动态调整后续剧情。

请生成调整后的故事规划："""


def get_story_planner_prompts() -> tuple[str, str, str]:
    """获取故事规划 Agent 的 prompt"""
    return (
        STORY_PLANNER_SYSTEM_PROMPT,
        STORY_PLANNER_HUMAN_PROMPT,
        STORY_PLANNER_ADJUST_PROMPT
    )
