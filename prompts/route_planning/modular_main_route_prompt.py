"""
Modular Main Route Agent Prompt
模块化主线框架规划 Prompt - 按起承转合四模块生成主线章节
完全参考 main_route_prompt 的要求
"""

MODULAR_MAIN_ROUTE_SYSTEM_PROMPT = """你是一位专业的GALGAME游戏策划，擅长根据战略规划生成详细的章节框架。

**你的职责：根据模块策略，生成单个模块的详细章节框架**

你需要严格按照模块策略中的要求生成每个章节的内容。

**重要：必须输出JSON格式，不要输出任何其他文字。**
"""

MODULAR_MAIN_ROUTE_HUMAN_PROMPT = """【用户创意】
{user_idea}

【故事数据】
{story_data}

【整体路线战略意见】
{route_strategy_text}

【主线概要】
{main_plot_summary}

【详细章节规划】
{chapters}

【模块信息】
模块名称: {module_name}
模块类型: {module_type}
章节范围: 第{chapter_start}章 - 第{chapter_end}章（共{chapter_count}章）

【本模块章节ID列表】
重要：本模块的章节ID必须是 common_ch{chapter_start} 到 common_ch{chapter_end}
例如：本模块是第7-14章，章节ID就是 common_ch7, common_ch8, ..., common_ch14

{previous_context}

【模块策略】
{module_strategy}

【已有状态框架】（如果不是第一个模块，请继承这些状态）
{state_framework}

【已有分支框架】（全局分支列表，保持一致性）
{global_branches}

【已有结局框架】（全局结局列表，保持一致性）
{global_endings}

请根据【详细章节规划】、【模块策略】和【故事大纲数据】生成该模块的章节框架。

**必须输出以下JSON格式：**
{{
    "module_name": "{module_name}",
    "module_type": "{module_type}",
    "chapter_range": {{"start": {chapter_start}, "end": {chapter_end}}},
    "chapters": [
        {{
            "id": "common_ch{chapter_start}",
            "summary": "章节概要，必须基于故事大纲",
            "scene": "关键场景描述",
            "choices": [
                {{
                    "id": "c{chapter_start}_1",
                    "text": "具体的行动描述",
                    "target": "heroine_001",
                    "branch": null,
                    "visible": null,
                    "effect": {{"heroine_001": 15}}
                }}
            ]
        }}
    ],
    "branches": [
        {{
            "id": "branch_heroine_001_1",
            "target": "heroine_001",
            "desc": "分支剧情概要",
            "chapters": 6,
            "return": "common_ch6",
            "reward": {{"heroine_001": 30}}
        }}
    ],
    "endings": [],
    "state_transitions": {{
        "heroine_001": {{"min_in": 0, "max_out": 20}}
    }}
}}

**生成要求：**

1. **剧情必须基于故事大纲**：
   - 章节概要必须与【故事大纲数据】中的 premise（前提）、cast_arc（角色弧光）、conflict_map（冲突地图）一致
   - 角色行为要符合其设定
   - 主线冲突要与故事大纲中的核心冲突相关

2. **严格按照模块策略生成**：
   - **分支数量必须严格遵循策略中的 branch_count**
   - 主线章节、分支内容、结局设计必须与【模块策略】中的描述一致
   - 选择点数量参考策略中的 key_choices 说明

3. **[最高要求]选择点密度控制**：
   - 不是每章都需要选择点
   - 一般每1-2章设置1个选择点
   - 6章模块约3-4个选择点
   - 8章模块约4-5个选择点
   - 5章模块约2-3个选择点（最后一章集中多个结局选项）

4. **每个选择必须有实际作用**：
   - 要么跳转到某个分支（branch_id不为null）
   - 要么显著影响好感度（effect不为空）
   - 绝对不允许没有任何作用的选择

5. **分支设计（关键！）**：
   - 严格按照策略中的 branch_count 生成分支
   - 每个分支3-8章长度
   - **分支类型要多样化**：
     * 早期分支：故事初期，建立关系的剧情
     * 中期危机：角色遭遇挫折，需要主角帮助
     * 秘密事件：发现角色不为人知的一面
     * 特殊事件：节日、突发事件等
   - **desc必须写剧情概要**：描述这个分支发生了什么故事

6. **分支跨度限制（关键！）**：
   - **分支回归点必须在本模块的章节范围内**
   - 例如：本模块是第7-14章，分支从第8章进入，回归点只能是 common_ch8, common_ch9, common_ch10, common_ch11 之一
   - 绝对不能回归到其他模块的章节
   - return 的章节ID必须在 common_ch{chapter_start} 到 common_ch{chapter_end} 之间

7. **数值平衡**：
   - 好感度初始值为0，范围0-100
   - 单次选择好感度变化：+10到+20（正向），-10到-20（负向）
   - 完成分支好感度奖励：+25到+40
   - 选项可见性门槛按模块设置：
     * 起（第1-6章）：不设置门槛（null）
     * 承（第7-14章）：5-20
     * 转（第15-22章）：25-50
     * 合（第23-27章）：55-70（好结局），30-40（普通结局）

8. **结局设计（仅合模块）**：
   - 每个女主应该有好结局、普通结局
   - 主线最后一章必须包含所有好结局和普通结局选项
   - 每个结局分支只能有一个入口

9. **choice_text必须保持沉浸感**：
   - 描述主角的具体行动、台词、心理活动
   - 例如："握住她颤抖的手，注视她的眼睛"
   - 绝对禁止：写"走向XX"、"选择XX好结局"这种破坏沉浸感的文字

{feedback_section}

**只输出JSON，不要添加任何markdown代码块标记或解释文字。**
"""

MODULAR_MAIN_ROUTE_PROMPT = MODULAR_MAIN_ROUTE_SYSTEM_PROMPT + "\n\n" + MODULAR_MAIN_ROUTE_HUMAN_PROMPT
