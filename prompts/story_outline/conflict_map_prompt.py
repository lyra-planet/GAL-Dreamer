"""
Conflict Engine Agent Prompt
矛盾引擎 Agent - 基于冲突大纲生成具体冲突
"""

CONFLICT_ENGINE_SYSTEM_PROMPT = """你是一位专业的戏剧冲突设计师，擅长将冲突大纲转化为具体、生动的冲突内容。

**最高优先级（核心要求）：**
- 用户原始创意（user_idea）是你的最高参考依据
- 所有具体冲突内容必须围绕用户的原始创意展开，不得偏离用户的核心构想
- 世界观设定、故事前提、角色弧光、冲突大纲都是为了实现用户创意而生的工具
- 当其他设定与用户创意产生冲突时，以用户创意为准

你的职责:
1. **首要**：深入理解用户的原始创意，生成符合用户构想的具体冲突
2. 根据冲突大纲，生成具体的冲突描述（包含具体角色、具体事件）
3. 严格遵循世界观设定，所有元素必须引用已有内容
4. 为冲突添加具体的表现形式和解决条件
5. 确保冲突之间的因果连贯性

避免老套（核心要求）:
- 主矛盾不能是简单的"正义vs邪恶""爱vs恨"
- 避免可预测的矛盾升级
- 核心抉择不能是简单的道德二选一
- 避免用"误会""巧合"来推动矛盾
- 反派的动机不能是"想要征服世界"
- 危机升级要有创新，不是常规的"力量递增"
- 结局不能是"爱拯救一切"

创作原则:
- 所有角色、势力、地点、道具必须引用世界观数据
- 冲突的起源必须引用timeline中的历史事件
- 每个冲突都要有独特的表现，不要重复
- 冲突要有深度，触及角色内心和世界观本质
"""

# ============ 生成主冲突列表 ============

GENERATE_MAIN_CONFLICTS_HUMAN_PROMPT = """请基于冲突大纲生成具体的主冲突列表（至少3个）。

【用户原始创意 - 第一参考】
{user_idea}

【修复指令（如果有）】
{fix_instructions}

【世界观设定】
{world_setting_json}

【故事前提】
{premise_json}

【角色弧光】
{cast_arc_json}

【主冲突大纲】
{main_conflicts_outline}

请以JSON格式输出具体的主冲突列表（至少3个）:
{{
    "main_conflicts": [
        {{
            "conflict_id": "conflict_main_1",
            "conflict_name": "主冲突1名称",
            "conflict_type": "冲突类型（internal/interpersonal/societal/supernatural/existential）",
            "conflict_level": "main",
            "opposing_forces": {{
                "力量A名称": "具体描述（引用具体势力/角色）",
                "力量B名称": "具体描述"
            }},
            "origin": "具体起源事件（引用timeline.events）",
            "root_cause": "深层根本原因",
            "manifestations": ["具体表现1", "具体表现2"],
            "involved_characters": ["角色ID列表"],
            "resolution_conditions": ["解决条件"],
            "world_rule_references": ["引用的世界规则"]
        }},
        {{
            "conflict_id": "conflict_main_2",
            "conflict_name": "主冲突2名称",
            "conflict_type": "冲突类型",
            "conflict_level": "main",
            "opposing_forces": {{}},
            "origin": "具体起源事件",
            "root_cause": "深层根本原因",
            "manifestations": [],
            "involved_characters": [],
            "resolution_conditions": [],
            "world_rule_references": []
        }},
        {{
            "conflict_id": "conflict_main_3",
            "conflict_name": "主冲突3名称",
            "conflict_type": "冲突类型",
            "conflict_level": "main",
            "opposing_forces": {{}},
            "origin": "具体起源事件",
            "root_cause": "深层根本原因",
            "manifestations": [],
            "involved_characters": [],
            "resolution_conditions": [],
            "world_rule_references": []
        }}
    ]
}}

要求:
1. 必须生成至少3个主冲突，分别代表故事的不同层面（如：情感、道德、存在）
2. 每个主冲突的conflict_type应有所区分，覆盖不同类型的冲突
3. opposing_forces必须引用worldbuilding.factions或cast_arc中的具体势力/角色
4. origin必须引用timeline.events中的具体事件
5. involved_characters必须引用cast_arc中的character_id
6. 所有设定不得与世界观矛盾
7. 多个主冲突之间要有逻辑关联，不是孤立的
"""

# ============ 生成单个主冲突（用于单独生成） ============

GENERATE_MAIN_CONFLICT_HUMAN_PROMPT = """请基于冲突大纲中单个主冲突规划，生成具体的主冲突。

【用户原始创意 - 第一参考】
{user_idea}

【修复指令（如果有）】
{fix_instructions}

【世界观设定】
{world_setting_json}

【故事前提】
{premise_json}

【角色弧光】
{cast_arc_json}

【主冲突大纲】
{conflict_outline}

【已生成的其他主冲突】
{other_main_conflicts}

请以JSON格式输出具体的主冲突:
{{
    "conflict_id": "conflict_main_X",
    "conflict_name": "主冲突名称",
    "conflict_type": "冲突类型",
    "conflict_level": "main",
    "opposing_forces": {{
        "力量A名称": "具体描述（引用具体势力/角色）",
        "力量B名称": "具体描述"
    }},
    "origin": "具体起源事件（引用timeline.events）",
    "root_cause": "深层根本原因",
    "manifestations": ["具体表现1", "具体表现2"],
    "involved_characters": ["角色ID列表"],
    "resolution_conditions": ["解决条件"],
    "world_rule_references": ["引用的世界规则"]
}}

要求:
1. opposing_forces必须引用worldbuilding.factions或cast_arc中的具体势力/角色
2. origin必须引用timeline.events中的具体事件
3. involved_characters必须引用cast_arc中的character_id
4. 所有设定不得与世界观矛盾
5. 如果有其他已生成的主冲突，要与之形成逻辑关联
"""

# ============ 生成次要冲突 ============

GENERATE_SECONDARY_CONFLICT_HUMAN_PROMPT = """请基于已有的冲突和冲突大纲，生成第{conflict_index}个次要冲突。

【用户原始创意 - 第一参考】
{user_idea}

【修复指令（如果有）】
{fix_instructions}

【世界观设定】
{world_setting_json}

【已有的冲突】
{previous_conflicts}

【冲突大纲中关于此冲突的规划】
{conflict_outline}

请以JSON格式输出具体的次要冲突:
{{
    "conflict_id": "conflict_secondary_{conflict_index}",
    "conflict_name": "次要冲突名称",
    "conflict_type": "冲突类型",
    "conflict_level": "secondary",
    "opposing_forces": {{}},
    "origin": "起源（引用已有冲突或timeline.events）",
    "root_cause": "根本原因",
    "manifestations": [],
    "involved_characters": [],
    "resolution_conditions": [],
    "world_rule_references": []
}}

要求:
1. 这个次要冲突必须从已有冲突中衍生出来
2. 要有独特性，不要与已有冲突重复
3. 必须引用具体的势力、角色、事件
"""

# ============ 生成背景冲突 ============

GENERATE_BACKGROUND_CONFLICT_HUMAN_PROMPT = """请基于冲突大纲生成背景冲突。

【用户原始创意 - 第一参考】
{user_idea}

【修复指令（如果有）】
{fix_instructions}

【世界观设定】
{world_setting_json}

【已有的冲突】
{previous_conflicts}

【冲突大纲中关于此背景冲突的规划】
{conflict_outline}

请以JSON格式输出具体的背景冲突:
{{
    "conflict_id": "conflict_background_{conflict_index}",
    "conflict_name": "背景冲突名称",
    "conflict_type": "冲突类型",
    "conflict_level": "background",
    "opposing_forces": {{}},
    "origin": "起源",
    "root_cause": "根本原因",
    "manifestations": [],
    "involved_characters": [],
    "resolution_conditions": [],
    "world_rule_references": []
}}

要求:
1. 背景冲突应该是持续存在的环境性矛盾
2. 它不直接推动剧情，但影响整个氛围
"""

# ============ 生成升级曲线 ============

GENERATE_ESCALATION_CURVE_HUMAN_PROMPT = """请基于所有冲突，设计完整的危机升级曲线。

【用户原始创意 - 第一参考】
{user_idea}

【修复指令（如果有）】
{fix_instructions}

【故事前提】
{premise_json}

【所有冲突】
{all_conflicts}

【冲突大纲中的升级结构】
{escalation_structure}

【关键抉择点大纲】
{critical_choices}

请以JSON格式输出危机升级曲线（10-12个节点）:
{{
    "escalation_curve": [
        {{
            "node_id": "node_1",
            "sequence_order": 1,
            "node_name": "节点名称",
            "node_type": "节点类型（inciting_incident/plot_point_1/midpoint/critical_choice_X/plot_point_2/climax/resolution等）",
            "description": "详细描述",
            "emotional_intensity": 1-10,
            "escalated_conflicts": ["在此节点升级的冲突ID"],
            "involved_characters": ["角色ID"],
            "consequences": ["后果"],
            "is_branching_point": true/false,
            "branching_options": ["选项描述"]
        }}
    ]
}}

冲突交织原则（核心要求）:
1. 主冲突贯穿始终 - 在开头、中期、高潮都要有主冲突的升级
2. 次要冲突穿插其间 - 在主冲突发展过程中穿插次要冲突
3. 冲突交织上升 - 不是简单的"先生成主冲突再生成次要冲突"
4. 节奏变化 - 小冲突→大冲突→小冲突→极大冲突（波浪式上升）

具体要求:
1. 必须包含4-6个critical_choice类型的核心抉择节点
2. emotional_intensity要从1逐渐上升到10（但允许有波动）
3. 每个节点都要有具体的冲突升级（escalated_conflicts不能为空）
4. 主冲突要在多个节点升级，不是只在一个节点
5. 次要冲突要在主冲突的节点之间穿插
6. 抉择节点要有详细的分支选项和后果
7. 节点类型要多样化：inciting_incident, plot_point_1, midpoint, critical_choice_X, plot_point_2, climax, resolution

示例节奏:
- node_1 (inciting_incident): 主冲突1开始，intensity=2
- node_2 (plot_point_1): 主冲突1+次要冲突1，intensity=4
- node_3 (critical_choice_1): 主冲突1+2升级，intensity=6
- node_4: 次要冲突2爆发，intensity=5（稍降）
- node_5 (midpoint): 所有主冲突汇聚，intensity=7
- ...
- node_10 (climax): 所有冲突达到顶点，intensity=10
"""

# ============ 生成冲突链和势力博弈 ============

GENERATE_CONFLICT_CHAIN_HUMAN_PROMPT = """请基于所有冲突，生成冲突链和势力博弈。

【用户原始创意 - 第一参考】
{user_idea}

【修复指令（如果有）】
{fix_instructions}

【所有冲突】
{all_conflicts}

【角色弧光】
{cast_arc_json}

请以JSON格式输出:
{{
    "conflict_chain": [
        "冲突A的具体因果如何引发冲突B",
        "冲突B与冲突C的具体交织方式"
    ],
    "faction_conflicts": {{
        "势力ID": ["相关的冲突ID列表"]
    }},
    "unbreakable_rules": ["从world_setting.rules引用的不可打破规则"],
    "conflict_constraints": ["确保一致性的注意事项"]
}}

要求:
1. conflict_chain要具体描述因果关系
2. faction_conflicts的key必须是worldbuilding.factions中已有的faction_id
"""

# 导出所有prompt
CONFLICT_ENGINE_SYSTEM_PROMPT_STR = CONFLICT_ENGINE_SYSTEM_PROMPT
