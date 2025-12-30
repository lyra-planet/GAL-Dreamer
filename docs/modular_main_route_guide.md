# 模块化主线规划 (Modular Main Route Planning)

## 概述

模块化主线规划 Pipeline 将故事分为 **起承转合** 四个模块，每个模块最多 5 章，避免上下文过长导致的一致性问题。

## 架构

```
起 (Introduction)    - 第1-5章
承 (Development)     - 第6-15章
转 (Twist)           - 第16-22章
合 (Resolution)      - 第23-27章
```

## 文件结构

### 新增文件

```
agents/route_planning/
├── module_strategy_agent.py      # 四模块策略规划 Agent
└── modular_main_route_agent.py   # 模块化主线框架规划 Agent

prompts/route_planning/
├── module_strategy_prompt.py     # 四模块策略 Prompt
└── modular_main_route_prompt.py  # 模块化主线 Prompt

pipelines/route_planning/
└── modular_main_route_pipeline.py  # 模块化主线 Pipeline

tests/
└── test_modular_main_route.py    # 测试脚本
```

## 使用方法

### 命令行使用

```bash
# 基础使用（使用默认27章）
python -m pipelines.route_planning.modular_main_route_pipeline \
    --story-outline ./output/xxx/story_outline.json \
    --output ./output/modular_main_route

# 自定义章节数
python -m pipelines.route_planning.modular_main_route_pipeline \
    --story-outline ./output/xxx/story_outline.json \
    --chapters 30 \
    --output ./output/modular_main_route
```

### Python API 使用

```python
from pipelines.route_planning.modular_main_route_pipeline import ModularMainRoutePipeline

# 初始化 Pipeline
pipeline = ModularMainRoutePipeline()

# 生成主线框架
result = pipeline.generate(
    story_outline_data=story_outline_data,
    total_chapters=27,
    output_dir="./output/modular_main_route",
    fix_issues=True
)

# 获取结果
final_output = result["final_output"]
print(f"总章节数: {final_output['total_estimated_chapters']}")
print(f"章节数: {len(final_output['chapters'])}")
print(f"分支数: {len(final_output['branches'])}")
print(f"结局数: {len(final_output['endings'])}")
```

### 仅生成单个模块

```python
from agents.route_planning.modular_main_route_agent import ModularMainRouteAgent

agent = ModularMainRouteAgent()

# 生成"起"模块
module_framework = agent.process_module(
    story_outline_data=story_outline_data,
    module_name="起",
    module_type="introduction",
    chapter_start=1,
    chapter_end=5,
    module_strategy=module_strategy,
    user_idea=user_idea
)

print(f"生成章节: {len(module_framework.chapters)}")
```

## 流程说明

### 1. 四模块策略生成 (ModuleStrategyAgent)

根据故事大纲，生成四模块的整体策略：
- 每个模块的章节范围
- 主线剧情概要
- 分支设计方向
- 关键选择点
- 好感度变化范围

### 2. 逐个模块生成 (ModularMainRouteAgent)

每个模块独立生成：
- 继承前序模块的上下文
- 基于模块策略生成详细章节
- 生成本模块的分支和选择点
- 最多5章，保持上下文可控

### 3. 合并模块

将所有模块合并为完整框架：
- 合并所有章节
- 合并所有分支
- 合并所有结局
- 构建完整状态框架

### 4. 一致性检查 (RouteConsistencyAgent)

检查整体设计问题：
- 分支可达性
- 结局可达性
- 数值平衡
- 分支跨度

### 5. 修复循环 (RouteFixerAgent)

如有问题，进行修复：
- 最多3轮修复
- 支持模块级别修复
- 自动重新验证

## 输出文件

```
output/modular_main_route/
└── 20241230_120000/
    ├── modular_main_route_framework.json  # 完整主线框架
    ├── modules_detail.json                # 各模块详细数据
    ├── consistency_report.json            # 一致性检查报告
    └── full_result.json                   # 完整结果（包含所有中间步骤）
```

## 与原 Pipeline 对比

| 特性 | MainRoutePipeline | ModularMainRoutePipeline |
|------|-------------------|--------------------------|
| 章节组织 | 一次性生成全部 | 分四模块生成 |
| 单次上下文 | 15-27章 | 最多5章 |
| 策略规划 | 需要预先提供策略文本 | 自动生成四模块策略 |
| 一致性保证 | 上下文长可能导致不一致 | 模块间显式上下文传递 |
| 修复能力 | 整体修复 | 支持模块级别修复 |

## 四模块定义

### 起 (Introduction)
- **章节**: 1-5章
- **功能**: 世界观介绍、角色登场、核心悬念铺垫
- **好感度**: 0-20区间
- **特点**: 玩家初步接触各角色，建立第一印象

### 承 (Development)
- **章节**: 6-15章
- **功能**: 角色关系深入发展，角色弧光展开
- **好感度**: 20-50区间
- **特点**: 日常事件与主线推进交织

### 转 (Twist)
- **章节**: 16-22章
- **功能**: 核心冲突爆发，真相揭露
- **好感度**: 50-70区间
- **特点**: 关键抉择时刻，决定进入哪条角色线

### 合 (Resolution)
- **章节**: 23-27章
- **功能**: 各角色专属结局章节
- **好感度**: 最终结局确定
- **特点**: 包含真结局（如果条件满足）
