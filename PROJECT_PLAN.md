# GAL-Dreamer 项目技术方案

## 📋 项目概述

**项目名称**: GAL-Dreamer
**项目目标**: 通过LangChain构建的一步生成式GALGAME系统
**核心理念**: 用户只需提供故事创意，系统自动生成完整的可运行Galgame（人物立绘、背景贴图、剧情脚本、Ren'Py代码）

---

## 🏗️ 系统架构

### 整体架构图

```
用户输入层
    ↓
用户输入故事创意/角色设定/游戏主题
    ↓
┌─────────────────────────────────────────────┐
│        LangChain Agent编排层                 │
│         (核心控制中心)                        │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│          多Agent协作系统                      │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐  ┌──────────────┐        │
│  │Story Agent   │  │Character     │        │
│  │故事编剧Agent  │→ │Agent角色设计  │        │
│  │              │  │Agent         │        │
│  └──────────────┘  └──────────────┘        │
│         ↓                  ↓                 │
│  ┌──────────────┐  ┌──────────────┐        │
│  │Scene Agent   │  │Image Agent   │        │
│  │场景分解Agent  │→ │图像生成Agent  │        │
│  │              │  │(SD/Flux)     │        │
│  └──────────────┘  └──────────────┘        │
│         ↓                  ↓                 │
│  ┌──────────────┐  ┌──────────────┐        │
│  │Dialogue      │  │Code Agent    │        │
│  │Agent对话生成  │→ │Ren'Py代码    │        │
│  │              │  │生成Agent     │        │
│  └──────────────┘  └──────────────┘        │
│         ↓                  ↓               │
│  ┌──────────────────────────────────┐       │
│  │    Project Builder Agent         │       │
│  │    项目构建Agent (文件组织)       │         │
│  └──────────────────────────────────┘       │
│                                             │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│          输出层                              │
│  完整的Ren'Py项目 + 资源文件                 │
└─────────────────────────────────────────────┘
```

### 数据流转图

```
用户创意 (文本)
    ↓
故事大纲 (JSON)
    ↓
角色设定列表 (JSON)
    ↓
场景脚本 (JSON)
    ↓
图像生成Prompt (文本)
    ↓
角色立绘/背景图 (PNG)
    ↓
Ren'Py脚本代码 (.rpy)
    ↓
可运行的游戏项目
```

---

## 📁 项目目录结构

```
GAL-Dreamer/
│
├── agents/                          # Agent模块
│   ├── __init__.py
│   ├── base_agent.py               # Agent基类
│   ├── story_agent.py              # 故事编剧Agent
│   ├── character_agent.py          # 角色设计Agent
│   ├── scene_agent.py              # 场景分解Agent
│   ├── dialogue_agent.py           # 对话生成Agent
│   ├── image_agent.py              # 图像生成Agent
│   ├── code_agent.py               # Ren'Py代码生成Agent
│   └── builder_agent.py            # 项目构建Agent
│
├── chains/                          # LangChain链定义
│   ├── __init__.py
│   ├── game_chain.py               # 游戏生成主链
│   ├── story_chain.py              # 故事生成子链
│   ├── character_chain.py          # 角色生成子链
│   ├── image_chain.py              # 图像生成子链
│   └── code_chain.py               # 代码生成子链
│
├── prompts/                         # Prompt模板
│   ├── __init__.py
│   ├── story_prompts.py            # 故事生成Prompt
│   ├── character_prompts.py        # 角色设计Prompt
│   ├── scene_prompts.py            # 场景分解Prompt
│   ├── dialogue_prompts.py         # 对话生成Prompt
│   ├── image_prompts.py            # 图像生成Prompt
│   └── code_prompts.py             # 代码生成Prompt
│
├── tools/                           # 工具函数
│   ├── __init__.py
│   ├── image_generator.py          # 图像生成接口(SD/Flux)
│   ├── renpy_builder.py            # Ren'Py项目构建工具
│   ├── file_manager.py             # 文件管理工具
│   ├── validator.py                # 数据验证工具
│   └── formatters.py               # 格式化工具
│
├── memory/                          # 记忆系统
│   ├── __init__.py
│   ├── game_memory.py              # 游戏上下文记忆
│   └── checkpoint.py               # 检查点管理
│
├── models/                          # 数据模型
│   ├── __init__.py
│   ├── story.py                    # 故事数据模型
│   ├── character.py                # 角色数据模型
│   ├── scene.py                    # 场景数据模型
│   └── game.py                     # 游戏项目模型
│
├── utils/                           # 工具类
│   ├── __init__.py
│   ├── logger.py                   # 日志工具
│   ├── config.py                   # 配置管理
│   └── constants.py                # 常量定义
│
├── output/                          # 输出目录
│   └── generated_games/            # 生成的游戏项目
│       └── game_001/
│           ├── game/
│           │   ├── script.rpy
│           │   ├── characters.rpy
│           │   └── images/
│           │       ├── characters/
│           │       └── backgrounds/
│           └── README.md
│
├── config/                          # 配置文件
│   ├── config.yaml                 # 主配置
│   ├── agents.yaml                 # Agent配置
│   └── prompts.yaml                # Prompt配置
│
├── tests/                           # 测试文件
│   ├── test_agents.py
│   ├── test_chains.py
│   └── test_tools.py
│
├── examples/                        # 示例代码
│   ├── simple_game.py              # 简单示例
│   └── advanced_game.py            # 复杂示例
│
├── docs/                            # 文档
│   ├── API.md                      # API文档
│   ├── ARCHITECTURE.md             # 架构文档
│   └── TUTORIAL.md                 # 教程
│
├── main.py                          # 主入口
├── requirements.txt                 # 依赖列表
├── setup.py                         # 安装脚本
└── README.md                        # 项目说明
```

---

## 🤖 核心Agent设计

### 1. Story Agent (故事编剧Agent)

**功能职责:**
- 接收用户输入的游戏创意
- 生成完整故事大纲（章节划分）
- 设计故事主题和风格
- 规划角色关系网络
- 创建多重结局分支

**输入:**
```python
{
    "user_idea": "一个关于时间旅行的校园恋爱故事",
    "genre": "恋爱/奇幻",
    "length": "中等",  # 短篇/中篇/长篇
    "tone": "温馨/感人"
}
```

**输出:**
```python
{
    "story_id": "story_001",
    "title": "时空的恋人们",
    "outline": {
        "prologue": "主角在图书馆发现了一本古老的时间机器设计图...",
        "chapters": [
            {
                "chapter_id": 1,
                "title": "命运的邂逅",
                "summary": "主角第一次使用时间机器，遇见了女主角",
                "key_events": ["时间机器启动", "遇见女主角", "第一次对话"]
            },
            # 更多章节...
        ],
        "endings": [
            {
                "ending_id": "good_ending",
                "name": "真结局",
                "condition": "完成所有角色线"
            }
        ]
    },
    "themes": ["时间", "命运", "成长"],
    "main_characters": ["char_001", "char_002"]
}
```

**使用技术:**
- LangChain ChatPromptTemplate
- 结构化输出 (Structured Output)
- 故事模板库

---

### 2. Character Agent (角色设计Agent)

**功能职责:**
- 根据故事需求设计角色
- 生成角色详细设定（外貌/性格/背景）
- 设计角色立绘prompt
- 创建角色台词风格
- 建立角色关系图

**输入:**
```python
{
    "story_outline": {...},
    "role": "女主角",
    "archetype": "傲娇",
    "story_importance": "main"
}
```

**输出:**
```python
{
    "character_id": "char_001",
    "name": "樱小路 露娜",
    "name_reading": "Sakurakouji Luna",
    "age": 17,
    "personality": {
        "traits": ["傲娇", "大小姐", "努力家"],
        "description": "表面高傲，内心温柔的大小姐",
        "speech_style": "偶尔使用大小姐语气，称呼主角为'庶民'"
    },
    "appearance": {
        "hair": "银色长发",
        "eyes": "红色",
        "height": "162cm",
        "style": "优雅校服",
        "distinctive_features": ["丝带", "长筒袜"]
    },
    "background": "财阀千金，隐藏身份就读普通高中",
    "role_in_story": "女主角",
    "relationships": {
        "protagonist": "暗恋",
        "char_002": "青梅竹马/竞争对手"
    },
    "image_prompts": {
        "neutral": "(masterpiece, best quality), anime style, 1girl, silver hair, red eyes, school uniform, neutral expression, white background",
        "happy": "(masterpiece, best quality), anime style, 1girl, silver hair, red eyes, school uniform, smiling, blushing",
        "angry": "(masterpiece, best quality), anime style, 1girl, silver hair, red eyes, school uniform, angry expression, pouting",
        "sad": "(masterpiece, best quality), anime style, 1girl, silver hair, red eyes, school uniform, crying, tears"
    }
}
```

**使用技术:**
- 角色模板库
- 性格标签系统
- 外貌生成规则

---

### 3. Scene Agent (场景分解Agent)

**功能职责:**
- 将故事大纲分解为具体场景
- 设计场景流程和转场
- 规划背景和立绘使用
- 创建选择分支点

**输入:**
```python
{
    "story_outline": {...},
    "characters": [...],
    "chapter_id": 1
}
```

**输出:**
```python
{
    "scene_id": "scene_001",
    "chapter": 1,
    "title": "图书馆的邂逅",
    "location": "学校图书馆",
    "time": "放学后",
    "background": "library_afternoon",
    "characters_present": ["char_001", "protagonist"],
    "flow": [
        {
            "step": 1,
            "action": "show_background",
            "params": {"background": "library_afternoon"}
        },
        {
            "step": 2,
            "action": "show_character",
            "params": {
                "character": "char_001",
                "expression": "neutral",
                "position": "center"
            }
        },
        {
            "step": 3,
            "action": "dialogue",
            "params": {
                "speaker": "char_001",
                "text": "这里是...哪里？",
                "voice_tone": "困惑"
            }
        },
        {
            "step": 4,
            "action": "choice",
            "params": {
                "options": [
                    {
                        "text": "主动搭话",
                        "next_scene": "scene_002_a"
                    },
                    {
                        "text": "静静观察",
                        "next_scene": "scene_002_b"
                    }
                ]
            }
        }
    ]
}
```

---

### 4. Dialogue Agent (对话生成Agent)

**功能职责:**
- 根据场景生成自然对话
- 保持角色语言风格
- 加入情感和动作描写
- 生成心理描写

**输入:**
```python
{
    "scene": {...},
    "characters": {...},
    "context": "第一次见面"
}
```

**输出:**
```python
{
    "dialogue_id": "dlg_001",
    "lines": [
        {
            "line_id": 1,
            "speaker": "protagonist",
            "text": "那个...你没事吧？",
            "action": "走近女孩",
            "expression": "关心"
        },
        {
            "line_id": 2,
            "speaker": "char_001",
            "text": "哈？你在跟谁说话呢，庶民。",
            "action": "转过身，双手抱胸",
            "expression": "高傲",
            "thought": "（这个人在说什么啊...）"
        }
    ]
}
```

---

### 5. Image Agent (图像生成Agent)

**功能职责:**
- 调用Stable Diffusion生成角色立绘
- 生成多表情立绘变体
- 生成场景背景图
- 图像质量优化和风格统一
- 批量生成和管理图像资源

**输入:**
```python
{
    "character": {...},
    "emotions": ["neutral", "happy", "angry", "sad", "blushing"],
    "style": "anime",
    "resolution": (1024, 1536)
}
```

**处理流程:**
```python
# 1. 构建prompt
def build_image_prompt(character, emotion):
    base_prompt = "(masterpiece, best quality), anime style"
    char_desc = f"1girl, {character['appearance']['hair']}, {character['appearance']['eyes']}"
    emotion_prompt = character['image_prompts'][emotion]
    return f"{base_prompt}, {char_desc}, {emotion_prompt}"

# 2. 调用SD API
def generate_image(prompt, negative_prompt, steps=30):
    # 使用Stable Diffusion XL / Flux
    pass

# 3. 后处理
def post_process(image):
    # 放大、去噪、风格化
    pass
```

**输出:**
```python
{
    "character_id": "char_001",
    "images": {
        "neutral": "/path/to/char_001_neutral.png",
        "happy": "/path/to/char_001_happy.png",
        "angry": "/path/to/char_001_angry.png",
        "sad": "/path/to/char_001_sad.png"
    },
    "spritesheet": "/path/to/char_001_spritesheet.png"
}
```

**技术栈:**
- Stable Diffusion XL / Flux.1
- ControlNet (姿势控制)
- LoRA模型 (风格训练)
- Automatic1111 / ComfyUI (API接口)

---

### 6. Code Agent (代码生成Agent)

**功能职责:**
- 将游戏数据转换为Ren'Py脚本
- 生成角色定义文件
- 生成主脚本文件
- 生成GUI配置
- 组织资源文件结构

**输入:**
```python
{
    "story": {...},
    "characters": [...],
    "scenes": [...],
    "images": {...}
}
```

**生成的文件结构:**
```python
# game/characters.rpy
init python:
    # 定义角色颜色
    luna_color = "#ff6b9d"
    hana_color = "#6b9dff"

# 角色定义
define l = Character("樱小路 露娜", color=luna_color, image="luna")
define h = Character("朝仓 花奈", color=hana_color, image="hana")

# 角色立绩定义
image luna neutral = "images/characters/luna_neutral.png"
image luna happy = "images/characters/luna_happy.png"
image luna angry = "images/characters/luna_angry.png"

# game/script.rpy
# 故事开始
label start:
    # 场景1: 图书馆
    scene bg library_afternoon with fade

    "我" "这是...哪里？"

    show luna neutral at center with dissolve

    l "这里是...哪里？"

    # 选择分支
    menu:
        "主动搭话":
            jump talk_to_her
        "静静观察":
            jump observe_her

label talk_to_her:
    l "啊，你...！"

    jump continue_story

label observe_her:
    l "奇怪的感觉..."

    jump continue_story

label continue_story:
    # 故事继续...
```

**输出:**
```python
{
    "files": {
        "characters.rpy": "...",
        "script.rpy": "...",
        "options.rpy": "...",
        "gui/custom.rpy": "..."
    },
    "assets": {
        "images/characters/": [...],
        "images/backgrounds/": [...]
    }
}
```

---

### 7. Builder Agent (项目构建Agent)

**功能职责:**
- 创建Ren'Py项目目录结构
- 复制生成的文件到正确位置
- 配置项目元数据
- 生成可执行文件

**处理流程:**
```python
def build_renpy_project(game_data, output_path):
    # 1. 创建目录结构
    create_project_structure(output_path)

    # 2. 复制资源文件
    copy_images(game_data['images'], output_path)

    # 3. 写入脚本文件
    write_script_files(game_data['scripts'], output_path)

    # 4. 配置项目
    configure_project(game_data['config'], output_path)

    # 5. 打包项目
    package_project(output_path)

    return output_path
```

---

## ⛓️ LangChain实现方案

### 1. Sequential Chain (顺序链)

适用于简单流程，按顺序执行各个步骤。

```python
from langchain.chains import SequentialChain
from langchain_openai import ChatOpenAI

# 初始化LLM
llm = ChatOpenAI(
    model="qwen-plus",
    api_key="your-api-key",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.7
)

# 定义子链
story_chain = create_story_chain(llm)
character_chain = create_character_chain(llm)
scene_chain = create_scene_chain(llm)
image_chain = create_image_chain(llm)
code_chain = create_code_chain(llm)

# 组合主链
game_generation_chain = SequentialChain(
    chains=[
        story_chain,       # 步骤1: 生成故事
        character_chain,   # 步骤2: 设计角色
        scene_chain,       # 步骤3: 分解场景
        image_chain,       # 步骤4: 生成图像
        code_chain         # 步骤5: 生成代码
    ],
    input_variables=["user_idea"],
    output_variables=["project_path"],
    verbose=True
)

# 执行
result = game_generation_chain({
    "user_idea": "一个关于时间旅行的校园恋爱故事"
})
```

---

### 2. LangGraph (状态图)

适用于复杂流程，需要循环和条件判断。

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

# 定义游戏生成状态
class GameState(TypedDict):
    user_idea: str
    story_outline: dict
    characters: list
    scenes: list
    images: dict
    renpy_code: str
    project_path: str
    current_step: str
    errors: list

# 定义状态图
workflow = StateGraph(GameState)

# 添加节点
workflow.add_node("story_agent", story_node)
workflow.add_node("character_agent", character_node)
workflow.add_node("scene_agent", scene_node)
workflow.add_node("image_agent", image_node)
workflow.add_node("code_agent", code_node)
workflow.add_node("builder_agent", builder_node)

# 定义边和条件
workflow.set_entry_point("story_agent")
workflow.add_edge("story_agent", "character_agent")
workflow.add_edge("character_agent", "scene_agent")
workflow.add_edge("scene_agent", "image_agent")
workflow.add_edge("image_agent", "code_agent")
workflow.add_edge("code_agent", "builder_agent")
workflow.add_edge("builder_agent", END)

# 编译图
app = workflow.compile()

# 执行
result = app.invoke({
    "user_idea": "一个关于时间旅行的校园恋爱故事",
    "current_step": "story_generation"
})
```

---

### 3. Agent with Tools (带工具的Agent)

使用LangChain的Agent功能，动态调用工具。

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import tool

# 定义工具
@tool
def generate_story_outline(idea: str) -> dict:
    """生成故事大纲"""
    pass

@tool
def generate_character(story: dict, role: str) -> dict:
    """生成角色设定"""
    pass

@tool
def generate_character_image(character: dict) -> str:
    """生成角色立绘，返回图像路径"""
    pass

@tool
def generate_renpy_code(game_data: dict) -> str:
    """生成Ren'Py代码"""
    pass

# 创建工具列表
tools = [
    generate_story_outline,
    generate_character,
    generate_character_image,
    generate_renpy_code
]

# 创建Agent
agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

# 执行
result = agent_executor.invoke({
    "input": "根据创意'时间旅行的校园恋爱'生成一个完整的Galgame"
})
```

---

### 4. Memory System (记忆系统)

使用LangChain的持久化记忆，保存生成过程中的上下文。

```python
from langchain.memory import (
    ConversationBufferMemory,
    ConversationSummaryMemory
)
from langchain.checkpoint.sqlite import SqliteSaver

# 检查点保存器
memory = SqliteSaver.from_conn_string("game_memory.db")

# 配置Agent的memory
config = {"configurable": {"thread_id": "game_001"}]

# 在生成过程中保存状态
for step in game_generation_steps:
    result = agent.invoke(step, config)
    # 自动保存到checkpoint
```

---

## 🎨 Prompt工程

### 1. 故事生成Prompt

```python
STORY_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一位专业的GALGAME编剧，拥有10年以上的视觉小说创作经验。

你的任务是:
1. 根据用户的创意生成完整的GALGAME故事大纲
2. 故事要有明确的起承转合
3. 设计引人入胜的角色
4. 创建分支选项和多重结局
5. 保持故事的连贯性和逻辑性

输出格式要求:
- 必须是有效的JSON格式
- 包含title, outline, chapters, endings等字段
- 章节要有明确的summary和key_events

风格要求:
- 对话自然生动，符合角色性格
- 情感描写细腻
- 适当留白，给玩家想象空间"""),

    ("human", """请根据以下创意生成GALGAME故事:

用户创意: {user_idea}
游戏类型: {genre}
故事长度: {length}
整体基调: {tone}

请输出完整的故事大纲JSON格式。""")
])
```

---

### 2. 角色设计Prompt

```python
CHARACTER_DESIGN_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一位专业的角色设计师，擅长创作视觉小说角色。

你的任务是:
1. 根据故事需求设计立体的角色
2. 角色要有鲜明的性格特征
3. 外貌描写要具体详细
4. 设计角色关系网络
5. 为角色创建多套表情prompt

角色设计要点:
- 避免陈词滥调，给角色独特性
- 性格要有成长空间
- 外貌和性格要协调
- 背景故事要合理"""),

    ("human", """请为以下故事设计{role}角色:

故事背景: {story_outline}
角色定位: {role}
角色原型: {archetype}

请输出完整的角色设定JSON格式，包括:
- 基本信息(姓名、年龄、外貌)
- 性格特征
- 背景故事
- 角色关系
- 立绘prompt(至少5种表情)""")
])
```

---

### 3. 图像生成Prompt模板

```python
# 角色立绘prompt模板
CHARACTER_IMAGE_PROMPT_TEMPLATE = """
(masterpiece, best quality:1.2),
anime style,
{character_count},
{hair_color} {hair_style} hair,
{eye_color} eyes,
{clothing},
{expression},
{pose},
{background},
{style_tags},
{quality_tags}
"""

# 背景图prompt模板
BACKGROUND_IMAGE_PROMPT_TEMPLATE = """
(masterpiece, best quality:1.2),
anime background,
{location},
{time_of_day},
{weather},
{perspective},
{mood},
detailed, highly detailed
"""

# 示例
def build_character_prompt(character, emotion):
    return CHARACTER_IMAGE_PROMPT_TEMPLATE.format(
        character_count="1girl",
        hair_color=character['appearance']['hair_color'],
        hair_style=character['appearance']['hair_style'],
        eye_color=character['appearance']['eye_color'],
        clothing=character['appearance']['clothing'],
        expression=f"{emotion} expression",
        pose="standing, full body",
        background="simple white background",
        style_tags="cel shaded, vibrant colors",
        quality_tags="4k, ultra detailed"
    )
```

---

### 4. 代码生成Prompt

```python
RENPY_CODE_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一位Ren'Py视觉小说引擎专家。

你的任务是:
1. 将游戏数据转换为标准的Ren'Py脚本
2. 代码要符合Ren'Py语法规范
3. 合理使用label、menu、jump等语句
4. 添加适当的注释
5. 优化性能和可读性

Ren'Py代码规范:
- 角色定义使用Character()
- 场景切换使用scene语句
- 角色显示使用show/hide语句
- 对话使用"角色名" "内容"格式
- 选择分支使用menu语句"""),

    ("human", """请将以下游戏数据转换为Ren'Py代码:

故事数据: {story_data}
角色列表: {characters}
场景列表: {scenes}

请生成:
1. characters.rpy - 角色定义文件
2. script.rpy - 主脚本文件
3. 其他必要的配置文件

输出完整的代码内容。""")
])
```

---

## 🔧 技术实现细节

### 1. 图像生成工具集成

```python
# tools/image_generator.py
import requests
from typing import Dict, List
import base64
from PIL import Image
import io

class ImageGenerator:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key

    def generate_character_sprite(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 768,
        steps: int = 30,
        cfg_scale: float = 7.0
    ) -> str:
        """
        生成角色立绘

        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词
            width: 图像宽度
            height: 图像高度
            steps: 采样步数
            cfg_scale: CFG强度

        Returns:
            图像保存路径
        """
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "sampler_name": "DPM++ 2M Karras"
        }

        response = requests.post(
            f"{self.api_url}/sdapi/v1/txt2img",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

        result = response.json()
        image_data = base64.b64decode(result['images'][0])

        # 保存图像
        image = Image.open(io.BytesIO(image_data))
        output_path = f"output/character_{id(prompt)}.png"
        image.save(output_path)

        return output_path

    def generate_background(
        self,
        scene_description: str,
        style: str = "anime"
    ) -> str:
        """生成背景图"""
        prompt = self._build_background_prompt(scene_description, style)
        return self.generate_character_sprite(
            prompt,
            width=1920,
            height=1080
        )

    def _build_background_prompt(self, description: str, style: str) -> str:
        """构建背景图prompt"""
        return f"(masterpiece, best quality), {style} background, {description}, detailed, scenic"

# 使用示例
image_gen = ImageGenerator(
    api_url="http://localhost:7860",
    api_key="your-api-key"
)

character_image = image_gen.generate_character_sprite(
    prompt="(masterpiece, best quality), 1girl, silver hair, red eyes, school uniform, happy",
    negative_prompt="low quality, blurry, distorted"
)
```

---

### 2. Ren'Py项目构建工具

```python
# tools/renpy_builder.py
import os
import shutil
from pathlib import Path
from typing import Dict

class RenpyProjectBuilder:
    def __init__(self, base_template_path: str):
        self.base_template_path = Path(base_template_path)

    def build_project(
        self,
        game_data: Dict,
        output_path: str
    ) -> str:
        """
        构建完整的Ren'Py项目

        Args:
            game_data: 游戏数据
            output_path: 输出路径

        Returns:
            项目路径
        """
        # 1. 创建项目目录
        project_path = self._create_project_structure(output_path)

        # 2. 复制基础文件
        self._copy_base_files(project_path)

        # 3. 生成脚本文件
        self._generate_script_files(game_data, project_path)

        # 4. 复制图像资源
        self._copy_images(game_data['images'], project_path)

        # 5. 配置项目
        self._configure_project(game_data, project_path)

        return project_path

    def _create_project_structure(self, output_path: str) -> Path:
        """创建Ren'Py项目目录结构"""
        path = Path(output_path)
        directories = [
            "game",
            "game/images",
            "game/images/characters",
            "game/images/backgrounds",
            "game/audio",
            "game/fonts"
        ]

        for directory in directories:
            (path / directory).mkdir(parents=True, exist_ok=True)

        return path

    def _generate_script_files(self, game_data: Dict, project_path: Path):
        """生成Ren'Py脚本文件"""
        # 生成characters.rpy
        characters_code = self._generate_characters_code(game_data['characters'])
        (project_path / "game" / "characters.rpy").write_text(characters_code, encoding='utf-8')

        # 生成script.rpy
        script_code = self._generate_script_code(game_data['scenes'])
        (project_path / "game" / "script.rpy").write_text(script_code, encoding='utf-8')

    def _generate_characters_code(self, characters: List[Dict]) -> str:
        """生成角色定义代码"""
        code = "# 角色定义\n\n"

        for char in characters:
            code += f'define {char["tag"]} = Character("{char["name"]}", color="{char["color"]}")\n'
            code += f'image {char["tag"]} neutral = "images/characters/{char["tag"]}_neutral.png"\n'
            code += f'image {char["tag"]} happy = "images/characters/{char["tag"]}_happy.png"\n'
            code += '\n'

        return code

    def _generate_script_code(self, scenes: List[Dict]) -> str:
        """生成主脚本代码"""
        code = "label start:\n\n"

        for scene in scenes:
            code += f'    # {scene["title"]}\n'
            code += f'    scene bg {scene["background"]} with fade\n\n'

            for action in scene['actions']:
                if action['type'] == 'dialogue':
                    code += f'    {action["speaker"]} "{action["text"]}"\n'
                elif action['type'] == 'show':
                    code += f'    show {action["character"]} {action["expression"]} at {action["position"]}\n'
                elif action['type'] == 'choice':
                    code += "    menu:\n"
                    for option in action['options']:
                        code += f'        "{option["text"]}":\n'
                        code += f'            jump {option["next_label"]}\n'

            code += "\n"

        return code
```

---

### 3. 数据模型定义

```python
# models/story.py
from pydantic import BaseModel, Field
from typing import List, Optional

class Chapter(BaseModel):
    chapter_id: int = Field(..., description="章节ID")
    title: str = Field(..., description="章节标题")
    summary: str = Field(..., description="章节摘要")
    key_events: List[str] = Field(default_factory=list, description="关键事件")

class Ending(BaseModel):
    ending_id: str = Field(..., description="结局ID")
    name: str = Field(..., description="结局名称")
    condition: str = Field(..., description="达成条件")
    description: str = Field(..., description="结局描述")

class StoryOutline(BaseModel):
    story_id: str = Field(..., description="故事ID")
    title: str = Field(..., description="游戏标题")
    genre: str = Field(..., description="游戏类型")
    outline: str = Field(..., description="故事大纲")
    chapters: List[Chapter] = Field(default_factory=list, description="章节列表")
    endings: List[Ending] = Field(default_factory=list, description="结局列表")
    themes: List[str] = Field(default_factory=list, description="主题标签")

# models/character.py
class CharacterAppearance(BaseModel):
    hair: str = Field(..., description="发色发型")
    eyes: str = Field(..., description="眼睛颜色")
    height: str = Field(..., description="身高")
    style: str = Field(..., description="服装风格")
    distinctive_features: List[str] = Field(default_factory=list, description="特征")

class Character(BaseModel):
    character_id: str = Field(..., description="角色ID")
    name: str = Field(..., description="角色姓名")
    age: int = Field(..., description="年龄")
    personality: List[str] = Field(default_factory=list, description="性格特征")
    appearance: CharacterAppearance = Field(..., description="外貌描述")
    background: str = Field(..., description="背景故事")
    role_in_story: str = Field(..., description="故事中的角色")
    image_prompts: Dict[str, str] = Field(default_factory=dict, description="立绘prompt")
```

---

## 🚀 实施路线图

### Phase 1: 基础框架搭建 (第1-2周)

**目标**: 搭建项目基础架构

**任务清单:**
- [x] 创建项目目录结构
- [ ] 配置LangChain环境
- [ ] 实现基础数据模型
- [ ] 编写配置管理模块
- [ ] 设置日志系统

**交付物:**
- 完整的项目目录结构
- 基础配置文件
- 数据模型定义

---

### Phase 2: Story Agent实现 (第3-4周)

**目标**: 实现故事编剧Agent

**任务清单:**
- [ ] 编写Story Agent
- [ ] 创建故事生成Prompt
- [ ] 实现故事大纲生成
- [ ] 添加故事模板库
- [ ] 编写单元测试

**交付物:**
- 可用的Story Agent
- 故事生成示例
- 测试报告

---

### Phase 3: Character Agent实现 (第5-6周)

**目标**: 实现角色设计Agent

**任务清单:**
- [ ] 编写Character Agent
- [ ] 创建角色设计Prompt
- [ ] 实现角色生成逻辑
- [ ] 建立角色数据库
- [ ] 编写单元测试

**交付物:**
- 可用的Character Agent
- 角色生成示例
- 角色模板库

---

### Phase 4: Scene & Dialogue Agent (第7-8周)

**目标**: 实现场景分解和对话生成

**任务清单:**
- [ ] 实现Scene Agent
- [ ] 实现Dialogue Agent
- [ ] 创建场景分解逻辑
- [ ] 实现对话生成
- [ ] 添加情感和动作描写

**交付物:**
- Scene Agent和Dialogue Agent
- 场景生成示例
- 对话生成示例

---

### Phase 5: Image Agent实现 (第9-11周)

**目标**: 实现图像生成Agent

**任务清单:**
- [ ] 集成Stable Diffusion API
- [ ] 实现立绘生成功能
- [ ] 实现背景图生成
- [ ] 添加图像后处理
- [ ] 实现批量生成
- [ ] 建立图像缓存系统

**交付物:**
- 可用的Image Agent
- 图像生成示例
- 图像质量评估报告

---

### Phase 6: Code Agent实现 (第12-13周)

**目标**: 实现代码生成Agent

**任务清单:**
- [ ] 实现Code Agent
- [ ] 编写Ren'Py代码生成器
- [ ] 实现脚本文件生成
- [ ] 实现资源文件组织
- [ ] 添加代码优化功能

**交付物:**
- 可用的Code Agent
- 代码生成示例
- Ren'Py项目模板

---

### Phase 7: 完整流程集成 (第14-15周)

**目标**: 集成所有Agent，实现完整流程

**任务清单:**
- [ ] 实现主流程Chain
- [ ] 集成所有Agent
- [ ] 实现状态管理
- [ ] 添加错误处理
- [ ] 实现进度反馈
- [ ] 端到端测试

**交付物:**
- 完整的游戏生成流程
- 端到端测试报告
- 用户使用文档

---

### Phase 8: 优化和完善 (第16周)

**目标**: 优化性能，提升用户体验

**任务清单:**
- [ ] 性能优化
- [ ] 添加缓存机制
- [ ] 改进Prompt效果
- [ ] 优化图像质量
- [ ] 添加用户配置选项
- [ ] 编写完整文档

**交付物:**
- 优化后的系统
- 完整文档
- 使用教程

---

## 🔍 测试策略

### 1. 单元测试

```python
# tests/test_agents.py
import pytest
from agents.story_agent import StoryAgent

def test_story_agent_basic():
    agent = StoryAgent()
    result = agent.generate(
        user_idea="一个校园恋爱故事",
        genre="恋爱",
        length="短篇"
    )

    assert result is not None
    assert "story_id" in result
    assert "title" in result
    assert len(result["chapters"]) > 0

def test_character_agent():
    agent = CharacterAgent()
    result = agent.generate(
        story_outline={...},
        role="女主角"
    )

    assert result["name"] is not None
    assert len(result["image_prompts"]) >= 5
```

---

### 2. 集成测试

```python
# tests/test_integration.py
def test_full_game_generation():
    """测试完整的游戏生成流程"""
    chain = GameGenerationChain()

    result = chain.invoke({
        "user_idea": "一个时间旅行的校园恋爱故事"
    })

    assert result["project_path"] exists
    assert "game/script.rpy" exists
    assert "game/characters.rpy" exists
    assert character images exist
    assert background images exist
```

---

### 3. 质量评估

- **故事质量**: 使用LLM评估故事连贯性、角色塑造
- **图像质量**: 人工评估立绘和背景图质量
- **代码质量**: Ren'Py语法检查，游戏可运行测试
- **整体体验**: 完整游戏测试

---

## 📊 配置文件

### config/config.yaml

```yaml
# LLM配置
llm:
  provider: "qwen"  # qwen, openai, claude
  model: "qwen-plus"
  api_key: "your-api-key"
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  temperature: 0.7
  max_tokens: 4000

# 图像生成配置
image_generation:
  provider: "stable_diffusion"
  api_url: "http://localhost:7860"
  api_key: ""
  default_model: "sd_xl_base_1.0"
  default_steps: 30
  default_cfg_scale: 7.0

# Ren'Py配置
renpy:
  sdk_path: "/path/to/renpy/sdk"
  default_resolution: [1920, 1080]
  default_font: "DejaVuSans.ttf"

# 项目配置
project:
  output_dir: "output/generated_games"
  temp_dir: "temp"
  max_retries: 3
  timeout: 300

# 日志配置
logging:
  level: "INFO"
  file: "logs/gal_dreamer.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

## 🎯 示例用法

### 命令行使用

```bash
# 生成完整游戏
python main.py --idea "一个时间旅行的校园恋爱故事" --output ./my_game

# 指定游戏类型
python main.py --idea "勇者斗恶龙的改编故事" --genre "奇幻" --output ./fantasy_game

# 查看帮助
python main.py --help
```

### Python API使用

```python
from gal_dreamer import GALDreamer

# 初始化
dreamer = GALDreamer(config_path="config/config.yaml")

# 生成游戏
game = dreamer.generate(
    user_idea="一个时间旅行的校园恋爱故事",
    genre="恋爱/奇幻",
    length="中篇"
)

# 访问生成的游戏
print(f"游戏标题: {game.title}")
print(f"项目路径: {game.project_path}")

# 查看角色
for character in game.characters:
    print(f"角色: {character.name}")
```

---

## 🔮 未来扩展功能

### 1. 高级功能

- **语音合成**: 为角色添加语音
- **背景音乐**: 自动生成BGM
- **动画效果**: 添加立绘动画
- **Live2D支持**: 升级为Live2D立绘
- **存档系统**: 实现存档/读档
- **成就系统**: 添加游戏成就

### 2. 用户体验优化

- **Web界面**: 提供Web UI
- **实时预览**: 生成过程中实时预览
- **交互式编辑**: 允许用户调整生成内容
- **模板系统**: 提供更多游戏模板
- **社区分享**: 游戏分享平台

### 3. 技术优化

- **模型微调**: 针对Galgame微调LLM
- **LoRA训练**: 训练特定风格LoRA
- **分布式生成**: 支持多GPU并行生成
- **增量生成**: 支持增量更新内容

---

## 📝 开发规范

### 代码风格

- 遵循PEP 8规范
- 使用类型注解
- 编写文档字符串
- 单元测试覆盖率>80%

### Git提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

### 分支管理

- `main`: 主分支
- `develop`: 开发分支
- `feature/*`: 功能分支
- `bugfix/*`: 修复分支

---

## 🛠️ 技术栈总结

| 模块 | 技术选型 |
|------|---------|
| **AI框架** | LangChain, LangGraph |
| **LLM** | 通义千问 / GPT-4 / Claude |
| **图像生成** | Stable Diffusion XL / Flux.1 |
| **游戏引擎** | Ren'Py |
| **数据存储** | SQLite, JSON, YAML |
| **图像处理** | Pillow, OpenCV |
| **Web框架** | FastAPI (可选) |
| **测试框架** | pytest |
| **日志系统** | Python logging |

---

## 📚 参考资源

### 文档
- [LangChain文档](https://python.langchain.com/)
- [Ren'Py文档](https://www.renpy.org/doc/html/)
- [Stable Diffusion文档](https://stability.ai/)

### 开源项目
- [Librian](https://github.com/32float/Librian) - 另一个AI Galgame生成器
- [Ren'Py官方示例](https://github.com/renpy/renpy)

### 学习资源
- GALGAME剧本写作技巧
- 角色设计教程
- Prompt工程指南

---

## 🎉 总结

GAL-Dreamer是一个创新的AI驱动Galgame生成系统，通过LangChain的多Agent协作，实现从创意到完整游戏的自动化生成。

**核心优势:**
- ✅ 一步生成完整游戏
- ✅ 高度自动化
- ✅ 可定制化强
- ✅ 易于扩展

**适用场景:**
- 独立游戏开发者快速原型
- 创作爱好者实现创意
- 教育工具学习编程
- AI应用研究

让我们一起用AI创造精彩的视觉小说世界！🎮✨
