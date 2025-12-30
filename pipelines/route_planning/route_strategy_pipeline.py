"""
GAL-Dreamer 路线规划 Pipeline (Phase 1)
基于故事大纲JSON生成共通线章节规划
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from tqdm import tqdm

# Agents
from agents.route_planning.route_strategy_agent import RouteStrategyAgent

# 数据模型
from utils.logger import log
from utils.config import config


class RouteStrategyPipeline:
    """
    路线规划 Pipeline (Phase 1)

    基于故事大纲生成共通线章节规划

    Agent依赖关系:
    1. RouteStrategyAgent → 共通线章节规划（基于story_outline + world_setting）

    输入: 故事大纲JSON文件路径或数据
    输出: 路线战略JSON
    """

    def __init__(self):
        """初始化 Pipeline"""
        self.agents = {
            "route_strategy": RouteStrategyAgent(),
        }
        log.info("RouteStrategyPipeline 初始化完成")

    def generate(
        self,
        story_outline_path: Optional[str] = None,
        story_outline_data: Optional[Dict[str, Any]] = None,
        world_setting_path: Optional[str] = None,
        world_setting_data: Optional[Dict[str, Any]] = None,
        output_dir: Optional[str] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        生成路线战略规划

        Args:
            story_outline_path: 故事大纲JSON文件路径
            story_outline_data: 直接传入的故事大纲数据（如果提供则忽略path）
            world_setting_path: 世界观JSON文件路径
            world_setting_data: 直接传入的世界观数据（如果提供则忽略path）
            output_dir: 输出目录
            show_progress: 是否显示进度

        Returns:
            路线战略规划结果字典
        """
        # 加载故事大纲数据
        if story_outline_data:
            story_outline_json = story_outline_data
        elif story_outline_path:
            with open(story_outline_path, 'r', encoding='utf-8') as f:
                story_outline_json = json.load(f)
        else:
            raise ValueError("必须提供 story_outline_path 或 story_outline_data")

        # 加载世界观数据（必选）
        if world_setting_data:
            world_setting_json = world_setting_data
        elif world_setting_path:
            with open(world_setting_path, 'r', encoding='utf-8') as f:
                world_setting_json = json.load(f)
        else:
            raise ValueError("必须提供 world_setting_path 或 world_setting_data")

        # 验证故事大纲数据
        if "steps" not in story_outline_json:
            raise ValueError("story_outline_json必须包含steps字段")

        result = {
            "input": {
                "story_outline_source": story_outline_path or "direct_data",
                "world_setting_source": world_setting_path or "none",
                "user_idea": story_outline_json.get("input", {}).get("user_idea", "")
            },
            "steps": {},
            "final_output": {},
        }

        # 生成章节规划
        self._run_route_steps(story_outline_json, world_setting_json, result, show_progress)

        # 格式化最终输出
        result["final_output"] = self._format_output(result)

        # 保存结果
        if output_dir:
            self._save_results(result, output_dir)

        return result

    def _run_route_steps(self, story_outline_json: Dict, world_setting_json: Optional[Dict], result: Dict, show_progress: bool):
        """执行路线规划步骤"""
        steps = [
            ("1️⃣ 路线战略规划", "route_strategy", self._step_route_strategy),
        ]

        pbar = tqdm(steps, desc="RouteStrategyPipeline: 路线规划", disable=not show_progress)
        for step_name, step_key, step_func in pbar:
            pbar.set_description(f"{step_name}")
            try:
                step_result = step_func(story_outline_json, world_setting_json)
                result["steps"][step_key] = step_result
                pbar.write(f"✅ {step_name} 完成")
            except Exception as e:
                pbar.write(f"❌ {step_name} 失败: {e}")
                log.error(f"{step_name} 失败: {e}")
                raise

    def _step_route_strategy(self, story_outline_json: Dict, world_setting_json: Optional[Dict]) -> Dict[str, Any]:
        """步骤1: 路线战略规划（基于story_outline + world_setting）"""
        route_strategy = self.agents["route_strategy"].process(
            story_outline_data=story_outline_json,
            world_setting_data=world_setting_json
        )
        # 转为dict
        return route_strategy.model_dump() if hasattr(route_strategy, "model_dump") else route_strategy

    def _format_output(self, result: Dict) -> Dict[str, Any]:
        """格式化最终输出"""
        route_strategy = result["steps"]["route_strategy"]

        # 辅助函数
        def get_field(data, field, default=None):
            if hasattr(data, field):
                return getattr(data, field)
            elif isinstance(data, dict):
                return data.get(field, default)
            return default

        output = {
            "route_strategy": {
                "strategy_id": get_field(route_strategy, "strategy_id", ""),
                "source_outline": get_field(route_strategy, "source_outline", ""),
                "recommended_chapters": get_field(route_strategy, "recommended_chapters", 0),
                "heroine_count": get_field(route_strategy, "heroine_count", 0),
                "main_plot_summary": get_field(route_strategy, "main_plot_summary", ""),
            },
            "major_conflicts": get_field(route_strategy, "major_conflicts", []),
            "chapters": get_field(route_strategy, "chapters", []),
        }

        return output

    def _save_results(self, result: Dict, output_dir: str):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 使用时间戳目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_dir = output_path / timestamp
        timestamped_dir.mkdir(parents=True, exist_ok=True)

        json_file = timestamped_dir / "route_strategy.json"
        with open(json_file, "w", encoding="utf-8") as f:
            # 转换Pydantic对象为dict
            serializable_result = self._make_serializable(result)
            json.dump(serializable_result, f, ensure_ascii=False, indent=2, default=str)
        log.info(f"结果已保存到: {json_file}")

        return timestamped_dir

    def _make_serializable(self, obj: Any) -> Any:
        """递归转换Pydantic对象为可序列化的dict"""
        if hasattr(obj, "model_dump"):
            return self._make_serializable(obj.model_dump())
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        else:
            return obj


def main():
    import argparse

    parser = argparse.ArgumentParser(description="GAL-Dreamer - 路线规划生成")
    parser.add_argument("--story-outline", "-s", help="故事大纲JSON文件路径")
    parser.add_argument("--world-setting", "-w", help="世界观JSON文件路径（可选）")
    parser.add_argument("--output", "-o", help="输出目录", default="./output")
    parser.add_argument("--no-progress", action="store_true", help="不显示进度条")

    args = parser.parse_args()

    if not args.story_outline:
        # 尝试使用最新的故事大纲数据
        output_dir = Path(args.output)
        if output_dir.exists():
            import re
            timestamp_dirs = [d for d in output_dir.iterdir() if d.is_dir() and re.match(r"\d{8}_\d{6}", d.name)]

            if timestamp_dirs:
                latest_dir = sorted(timestamp_dirs)[-1]
                story_outline_path = latest_dir / "story_outline.json"
                if story_outline_path.exists():
                    args.story_outline = str(story_outline_path)
                    print(f"使用最新的故事大纲: {story_outline_path}")

                    # 同时尝试加载世界观
                    world_setting_path = latest_dir / "world_setting.json"
                    if world_setting_path.exists():
                        args.world_setting = str(world_setting_path)
                        print(f"使用世界观: {world_setting_path}")

    if not args.story_outline or not Path(args.story_outline).exists():
        print("错误: 请提供有效的故事大纲JSON文件路径")
        return 1

    pipeline = RouteStrategyPipeline()

    print("\n" + "=" * 60)
    print("GAL-Dreamer 路线规划生成 (Phase 1)")
    print("=" * 60)

    result = pipeline.generate(
        story_outline_path=args.story_outline,
        world_setting_path=args.world_setting,
        output_dir=args.output,
        show_progress=not args.no_progress
    )

    print("\n" + "=" * 60)
    print("生成完成!")
    print("=" * 60)

    final = result["final_output"]
    strategy = final["route_strategy"]

    print(f"\n📋 路线战略:")
    print(f"  战略ID: {strategy['strategy_id']}")
    print(f"  推荐章节数: {strategy['recommended_chapters']}")
    print(f"  女主数量: {strategy['heroine_count']}")
    print(f"  主线概要: {strategy['main_plot_summary']}")

    if final.get("major_conflicts"):
        print(f"\n🔥 大冲突: {len(final['major_conflicts'])}个")
        for idx, conflict in enumerate(final["major_conflicts"], 1):
            print(f"  {idx}. {conflict.get('name', '')} ({conflict.get('position_chapter', '')})")

    print(f"\n📖 章节数: {len(final['chapters'])}")

    return 0


if __name__ == "__main__":
    exit(main())
