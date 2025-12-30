# GAL-Dreamer 导演系统设计文档

## 1. 概述

### 1.1 目标
设计一个实时对话驱动的 GAL 游戏导演系统，根据用户输入动态推进剧情，世界状态会根据玩家发言实时变化。

### 1.2 核心职责
```
导演系统 (Director)
    ├── 解析用户输入
    ├── 评估当前状态（角色好感度、物品、世界状态、大纲进度）
    ├── 决定下一步剧情走向
    ├── 生成场景描述
    ├── 生成角色对话
    └── 更新世界状态
```

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          GAL-Dreamer 实时运行时                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────┐     ┌─────────────────────────────────────────────┐ │
│  │   用户输入    │────▶│            DirectorSystem                    │ │
│  │  (对话/选择)  │     │  ┌─────────────────────────────────────────┐ │ │
│  └───────────────┘     │  │         DirectorAgent (导演AI)          │ │ │
│                        │  │  - 分析用户意图                         │ │ │
│                        │  │  - 评估当前状态                         │ │ │
│                        │  │  - 决定剧情走向                         │ │ │
│                        │  │  - 触发事件/转折点                      │ │ │
│                        │  └─────────────────────────────────────────┘ │ │
│                        │                      │                        │ │
│                        │                      ▼                        │ │
│                        │  ┌─────────────────────────────────────────┐ │ │
│                        │  │         RuntimeStateManager              │ │ │
│                        │  │  - 角色好感度                           │ │ │
│                        │  │  - 主角物品背包                         │ │ │
│                        │  │  - 当前位置/时间                         │ │
│                        │  │  - 已触发事件                           │ │ │
│                        │  │  - Flag系统                             │ │ │
│                        │  │  - 大纲进度追踪                          │ │ │
│                        │  └─────────────────────────────────────────┘ │ │
│                        │                      │                        │ │
│                        │                      ▼                        │ │
│                        │  ┌─────────────────────────────────────────┐ │ │
│                        │  │           SceneGenerator                 │ │ │
│                        │  │  - 生成场景描述                         │ │ │
│                        │  │  - 确定在场角色                         │ │ │
│                        │  │  - 设定氛围基调                         │ │ │
│                        │  └─────────────────────────────────────────┘ │ │
│                        │                      │                        │ │
│                        │                      ▼                        │ │
│                        │  ┌─────────────────────────────────────────┐ │ │
│                        │  │          DialogueGenerator               │ │ │
│                        │  │  - 生成角色对话                         │ │ │
│                        │  │  - 根据好感度调整语气                   │ │ │
│                        │  │  - 推进情节                             │ │ │
│                        │  └─────────────────────────────────────────┘ │ │
│                        │                                              │ │
│                        └─────────────────────────────────────────────┘ │
│                                       │                                 │
│                                       ▼                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                           静态数据层                                │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │ │
│  │  │ World      │  │ Story      │  │ Cast       │  │ Conflict   │  │ │
│  │  │ Setting    │  │ Premise    │  │ Arc        │  │ Map        │  │ │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

| 组件 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **DirectorAgent** | 导演AI，核心决策 | 用户输入 + 当前状态 + 静态数据 | 导演决策 |
| **RuntimeStateManager** | 运行时状态管理 | 状态更新指令 | 当前完整状态 |
| **SceneGenerator** | 场景生成 | 导演决策 + 状态 | 场景描述 |
| **DialogueGenerator** | 对话生成 | 场景 + 角色 + 用户输入 | 对话文本 |

---

## 3. 数据模型设计

### 3.1 运行时状态模型

```python
# models/runtime/runtime_state.py

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime

class AffectionLevel(BaseModel):
    """单个角色的好感度状态"""
    character_id: str = Field(..., description="角色ID")
    character_name: str = Field(..., description="角色名称")
    affection_value: int = Field(default=50, ge=0, le=100, description="好感度值 0-100")
    affection_stage: Literal["stranger", "acquaintance", "friend", "close", "love", "obsessed"] = Field(
        default="stranger", description="好感度阶段"
    )
    trust_level: int = Field(default=50, ge=0, le=100, description="信任度 0-100")
    last_interaction_type: str = Field(default="", description="上次交互类型")
    interaction_count: int = Field(default=0, description="交互次数")

    # 角色特定状态
    mood: str = Field(default="neutral", description="当前情绪")
    revealed_secrets: List[str] = Field(default_factory=list, description="已揭露的秘密")
    triggered_growth_nodes: List[str] = Field(default_factory=list, description="已触发的成长节点")

class InventoryItem(BaseModel):
    """背包物品"""
    item_id: str = Field(..., description="物品ID")
    name: str = Field(..., description="物品名称")
    description: str = Field(..., description="物品描述")
    quantity: int = Field(default=1, ge=0, description="数量")
    is_equipped: bool = Field(default=False, description="是否装备")
    obtained_from: Optional[str] = Field(None, description="获得来源")
    obtained_at_scene: Optional[str] = Field(None, description="获得场景")

class WorldState(BaseModel):
    """世界状态"""
    current_location_id: str = Field(..., description="当前位置ID")
    current_location_name: str = Field(..., description="当前位置名称")
    current_time: str = Field(..., description="当前时间 (如: 平日早晨、周末夜晚)")
    current_chapter: int = Field(default=1, ge=1, description="当前章节")
    current_scene: int = Field(default=1, ge=1, description="当前场景")

    # 大纲进度追踪
    escalation_progress: float = Field(default=0.0, ge=0.0, le=1.0, description="危机升级进度 0-1")
    passed_escalation_nodes: List[str] = Field(default_factory=list, description="已通过的危机节点")
    active_conflicts: List[str] = Field(default_factory=list, description="当前活跃的冲突ID")

    # 已发生的事件
    triggered_events: List[str] = Field(default_factory=list, description="已触发的事件ID")
    completed_scenes: List[str] = Field(default_factory=list, description="已完成的场景ID")

class FlagSystem(BaseModel):
    """Flag系统"""
    flags: Dict[str, bool] = Field(default_factory=dict, description="所有Flag {flag_name: is_set}")
    counters: Dict[str, int] = Field(default_factory=dict, description="计数器 {counter_name: value}")

    def set_flag(self, flag_name: str, value: bool = True):
        """设置Flag"""
        self.flags[flag_name] = value

    def get_flag(self, flag_name: str) -> bool:
        """获取Flag"""
        return self.flags.get(flag_name, False)

    def increment_counter(self, counter_name: str, amount: int = 1):
        """增加计数器"""
        self.counters[counter_name] = self.counters.get(counter_name, 0) + amount

class PlayerProfile(BaseModel):
    """主角档案（运行时）"""
    protagonist_id: str = Field(..., description="主角ID")
    name: str = Field(default="主角", description="主角名称")

    # 背包
    inventory: List[InventoryItem] = Field(default_factory=list, description="背包物品")

    # 状态
    health: int = Field(default=100, ge=0, le=100, description="健康值")
    mental_state: str = Field(default="normal", description="精神状态")
    current_goal: str = Field(default="", description="当前目标")

    # 已做出的关键选择
    critical_choices: List[Dict[str, str]] = Field(
        default_factory=list,
        description="关键选择记录 [{choice_point_id, choice_made, timestamp}]"
    )

class RuntimeState(BaseModel):
    """完整的运行时状态"""
    state_id: str = Field(..., description="状态ID (session_id)")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")

    # 核心状态
    player: PlayerProfile = Field(..., description="主角状态")
    world: WorldState = Field(..., description="世界状态")
    affections: List[AffectionLevel] = Field(default_factory=list, description="所有角色好感度")
    flags: FlagSystem = Field(default_factory=FlagSystem, description="Flag系统")

    # 历史记录
    dialogue_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="对话历史 [{speaker, content, scene_id, timestamp}]"
    )

    # 会话状态
    current_scene_id: Optional[str] = Field(None, description="当前场景ID")
    active_characters: List[str] = Field(default_factory=list, description="当前在场角色")

    # 来源数据
    source_world_setting: str = Field(..., description="来源的世界观数据ID")
    source_story_outline: str = Field(..., description="来源的故事大纲ID")

    def get_affection(self, character_id: str) -> Optional[AffectionLevel]:
        """获取指定角色的好感度"""
        for aff in self.affections:
            if aff.character_id == character_id:
                return aff
        return None

    def update_affection(self, character_id: str, delta: int):
        """更新好感度"""
        aff = self.get_affection(character_id)
        if aff:
            old_value = aff.affection_value
            aff.affection_value = max(0, min(100, aff.affection_value + delta))
            # 自动更新阶段
            if aff.affection_value >= 90:
                aff.affection_stage = "love"
            elif aff.affection_value >= 70:
                aff.affection_stage = "close"
            elif aff.affection_value >= 50:
                aff.affection_stage = "friend"
            elif aff.affection_value >= 30:
                aff.affection_stage = "acquaintance"
            else:
                aff.affection_stage = "stranger"
            return aff.affection_value - old_value
        return 0

    def has_item(self, item_id: str) -> bool:
        """检查是否拥有物品"""
        return any(item.item_id == item_id and item.quantity > 0 for item in self.player.inventory)

    def add_item(self, item: InventoryItem):
        """添加物品"""
        # 检查是否已存在
        for existing in self.player.inventory:
            if existing.item_id == item.item_id:
                existing.quantity += item.quantity
                return
        self.player.inventory.append(item)

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        """移除物品"""
        for item in self.player.inventory:
            if item.item_id == item_id:
                if item.quantity >= quantity:
                    item.quantity -= quantity
                    if item.quantity == 0:
                        self.player.inventory.remove(item)
                    return True
        return False
```

### 3.2 导演决策模型

```python
# models/runtime/director_decision.py

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Any

class DecisionType(BaseModel):
    """决策类型"""
    type: Literal[
        "continue_dialogue",    # 继续对话
        "change_scene",         # 切换场景
        "trigger_event",        # 触发事件
        "offer_choice",         # 提供选择
        "escalate_conflict",    # 升级冲突
        "resolve_conflict",     # 解决冲突
        "character_development",# 角色发展
        "branch_route",         # 分支路线
        "ending_approach"       # 接近结局
    ] = Field(..., description="决策类型")

class DirectorDecision(BaseModel):
    """导演决策结果"""
    decision_id: str = Field(..., description="决策ID")
    timestamp: str = Field(..., description="时间戳")

    # 决策类型和理由
    decision_type: DecisionType = Field(..., description="决策类型")
    reasoning: str = Field(..., description="决策理由")

    # 场景控制
    next_scene_id: Optional[str] = Field(None, description="下一个场景ID")
    scene_change_type: Optional[Literal["fade", "cut", "dissolve", "transition"]] = Field(
        None, description="场景切换类型"
    )

    # 角色控制
    characters_to_enter: List[str] = Field(default_factory=list, description="进场的角色ID")
    characters_to_exit: List[str] = Field(default_factory=list, description="退场的角色ID")
    focus_character: Optional[str] = Field(None, description="焦点角色ID")

    # 事件控制
    event_to_trigger: Optional[str] = Field(None, description="要触发的事件ID")
    event_priority: Literal["background", "foreground", "interrupt"] = Field(
        default="background", description="事件优先级"
    )

    # 冲突控制
    conflict_to_escalate: Optional[str] = Field(None, description="要升级的冲突ID")
    escalation_amount: float = Field(default=0.1, ge=0.0, le=1.0, description="升级幅度")

    # 选择控制
    choice_options: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="选择选项 [{choice_id, text, affection_impact, flags}]"
    )

    # 状态更新指令
    state_updates: Dict[str, Any] = Field(
        default_factory=dict,
        description="状态更新指令 {affection_changes, flags_to_set, items_to_add, items_to_remove}"
    )

    # 叙事控制
    narrative_tone: Literal["daily", "sweet", "suspense", "angst", "climax", "aftermath", "comedy"] = Field(
        default="daily", description="叙事基调"
    )
    emotional_intensity: int = Field(default=5, ge=1, le=10, description="情感强度")
    pacing: Literal["slow", "medium", "fast", "rapid"] = Field(default="medium", description="节奏")

    # 剧情推进
    plot_progress: float = Field(default=0.0, ge=0.0, le=1.0, description="剧情推进程度")
    arc_progress: Dict[str, float] = Field(
        default_factory=dict,
        description="各角色弧光进度 {character_id: progress}"
    )

    # 指引给生成器
    scene_guidance: str = Field(default="", description="场景生成指引")
    dialogue_guidance: str = Field(default="", description="对话生成指引")

class DialogueLine(BaseModel):
    """单句对话"""
    line_id: str = Field(..., description="对话ID")
    speaker_id: str = Field(..., description="说话者ID")
    speaker_name: str = Field(..., description="说话者名称")

    content: str = Field(..., description="对话内容")
    tone: str = Field(default="neutral", description="语气")

    # 表现细节
    expression: Optional[str] = Field(None, description="表情")
    action: Optional[str] = Field(None, description="动作")
    position: Optional[str] = Field(None, description="位置")

    # 元数据
    is_narration: bool = Field(default=False, description="是否为旁白")
    is_inner_thought: bool = Field(default=False, description="是否为内心独白")

class SceneOutput(BaseModel):
    """场景输出"""
    scene_id: str = Field(..., description="场景ID")
    scene_name: str = Field(..., description="场景名称")

    # 场景描述
    location_description: str = Field(..., description="地点描述")
    atmosphere: str = Field(..., description="氛围描述")
    time_period: str = Field(..., description="时间段")

    # 在场角色
    present_characters: List[str] = Field(default_factory=list, description="在场角色ID")

    # 对话内容
    dialogues: List[DialogueLine] = Field(default_factory=list, description="对话列表")

    # 如果有选择
    has_choice: bool = Field(default=False, description="是否有选择点")
    choice_options: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="选择选项"
    )

    # 场景结束条件
    end_conditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="场景结束条件"
    )
```

---

## 4. DirectorAgent 设计

### 4.1 Director Prompt 设计

```python
# prompts/runtime/director_prompt.py

DIRECTOR_SYSTEM_PROMPT = """你是GAL游戏的导演AI，负责根据玩家输入决定剧情走向。

【核心职责】
1. 分析玩家输入的意图和情感
2. 结合当前状态（好感度、物品、世界状态、大纲进度）做出决策
3. 决定剧情的下一步发展
4. 确保故事连贯性，与世界观和角色设定一致

【决策原则】
1. 好感度驱动：不同好感度阶段，角色的反应完全不同
2. 物品系统：关键物品影响剧情分支
3. 冲突升级：根据大纲中的冲突引擎，适时推进危机
4. 角色弧光：在合适的时机触发角色的成长节点
5. 意外与必然：平衡玩家自由度与故事必然性

【状态解读】
- 好感度0-20: 敌对/疏远
- 好感度21-40: 陌生/冷淡
- 好感度41-60: 普通朋友
- 好感度61-80: 亲密朋友/暧昧
- 好感度81-100: 深爱/ obsessed

【决策类型】
- continue_dialogue: 继续当前对话，深化关系或推进情节
- change_scene: 切换到新场景，推进故事节奏
- trigger_event: 触发预设事件或生成新事件
- offer_choice: 提供给玩家选择点
- escalate_conflict: 推进主线冲突升级
- character_development: 触发角色成长节点
- branch_route: 明确进入某女主路线
- ending_approach: 接近结局

【输出格式】
严格按照JSON格式输出，包含所有必填字段。
"""

DIRECTOR_HUMAN_PROMPT = """【玩家输入】
{user_input}

【当前状态】
{runtime_state}

【角色信息】
{characters_info}

【冲突进度】
{conflict_info}

【最近对话历史】
{dialogue_history}

【可用事件池】
{available_events}

【大纲指引】
{outline_guidance}

请做出导演决策，输出JSON格式。"""
```

### 4.2 DirectorAgent 实现

```python
# agents/runtime/director_agent.py

from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from prompts.runtime.director_prompt import (
    DIRECTOR_SYSTEM_PROMPT,
    DIRECTOR_HUMAN_PROMPT
)
from models.runtime.director_decision import DirectorDecision
from utils.logger import log

class DirectorAgent(BaseAgent):
    """导演Agent - 实时剧情决策核心"""

    name = "DirectorAgent"
    system_prompt = DIRECTOR_SYSTEM_PROMPT
    human_prompt_template = DIRECTOR_HUMAN_PROMPT
    required_fields = [
        "decision_type", "reasoning", "narrative_tone",
        "emotional_intensity", "pacing", "scene_guidance", "dialogue_guidance"
    ]
    output_model = DirectorDecision

    def decide(
        self,
        user_input: str,
        runtime_state: Dict[str, Any],
        characters_info: Dict[str, Any],
        conflict_info: Dict[str, Any],
        dialogue_history: List[Dict[str, str]],
        available_events: List[Dict[str, Any]],
        outline_guidance: Dict[str, Any],
    ) -> DirectorDecision:
        """
        做出导演决策

        Args:
            user_input: 玩家输入
            runtime_state: 当前运行时状态
            characters_info: 角色信息
            conflict_info: 冲突进度信息
            dialogue_history: 最近对话历史
            available_events: 可触发事件池
            outline_guidance: 大纲指引

        Returns:
            DirectorDecision: 导演决策
        """
        log.info(f"DirectorAgent 决策中... 玩家输入: {user_input[:50]}...")

        # 构建状态描述
        runtime_state_str = self._format_runtime_state(runtime_state)
        characters_str = self._format_characters(characters_info, runtime_state)
        conflict_str = self._format_conflict(conflict_info)
        history_str = self._format_dialogue_history(dialogue_history)
        events_str = self._format_events(available_events)
        outline_str = self._format_outline(outline_guidance)

        result = self.run(
            user_input=user_input,
            runtime_state=runtime_state_str,
            characters_info=characters_str,
            conflict_info=conflict_str,
            dialogue_history=history_str,
            available_events=events_str,
            outline_guidance=outline_str
        )

        # 生成决策ID
        import uuid
        from datetime import datetime
        result["decision_id"] = f"decision_{uuid.uuid4().hex[:8]}"
        result["timestamp"] = datetime.now().isoformat()

        decision = DirectorDecision(**result)
        self._log_decision(decision)

        return decision

    def _format_runtime_state(self, state: Dict[str, Any]) -> str:
        """格式化运行时状态"""
        lines = ["=== 当前状态 ==="]

        player = state.get("player", {})
        world = state.get("world", {})

        # 主角信息
        lines.append(f"主角: {player.get('name', '未知')}")
        lines.append(f"当前位置: {world.get('current_location_name', '未知')}")
        lines.append(f"当前时间: {world.get('current_time', '未知')}")
        lines.append(f"章节: {world.get('current_chapter', 1)} - 场景: {world.get('current_scene', 1)}")

        # 背包（关键物品）
        inventory = player.get("inventory", [])
        if inventory:
            lines.append(f"\n关键物品:")
            for item in inventory[:5]:  # 最多显示5个
                lines.append(f"  - {item.get('name', '未知')}")

        # 危机进度
        escalation = world.get("escalation_progress", 0.0)
        lines.append(f"\n危机升级进度: {escalation:.1%}")

        return "\n".join(lines)

    def _format_characters(self, characters: Dict[str, Any], runtime_state: Dict[str, Any]) -> str:
        """格式化角色信息（带好感度）"""
        lines = ["=== 角色状态 ==="]

        affections = runtime_state.get("affections", [])
        affection_map = {a["character_id"]: a for a in affections}

        for char_id, char_info in characters.items():
            # 获取好感度
            aff = affection_map.get(char_id, {})
            affection_value = aff.get("affection_value", 50)
            affection_stage = aff.get("affection_stage", "stranger")

            lines.append(f"\n[{char_info.get('name', '未知')}]")
            lines.append(f"  ID: {char_id}")
            lines.append(f"  好感度: {affection_value}/100 ({affection_stage})")
            lines.append(f"  当前情绪: {aff.get('mood', 'neutral')}")
            lines.append(f"  角色定位: {char_info.get('role_type', 'unknown')}")
            lines.append(f"  性格: {', '.join(char_info.get('personality', []))}")

            # 已揭露的秘密
            revealed = aff.get("revealed_secrets", [])
            if revealed:
                lines.append(f"  已揭露秘密: {len(revealed)}个")

            # 已触发的成长节点
            growth = aff.get("triggered_growth_nodes", [])
            if growth:
                lines.append(f"  成长进度: {len(growth)}/{len(char_info.get('growth_nodes', []))}")

        return "\n".join(lines)

    def _format_conflict(self, conflict: Dict[str, Any]) -> str:
        """格式化冲突信息"""
        lines = ["=== 冲突进度 ==="]

        active_conflicts = conflict.get("active_conflicts", [])
        if active_conflicts:
            for conf in active_conflicts:
                lines.append(f"\n- {conf.get('name', '未知')}")
                lines.append(f"  类型: {conf.get('type', 'unknown')}")
                lines.append(f"  等级: {conf.get('level', 'unknown')}")
                lines.append(f"  状态: {conf.get('status', 'active')}")
        else:
            lines.append("当前无活跃冲突")

        return "\n".join(lines)

    def _format_dialogue_history(self, history: List[Dict[str, str]]) -> str:
        """格式化对话历史"""
        if not history:
            return "=== 最近对话 ===\n(无)"

        lines = ["=== 最近对话 ==="]
        # 最多显示最近10句
        for line in history[-10:]:
            speaker = line.get("speaker_name", "未知")
            content = line.get("content", "")
            lines.append(f"{speaker}: {content}")

        return "\n".join(lines)

    def _format_events(self, events: List[Dict[str, Any]]) -> str:
        """格式化可用事件"""
        if not events:
            return "=== 可用事件 ===\n(无)"

        lines = ["=== 可用事件 ==="]
        for event in events[:10]:
            lines.append(f"\n- {event.get('name', '未知')} ({event.get('event_id', 'unknown')})")
            lines.append(f"  触发条件: {event.get('trigger_condition', '未知')}")
            lines.append(f"  类型: {event.get('type', 'unknown')}")

        return "\n".join(lines)

    def _format_outline(self, outline: Dict[str, Any]) -> str:
        """格式化大纲指引"""
        lines = ["=== 大纲指引 ==="]

        # 当前应该到达的大纲节点
        current_node = outline.get("current_node", {})
        if current_node:
            lines.append(f"\n当前大纲节点: {current_node.get('name', '未知')}")
            lines.append(f"节点类型: {current_node.get('type', 'unknown')}")
            lines.append(f"应该推进: {current_node.get('objective', '未知')}")

        # 附近的危机节点
        nearby_nodes = outline.get("nearby_nodes", [])
        if nearby_nodes:
            lines.append(f"\n即将到来的节点:")
            for node in nearby_nodes[:3]:
                lines.append(f"  - {node.get('name', '未知')} ({node.get('type', 'unknown')})")

        return "\n".join(lines)

    def _log_decision(self, decision: DirectorDecision) -> None:
        """记录决策日志"""
        log.info("导演决策生成:")
        log.info(f"  类型: {decision.decision_type.type}")
        log.info(f"  理由: {decision.reasoning[:100]}...")
        log.info(f"  基调: {decision.narrative_tone}, 强度: {decision.emotional_intensity}/10")
        log.info(f"  节奏: {decision.pacing}")

        if decision.characters_to_enter:
            log.info(f"  进场角色: {decision.characters_to_enter}")
        if decision.event_to_trigger:
            log.info(f"  触发事件: {decision.event_to_trigger}")

    def validate_output(self, output: Dict[str, Any]) -> bool | str:
        """验证输出"""
        # 检查decision_type
        dt = output.get("decision_type")
        if not dt:
            return "缺少decision_type"

        # decision_type可能是字符串或字典
        if isinstance(dt, dict):
            if "type" not in dt:
                return "decision_type必须包含type字段"
        elif not isinstance(dt, str):
            return "decision_type格式错误"

        # 检查reasoning
        if not output.get("reasoning"):
            return "缺少reasoning"

        # 检查narrative_tone
        valid_tones = ["daily", "sweet", "suspense", "angst", "climax", "aftermath", "comedy"]
        if output.get("narrative_tone") not in valid_tones:
            return f"narrative_tone必须是以下之一: {', '.join(valid_tones)}"

        # 检查emotional_intensity范围
        intensity = output.get("emotional_intensity", 5)
        if not isinstance(intensity, int) or intensity < 1 or intensity > 10:
            return "emotional_intensity必须是1-10的整数"

        return True
```

---

## 5. 使用流程

### 5.1 初始化流程

```python
# 1. 加载静态数据（由MainPipeline生成）
world_setting = load_json("world_setting.json")
story_outline = load_json("story_outline.json")

# 2. 初始化运行时状态
runtime_state = RuntimeState(
    state_id="session_001",
    player=PlayerProfile(
        protagonist_id=story_outline["protagonist"]["id"],
        name="主角"
    ),
    world=WorldState(
        current_location_id=world_setting["key_elements"]["locations"][0]["id"],
        current_location_name=world_setting["key_elements"]["locations"][0]["name"],
        current_time="平日早晨",
        current_chapter=1,
        current_scene=1
    ),
    affections=[
        AffectionLevel(
            character_id=heroine["id"],
            character_name=heroine["name"],
            affection_value=50,
            affection_stage="acquaintance"
        )
        for heroine in story_outline["heroines"]
    ],
    flags=FlagSystem(),
    source_world_setting=world_setting["id"],
    source_story_outline=story_outline["id"]
)

# 3. 初始化系统
director = DirectorAgent()
scene_generator = SceneGenerator()
dialogue_generator = DialogueGenerator()
```

### 5.2 运行循环

```python
def game_loop(user_input: str):
    """单次游戏循环"""

    # 1. 导演决策
    decision = director.decide(
        user_input=user_input,
        runtime_state=runtime_state.model_dump(),
        characters_info=extract_characters(story_outline),
        conflict_info=extract_conflicts(story_outline),
        dialogue_history=runtime_state.dialogue_history[-20:],
        available_events=get_available_events(runtime_state),
        outline_guidance=get_outline_guidance(runtime_state)
    )

    # 2. 应用状态更新
    apply_state_updates(runtime_state, decision.state_updates)

    # 3. 生成场景
    if decision.next_scene_id or decision.scene_guidance:
        scene = scene_generator.generate(
            decision=decision,
            runtime_state=runtime_state,
            world_setting=world_setting
        )
    else:
        scene = current_scene

    # 4. 生成对话
    dialogues = dialogue_generator.generate(
        decision=decision,
        scene=scene,
        runtime_state=runtime_state,
        characters=story_outline["characters"]
    )

    # 5. 更新历史
    for dialogue in dialogues:
        runtime_state.dialogue_history.append({
            "speaker": dialogue.speaker_id,
            "speaker_name": dialogue.speaker_name,
            "content": dialogue.content,
            "scene_id": scene.scene_id,
            "timestamp": datetime.now().isoformat()
        })

    # 6. 返回输出
    return {
        "scene": scene,
        "dialogues": dialogues,
        "decision": decision
    }
```

---

## 6. 目录结构

```
GAL-Dreamer/
├── agents/
│   ├── base_agent.py
│   ├── runtime/
│   │   ├── __init__.py
│   │   ├── director_agent.py         # 导演Agent
│   │   ├── scene_generator_agent.py  # 场景生成Agent
│   │   └── dialogue_generator_agent.py # 对话生成Agent
├── models/
│   ├── runtime/
│   │   ├── __init__.py
│   │   ├── runtime_state.py          # 运行时状态模型
│   │   └── director_decision.py      # 导演决策模型
├── prompts/
│   └── runtime/
│       ├── __init__.py
│       ├── director_prompt.py        # 导演Prompt
│       ├── scene_prompt.py           # 场景Prompt
│       └── dialogue_prompt.py        # 对话Prompt
├── runtime/
│   ├── __init__.py
│   ├── director_system.py            # 导演系统主类
│   ├── state_manager.py              # 状态管理器
│   └── event_system.py               # 事件系统
└── docs/
    └── director_system_design.md     # 本文档
```

---

## 7. 后续扩展

### 7.1 记忆系统
- 长期记忆：跨会话记住玩家偏好
- 短期记忆：当前会话的重要对话

### 7.2 事件系统
- 预设事件池（由故事大纲生成）
- 动态事件生成（根据当前状态）

### 7.3 多结局追踪
- 基于Flag和好感度的结局判定
- 多个结局可能性的实时计算

### 7.4 视觉反馈
- 场景图片生成
- 角色立绘变化
- CG触发时机
