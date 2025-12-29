# GAL-Dreamer 🎮

> 通过对话一步生成完整Galgame的AI Agent系统

## ✨ 特性

- 🤖 **多Agent协作**: 基于LangChain的智能Agent系统
- 🌍 **世界观构建**: 自动生成完整的世界观设定和背景故事
- 📜 **故事理解**: 智能分析用户创意，提取核心要素
- ⏳ **时间线生成**: 自动构建世界历史和关键事件时间线
- 🎭 **角色势力**: 生成NPC、势力组织和关键角色设定
- 🎨 **氛围营造**: 统一世界氛围和基调设定
- ✅ **一致性检查**: 自动检查并修复世界观设定中的矛盾
- 💻 **Pipeline架构**: 模块化设计，易于扩展和定制

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/lyra-planet/GAL-Dreamer.git
cd GAL-Dreamer

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件,填写你的配置
# 至少需要配置:
# - LLM_API_KEY (必填)
# - LLM_PROVIDER (默认qwen)
```

### 3. 验证配置

```bash
python -c "from utils.config import config; config.validate(); print('✓ 配置验证通过')"
```

### 4. 生成你的第一个世界观

```python
from pipelines.main_pipeline import MainPipeline

# 初始化
pipeline = MainPipeline()

# 生成世界观
result = pipeline.generate(
    user_idea="一个魔法与科技共存的蒸汽朋克世界，"
              "古代巨龙苏醒带来魔力的回归"
)

print(f"世界观已生成: {result['worldbuilding']['output_dir']}")
```

## 📖 项目结构

```
GAL-Dreamer/
├── agents/                    # Agent模块
│   ├── base_agent.py         # Agent基类
│   ├── story_intake_agent.py # 故事理解Agent
│   ├── worldbuilding_agent.py # 世界观构建Agent
│   ├── key_element_agent.py  # 关键元素提取Agent
│   ├── timeline_agent.py     # 时间线生成Agent
│   ├── atmosphere_agent.py   # 氛围设定Agent
│   ├── npc_faction_agent.py  # NPC势力生成Agent
│   ├── world_consistency_agent.py # 一致性检查Agent
│   ├── world_fixer_agent.py  # 世界观修复Agent
│   └── world_summary_agent.py # 世界观摘要Agent
├── pipelines/                 # Pipeline流程
│   ├── main_pipeline.py      # 主流程入口
│   └── worldbuilding_pipeline.py # 世界观构建流程
├── prompts/                   # Prompt模板
│   ├── story_intake_prompt.py
│   ├── worldbuilding_prompt.py
│   └── ...
├── models/                    # 数据模型
│   ├── story.py              # 故事相关模型
│   ├── world.py              # 世界观模型
│   ├── timeline.py           # 时间线模型
│   ├── faction.py            # 势力模型
│   └── ...
├── utils/                     # 工具类
│   ├── config.py             # 配置管理
│   ├── logger.py             # 日志管理
│   └── json_utils.py         # JSON工具
├── tests/                     # 测试文件
├── output/                    # 输出目录(已忽略)
├── docs/                      # 文档目录
├── .env.example               # 环境变量模板
├── requirements.txt           # 依赖列表
├── PROJECT_PLAN.md            # 完整技术方案
└── README.md                  # 项目说明
```

## ⚙️ 配置说明

### 环境变量

主要配置项(在`.env`文件中):

```bash
# LLM配置 (必填)
LLM_PROVIDER=qwen                    # 提供商: qwen, openai, claude
LLM_API_KEY=your-api-key-here        # API密钥
LLM_MODEL=qwen-plus                  # 模型名称

# 项目配置
PROJECT_OUTPUT_DIR=./output          # 输出目录
LOG_LEVEL=INFO                       # 日志级别
```

## 🗺️ 开发进度

### 已完成功能

- [x] **Phase 1**: 基础框架搭建
  - [x] Agent基类设计
  - [x] 配置管理系统
  - [x] 日志系统
  - [x] 数据模型定义

- [x] **Phase 2**: 世界观构建系统
  - [x] 故事理解Agent (StoryIntakeAgent)
  - [x] 世界观构建Agent (WorldbuildingAgent)
  - [x] 关键元素Agent (KeyElementAgent)
  - [x] 时间线Agent (TimelineAgent)
  - [x] 氛围Agent (AtmosphereAgent)
  - [x] NPC势力Agent (NpcFactionAgent)
  - [x] 一致性检查Agent (WorldConsistencyAgent)
  - [x] 世界观修复Agent (WorldFixerAgent)
  - [x] 世界观摘要Agent (WorldSummaryAgent)
  - [x] 世界观构建Pipeline (WorldbuildingPipeline)

- [x] **Phase 3**: 主流程集成
  - [x] MainPipeline框架
  - [x] 模块化执行流程
  - [x] 输出管理

### 计划功能

- [ ] **Phase 4**: 图像生成系统
  - [ ] Image Agent (集成Stable Diffusion/Flux)
  - [ ] 角色立绘生成
  - [ ] 背景图生成

- [ ] **Phase 5**: 剧情生成系统
  - [ ] Scene Agent (场景分解)
  - [ ] Dialogue Agent (对话生成)
  - [ ] 剧情脚本生成

- [ ] **Phase 6**: 代码生成系统
  - [ ] Code Agent (Ren'Py代码生成)
  - [ ] 项目构建Agent
  - [ ] 资源文件组织

- [ ] **Phase 7**: 完整流程集成测试
- [ ] **Phase 8**: 性能优化与用户体验提升

## 📝 输出示例

运行后会生成类似以下结构的世界观文件：

```json
{
  "world_name": "巨龙觉醒的蒸汽纪元",
  "world_type": "蒸汽朋克/高魔奇幻",
  "core_concepts": ["蒸汽科技", "龙血魔法", "工业革命"],
  "timeline": [...],
  "factions": [...],
  "atmosphere": {...}
}
```

## 🤝 贡献

欢迎贡献代码、提出建议或报告问题!

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - 强大的LLM应用框架
- [Ren'Py](https://www.renpy.org/) - 优秀的视觉小说引擎
- [Stable Diffusion](https://stability.ai/) - 强大的图像生成模型

## 📮 联系方式

- 项目主页: [GitHub](https://github.com/lyra-planet/GAL-Dreamer)
- 问题反馈: [Issues](https://github.com/lyra-planet/GAL-Dreamer/issues)

---

**想要变成美少女。。。**
