# GAL-Dreamer 🎮

> 通过对话一步生成完整Galgame的AI Agent系统

## ✨ 特性

- 🤖 **多Agent协作**: 基于LangChain的智能Agent系统
- 📖 **自动编剧**: 自动生成完整的故事大纲和角色设定
- 🎨 **图像生成**: 集成Stable Diffusion生成角色立绘和背景
- 💻 **代码生成**: 自动生成可运行的Ren'Py项目
- 🔄 **端到端**: 从创意到完整游戏,一步到位

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/yourusername/GAL-Dreamer.git
cd GAL-Dreamer

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

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
# - IMAGE_API_URL (如果使用Stable Diffusion)
```

### 3. 验证配置

```bash
python -c "from utils.config import config; config.validate(); print('✓ 配置验证通过')"
```

### 4. 生成你的第一个Galgame

```python
from gal_dreamer import GALDreamer

# 初始化
dreamer = GALDreamer()

# 生成游戏
game = dreamer.generate(
    user_idea="一个时间旅行的校园恋爱故事"
)

print(f"游戏已生成: {game.project_path}")
```

## 📖 项目结构

```
GAL-Dreamer/
├── agents/          # Agent模块
├── chains/          # LangChain链
├── prompts/         # Prompt模板
├── tools/           # 工具函数
├── models/          # 数据模型
├── utils/           # 工具类
│   ├── config.py    # 配置管理
│   └── logger.py    # 日志管理
├── output/          # 输出目录
├── .env.example     # 环境变量模板
├── requirements.txt # 依赖列表
└── PROJECT_PLAN.md  # 完整技术方案
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

详细配置说明请参考 [配置文档](docs/CONFIG.md)

## 📚 文档

- [完整技术方案](PROJECT_PLAN.md) - 详细的系统设计和实现方案
- [快速开始教程](docs/TUTORIAL.md) - 入门教程
- [API文档](docs/API.md) - API接口文档
- [配置指南](docs/CONFIG.md) - 详细配置说明

## 🔧 开发

### 运行测试

```bash
# 运行所有测试
pytest

# 运行单个测试
pytest tests/test_agents.py

# 查看覆盖率
pytest --cov=.
```

### 代码规范

```bash
# 格式化代码
black .

# 检查代码风格
flake8 .

# 类型检查
mypy .
```

## 🗺️ 开发路线

- [x] Phase 1: 基础框架搭建
- [ ] Phase 2: Story Agent实现
- [ ] Phase 3: Character Agent实现
- [ ] Phase 4: Scene & Dialogue Agent
- [ ] Phase 5: Image Agent实现
- [ ] Phase 6: Code Agent实现
- [ ] Phase 7: 完整流程集成
- [ ] Phase 8: 优化和完善

## 🤝 贡献

欢迎贡献代码、提出建议或报告问题!

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - 强大的LLM应用框架
- [Ren'Py](https://www.renpy.org/) - 优秀的视觉小说引擎
- [Stable Diffusion](https://stability.ai/) - 强大的图像生成模型

## 📮 联系方式

- 项目主页: [GitHub](https://github.com/yourusername/GAL-Dreamer)
- 问题反馈: [Issues](https://github.com/yourusername/GAL-Dreamer/issues)

---

**让我们一起用AI创造精彩的视觉小说世界！** 🎮✨
