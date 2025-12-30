"""
GAL-Dreamer 模块化主线路线 Pipeline
基于四模块（起承转合）结构生成主线框架 - 支持分模块生成避免上下文过长
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from agents.route_planning.route_strategy_agent import RouteStrategyAgent
from agents.route_planning.module_strategy_agent import ModuleStrategyAgent
from agents.route_planning.modular_main_route_agent import ModularMainRouteAgent

from utils.logger import log
from utils.config import config


class ModularMainRoutePipeline:
    """
    模块化主线路线 Pipeline

    处理流程:
    1. RouteStrategyAgent → 生成整体路线战略意见
    2. ModuleStrategyAgent → 生成四模块策略（起承转合）
    3. ModularMainRouteAgent → 逐个生成各模块框架（每模块6-8章）
    4. 合并所有模块为完整框架

    输入: 故事大纲数据
    输出: 主线框架JSON
    """

    MIN_CHAPTERS_PER_MODULE = 6
    MAX_CHAPTERS_PER_MODULE = 8

    # 四模块定义
    MODULES = [
        {"name": "起", "type": "introduction", "default_chapters": 6},
        {"name": "承", "type": "development", "default_chapters": 8},
        {"name": "转", "type": "twist", "default_chapters": 8},
        {"name": "合", "type": "resolution", "default_chapters": 5},
    ]

    def __init__(self):
        """初始化 Pipeline"""
        self.agents = {
            "route_strategy": RouteStrategyAgent(),
            "module_strategy": ModuleStrategyAgent(),
            "modular_main_route": ModularMainRouteAgent(),
        }
        self.route_strategy = None
        self.module_strategies = {}
        self.module_frameworks = {}
        log.info("ModularMainRoutePipeline 初始化完成")

    def generate(
        self,
        story_outline_data: Dict[str, Any],
        total_chapters: int = 27,
        output_dir: Optional[str] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        生成主线框架

        Args:
            story_outline_data: 故事大纲数据
            total_chapters: 总章节数
            output_dir: 输出目录
            show_progress: 是否显示进度

        Returns:
            处理结果字典
        """
        user_idea = story_outline_data.get("input", {}).get("user_idea", "")
        source_outline = story_outline_data.get("structure_id", "unknown")

        result = {
            "input": {
                "user_idea": user_idea,
                "source_outline": source_outline,
                "total_chapters": total_chapters
            },
            "route_strategy": {},
            "module_strategies": {},
            "module_frameworks": {},
            "final_output": {},
        }

        # 0. 生成整体路线战略意见
        print("\n" + "=" * 60)
        print("📍 步骤0: 生成整体路线战略意见")
        print("=" * 60)

        route_strategy = self.agents["route_strategy"].process(
            story_outline_data=story_outline_data,
            user_idea=user_idea
        )
        result["route_strategy"] = route_strategy.model_dump()
        self.route_strategy = route_strategy.strategy_text
        self.main_plot_summary = route_strategy.main_plot_summary
        self.chapters = route_strategy.chapters

        # 使用RouteStrategy推荐的章节数
        recommended_chapters = route_strategy.recommended_chapters
        print(f"\n📊 RouteStrategy推荐章节数: {recommended_chapters}")

        # 1. 生成四模块策略
        print("\n" + "=" * 60)
        print("📍 步骤1: 生成四模块策略（起承转合）")
        print("=" * 60)

        strategy = self.agents["module_strategy"].process(
            story_outline_data=story_outline_data,
            user_idea=user_idea,
            total_chapters=recommended_chapters,
            route_strategy_text=self.route_strategy
        )
        result["module_strategies"]["strategy"] = strategy.model_dump()
        self.module_strategies = {m["module_name"]: m for m in strategy.modules}

        # 使用ModuleStrategy提供的章节分配
        module_allocation = []
        for m in strategy.modules:
            chapter_range = m.get("chapter_range", {})
            module_allocation.append({
                "name": m["module_name"],
                "type": m["module_type"],
                "chapters": m["chapter_count"],
                "start": chapter_range.get("start", 1),
                "end": chapter_range.get("end", m["chapter_count"])
            })
        result["module_allocation"] = module_allocation
        result["recommended_chapters"] = recommended_chapters

        # 2. 逐个生成各模块框架
        print("\n" + "=" * 60)
        print("📍 步骤2: 逐个生成各模块框架")
        print("=" * 60)

        global_state = None
        global_branches = []
        global_endings = []

        for module_info in module_allocation:
            module_name = module_info["name"]
            module_type = module_info["type"]
            chapter_start = module_info["start"]
            chapter_end = module_info["end"]

            print(f"\n--- 生成 {module_name} 模块（第{chapter_start}-{chapter_end}章）---")

            # 获取该模块的策略
            module_strategy = self.module_strategies.get(module_name, {})

            # 生成该模块框架
            module_framework = self.agents["modular_main_route"].process_module(
                story_outline_data=story_outline_data,
                module_name=module_name,
                module_type=module_type,
                chapter_start=chapter_start,
                chapter_end=chapter_end,
                module_strategy=module_strategy,
                global_state=global_state,
                global_branches=global_branches,
                global_endings=global_endings,
                user_idea=user_idea,
                route_strategy_text=self.route_strategy,
                main_plot_summary=self.main_plot_summary,
                chapters=self.chapters
            )

            # 保存模块框架
            self.module_frameworks[module_name] = module_framework
            result["module_frameworks"][module_name] = module_framework.model_dump()

            # 更新全局数据
            global_branches.extend(module_framework.branches)
            global_endings.extend(module_framework.endings)

            # 更新全局状态（合并状态转换）
            if not global_state:
                # 第一个模块，初始化状态
                global_state = self._initialize_state(module_framework)
            else:
                # 后续模块，更新状态范围
                global_state = self._update_state(global_state, module_framework)

        # 3. 合并所有模块为完整框架
        print("\n" + "=" * 60)
        print("📍 步骤3: 合并所有模块")
        print("=" * 60)

        complete_framework = self._merge_modules(global_state, global_branches, global_endings)
        result["final_output"] = complete_framework

        # 4. 保存结果
        if output_dir:
            self._save_results(result, output_dir)

        return result

    def _allocate_chapters(self, total_chapters: int) -> List[Dict[str, Any]]:
        """分配各模块的章节数，每个模块6-8章"""
        allocation = []

        # 计算默认章节总和
        default_total = sum(m["default_chapters"] for m in self.MODULES)

        for module_info in self.MODULES:
            name = module_info["name"]
            module_type = module_info["type"]
            default = module_info["default_chapters"]

            # 按比例分配，限制在6-8章范围内
            if default_total > 0:
                ratio = default / default_total
                chapters = max(
                    self.MIN_CHAPTERS_PER_MODULE,
                    min(self.MAX_CHAPTERS_PER_MODULE, int(total_chapters * ratio))
                )
            else:
                chapters = max(
                    self.MIN_CHAPTERS_PER_MODULE,
                    min(self.MAX_CHAPTERS_PER_MODULE, total_chapters // 4)
                )

            allocation.append({
                "name": name,
                "type": module_type,
                "chapters": chapters
            })

        # 调整总数匹配
        allocated_total = sum(m["chapters"] for m in allocation)
        diff = total_chapters - allocated_total

        # 将差异分配给"承"模块（通常是主要剧情部分）
        if diff != 0:
            for module in allocation:
                if module["name"] == "承":
                    new_chapters = module["chapters"] + diff
                    # 确保不超过范围
                    if self.MIN_CHAPTERS_PER_MODULE <= new_chapters <= self.MAX_CHAPTERS_PER_MODULE:
                        module["chapters"] = new_chapters
                        diff = 0
                    break

        # 如果还有差异，分配给"转"模块
        if diff != 0:
            for module in allocation:
                if module["name"] == "转":
                    new_chapters = module["chapters"] + diff
                    if self.MIN_CHAPTERS_PER_MODULE <= new_chapters <= self.MAX_CHAPTERS_PER_MODULE:
                        module["chapters"] = new_chapters
                    break

        return allocation

    def _initialize_state(self, framework: Any) -> Dict[str, Any]:
        """初始化状态框架（从第一个模块）"""
        state = {}
        state_transitions = framework.state_transitions if hasattr(framework, "state_transitions") else {}

        for heroine_id, transition in state_transitions.items():
            state[heroine_id] = {
                "initial": transition.get("min_in", 0),
                "min": 0,
                "max": 100,
                "description": f"{heroine_id}好感度"
            }

        # 如果没有状态转换，创建默认状态
        if not state:
            state = {
                "heroine_001": {"initial": 0, "min": 0, "max": 100, "description": "女主1好感度"}
            }

        return state

    def _update_state(self, global_state: Dict[str, Any], framework: Any) -> Dict[str, Any]:
        """更新全局状态范围"""
        state_transitions = framework.state_transitions if hasattr(framework, "state_transitions") else {}

        for heroine_id, transition in state_transitions.items():
            if heroine_id not in global_state:
                global_state[heroine_id] = {
                    "initial": 0,
                    "min": 0,
                    "max": 100,
                    "description": f"{heroine_id}好感度"
                }

        return global_state

    def _merge_modules(
        self,
        global_state: Dict[str, Any],
        global_branches: List[Dict[str, Any]],
        global_endings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """合并所有模块为完整框架"""
        all_chapters = self.agents["modular_main_route"].get_all_chapters()

        # 构建完整框架
        framework = {
            "structure_id": f"modular_main_route_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "source_outline": "",
            "total_estimated_chapters": len(all_chapters),
            "common_ratio": 0.7,
            "state": global_state,
            "branches": global_branches,
            "endings": global_endings,
            "chapters": all_chapters
        }

        return framework

    def _save_results(self, result: Dict, output_dir: str):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_dir = output_path / timestamp
        timestamped_dir.mkdir(parents=True, exist_ok=True)

        # 保存主线框架
        route_file = timestamped_dir / "modular_main_route_framework.json"
        final_output = result.get("final_output", {})
        with open(route_file, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)
        log.info(f"模块化主线框架已保存到: {route_file}")

        # 保存各模块详细数据
        modules_file = timestamped_dir / "modules_detail.json"
        with open(modules_file, 'w', encoding='utf-8') as f:
            json.dump(result.get("module_frameworks", {}), f, ensure_ascii=False, indent=2)
        log.info(f"模块详细数据已保存到: {modules_file}")

        # 保存完整结果
        full_file = timestamped_dir / "full_result.json"
        with open(full_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        log.info(f"完整结果已保存到: {full_file}")

        return timestamped_dir


def main():
    import argparse

    parser = argparse.ArgumentParser(description="GAL-Dreamer - 模块化主线路线生成")
    parser.add_argument("--story-outline", "-s", help="故事大纲JSON文件路径")
    parser.add_argument("--chapters", "-c", type=int, default=27, help="总章节数（默认27章）")
    parser.add_argument("--output", "-o", help="输出目录", default="./output/modular_main_route")

    args = parser.parse_args()

    if not args.story_outline:
        # 尝试使用最新的故事大纲
        output_dir = Path("./output")
        if output_dir.exists():
            import re
            timestamp_dirs = [d for d in output_dir.iterdir() if d.is_dir() and re.match(r"\d{8}_\d{6}", d.name)]

            if timestamp_dirs:
                latest_dir = sorted(timestamp_dirs)[-1]
                outline_path = latest_dir / "story_outline.json"
                if outline_path.exists():
                    args.story_outline = str(outline_path)
                    print(f"使用最新的故事大纲: {outline_path}")

    if not args.story_outline or not Path(args.story_outline).exists():
        print("错误: 请提供有效的故事大纲JSON文件路径")
        return 1

    # 加载数据
    with open(args.story_outline, 'r', encoding='utf-8') as f:
        story_outline_data = json.load(f)

    pipeline = ModularMainRoutePipeline()

    print("\n" + "=" * 60)
    print("GAL-Dreamer 模块化主线路线生成")
    print("=" * 60)

    result = pipeline.generate(
        story_outline_data=story_outline_data,
        total_chapters=args.chapters,
        output_dir=args.output
    )

    print("\n" + "=" * 60)
    print("生成完成!")
    print("=" * 60)

    final = result.get("final_output", {})

    print(f"\n📋 结构ID: {final.get('structure_id')}")
    print(f"📋 预计总章节: {final.get('total_estimated_chapters')}章")
    print(f"📋 共通线占比: {final.get('common_ratio')*100:.0f}%")
    print(f"📋 章节数: {len(final.get('chapters', []))}")
    print(f"📋 分支数: {len(final.get('branches', []))}")
    print(f"📋 结局数: {len(final.get('endings', []))}")

    # 显示各模块统计
    print("\n📊 各模块统计:")
    for module_name, framework in result.get("module_frameworks", {}).items():
        print(f"  {module_name}模块: {len(framework.get('chapters', []))}章, "
              f"{len(framework.get('branches', []))}分支")

    return 0


if __name__ == "__main__":
    exit(main())
