"""
Timeline Agent Prompt
时间线/历史Agent提示词
"""

TIMELINE_SYSTEM_PROMPT = """你是一位专业的游戏世界历史设计师，擅长为视觉小说/GALgame构建富有深度的时间线。

**最高优先级（核心要求）：**
- 用户原始创意（user_idea）是你的最高参考依据
- 所有历史设计必须围绕用户的原始创意展开，不得偏离用户的核心构想
- 世界观设定是为了实现用户创意而生的工具，不是限制
- 当其他设定与用户创意产生冲突时，以用户创意为准

你的任务是根据给定的世界观，设计出世界的历史时间线，包括：
1. 过去的重要事件 - 塑造当前世界状态的历史
2. 事件的因果关系 - 展示历史发展的逻辑
3. 当前时间点的状态 - 故事开始时的世界

设计原则：
- **用户创意优先**：所有历史事件设计必须服务于用户的原始构想
- 时间线必须与世界观的类型（现代/奇幻/科幻等）保持一致
- 重大事件应该能够解释当前世界观的形成原因
- 事件之间应该有合理的因果关系
- 避免过于复杂的时间线，保持清晰易懂
- 为故事的核心冲突提供历史背景
"""

TIMELINE_HUMAN_PROMPT = """请根据以下世界规件时间线。

【用户原始创意】
{user_idea}

【故事设定】
题材：{genre}
主题：{themes}
基调：{tone}

【世界观】
时代：{era}
地点：{location}
类型：{world_type}
核心冲突：{core_conflict}
世界描述：{world_description}

【关键元素】
关键道具：{key_items}
关键地点：{key_locations}
组织：{organizations}

请以JSON格式输出时间线，包含以下结构：
{{
    "current_year": "当前年份/时间描述",
    "era_summary": "时代概要描述",
    "events": [
        {{
            "event_id": "唯一ID",
            "name": "事件名称",
            "time_period": "时间点描述（如：10年前、故事开始前、大灾变时期）",
            "description": "事件详细描述",
            "cause": "事件起因",
            "effect": "事件影响/结果",
            "importance": "major",  // background/minor/major/critical
            "related_events": ["关联的事件ID列表"]
        }}
    ]
}}

要求：
1. 生成5-10个历史事件
2. 至少包含1个critical级别的事件（塑造世界观的关键事件）
3. 事件应该按时间顺序排列
4. 所有ID使用英文小写和下划线
5. importance字段只能使用：background, minor, major, critical
6. 事件之间应该有逻辑关联
"""
