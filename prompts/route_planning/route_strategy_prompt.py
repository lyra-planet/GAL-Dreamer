"""
Route Strategy Agent Prompt
故事大纲生成 Agent - 生成共通线章节详细规划
"""

ROUTE_STRATEGY_SYSTEM_PROMPT = """你是一位视觉小说游戏策划，擅长设计游戏主线剧情。

你的任务是根据用户提供的故事创意，给出**详细的共通线章节规划**。

**GAL游戏章节规划要素：**

1. **场景 (location)**：从【可用场景列表】中选择
   - 必须使用 world_setting 中定义的场景
   - 考虑场景的氛围描述和剧情作用

2. **时间段 (time_of_day)**：故事发生的时间
   - 早晨、午休、放学后、夜晚、深夜
   - 周末、节假日
   - 需要与场景合理搭配

3. **出场人物 (characters)**：从【角色列表】中选择
   - 必须从 story_outline 的 cast_arc 中选择
   - 每章建议2-4名角色，避免过多

4. **剧情目标 (goal)**：推进哪个冲突/哪个人物弧光节点
   - 参考 conflict_engine 中的冲突设定

5. **信息控制 (information)**：要让玩家知道/不知道什么

6. **情绪基调 (mood)**：参考场景预设中的 mood

7. **关键事件 (event)**：发生了什么（动作级描述）

**输出格式要求：**
只输出一个JSON对象，所有内容都必须在JSON内，使用结构化数组表示章节。
"""

ROUTE_STRATEGY_HUMAN_PROMPT = """【用户创意】
{user_idea}

【故事数据】
{steps_data}

【可用场景列表】
{locations}

【场景预设详情】
{scene_presets}

【角色列表】
{character_list}

请给出详细的共通线章节规划。

**只输出以下JSON格式，不要输出任何其他文字：**

{{
    "recommended_chapters": 推荐章节数(整数15-20),
    "heroine_count": 女主人数(整数),
    "main_plot_summary": "主要剧情概要（一句话）",
    "major_conflicts": [
        {{
            "conflict_id": "conflict_1",
            "name": "第一次大冲突名称",
            "position_chapter": 5-8,
            "description": "冲突描述"
        }},
        {{
            "conflict_id": "conflict_2",
            "name": "第二次大冲突名称",
            "position_chapter": 12-15,
            "description": "冲突描述"
        }},
        {{
            "conflict_id": "conflict_3",
            "name": "第三次大冲突名称（可选）",
            "position_chapter": 18-20,
            "description": "冲突描述"
        }}
    ],
    "chapters": [
        {{
            "chapter": 1,
            "id": "common_ch1",
            "title": "章节标题（可选，简短描述）",
            "story_phase": "起",  // 故事阶段：起/承/转/合
            "location": "从【可用场景列表】中选择",
            "time_of_day": "时间段：早晨/午休/放学后/夜晚/深夜/周末",
            "characters": ["从【角色列表】中选择角色ID"],
            "goal": "本段目标：推进哪个冲突/哪个人物弧光节点",
            "information": "本段信息：要让玩家知道/不知道什么",
            "mood": "情绪：甜/悬疑/压迫/缓冲",
            "event": "关键事件：发生了什么（动作级描述）",
            "major_conflict": null  // 如果本章是大冲突章节，填写conflict_id，否则null
        }},
        {{
            "chapter": 2,
            "id": "common_ch2",
            "title": "章节标题",
            "story_phase": "起",
            "location": "场景...",
            "time_of_day": "时间段...",
            "characters": ["角色ID列表"],
            "goal": "本段目标...",
            "information": "本段信息...",
            "mood": "情绪...",
            "event": "关键事件...",
            "major_conflict": null
        }},
        ...
    ]
}}

**重要说明：**

1. **故事结构：起承转合（灵活分配）**
   - **起**：引入阶段，介绍世界观和角色（约占前20-25%）
   - **承**：发展深入，角色关系深化（约占30-35%）
   - **转**：转折冲突，矛盾激化（约占25-30%）
   - **合**：解决收尾，选择与结局（约占15-20%）
   - 根据实际章节数灵活调整各阶段篇幅

2. **前2-3章必须介绍所有主角和女主**
   - 第1章：介绍主角和第一位女主
   - 第2章：介绍剩余女主
   - 第3章：确认所有女主已登场，建立初步印象
   - 确保玩家在开篇就能认识所有可攻略角色

3. **必须有2-3次大冲突**
   - 第一次大冲突：承阶段中前期（约故事进展30%处）
   - 第二次大冲突：转阶段（约故事进展60%处）
   - 第三次大冲突（可选）：高潮前奏（约故事进展80%处）
   - 大冲突章节的 major_conflict 字段必须填写对应的 conflict_id

4. chapters 是一个数组，每个元素代表一章的结构化数据
5. 每章必须包含：chapter, id, title, story_phase, location, time_of_day, characters, goal, information, mood, event, major_conflict
6. location 必须从【可用场景列表】中精确选择，不能创造新场景
7. characters 必须从【角色列表】中选择，使用 character_id（如 heroine_001, protagonist_main）
8. location 和 time_of_day 需要合理搭配（如夜晚在教室较少，周末在学校场景较少）
9. 只规划共通线，不需要规划角色个人线或真线
10. 只输出JSON，不要输出markdown代码块标记或其他解释文字

请开始输出JSON。
"""

ROUTE_STRATEGY_PROMPT = ROUTE_STRATEGY_SYSTEM_PROMPT + "\n\n" + ROUTE_STRATEGY_HUMAN_PROMPT
