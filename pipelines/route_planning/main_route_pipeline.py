"""
GAL-Dreamer 主线路线 Pipeline
基于策略文本生成主线框架 - 包含MainRouteAgent + 检查修复循环
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from tqdm import tqdm

# Agents
from agents.route_planning.main_route_agent import MainRouteAgent
from agents.route_planning.route_consistency_agent import RouteConsistencyAgent
from agents.route_planning.route_fixer_agent import RouteFixerAgent

# 数据模型
from utils.logger import log
from utils.config import config


class MainRoutePipeline:
    """
    主线路线 Pipeline

    处理流程:
    1. MainRouteAgent      → 生成主线框架（基于策略文本）
    2. RouteConsistencyAgent → 检查路线设计问题
    3. RouteFixerAgent      → 修复问题（循环直到无关键问题）

    输入: 故事大纲数据 + 策略文本
    输出: 修复后的主线框架JSON
    """

    MAX_FIX_ROUNDS = 3

    def __init__(self):
        """初始化 Pipeline"""
        self.agents = {
            "main_route": MainRouteAgent(),
            "consistency": RouteConsistencyAgent(),
            "fixer": RouteFixerAgent(),
        }
        log.info("MainRoutePipeline 初始化完成")

    def generate(
        self,
        story_outline_data: Dict[str, Any],
        strategy_text: str,
        output_dir: Optional[str] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        生成主线框架

        Args:
            story_outline_data: 故事大纲数据
            strategy_text: 路线策略文本
            output_dir: 输出目录
            show_progress: 是否显示进度

        Returns:
            处理结果字典
        """
        user_idea = story_outline_data.get("input", {}).get("user_idea", "")

        result = {
            "input": {
                "user_idea": user_idea,
                "source_outline": story_outline_data.get("structure_id", "unknown")
            },
            "steps": {},
            "fix_history": [],
            "final_output": {},
        }

        # 1. 生成主线框架
        print("\n" + "=" * 60)
        print("📍 步骤1: 生成主线框架")
        print("=" * 60)

        main_route = self.agents["main_route"].process(
            story_outline_data=story_outline_data,
            strategy_text=strategy_text,
            user_idea=user_idea
        )
        result["steps"]["main_route"] = main_route

        # 2. 一致性检查
        print("\n" + "=" * 60)
        print("📍 步骤2: 路线一致性检查")
        print("=" * 60)

        route_dict = main_route.model_dump() if hasattr(main_route, "model_dump") else main_route
        consistency_report = self.agents["consistency"].process(route_framework=route_dict)
        result["steps"]["consistency"] = consistency_report

        # 3. 修复循环
        critical_issues = self._get_critical_issues(consistency_report)
        high_issues = self._get_high_issues(consistency_report)

        if critical_issues or high_issues:
            print(f"\n🔧 发现{len(critical_issues)}个关键问题，{len(high_issues)}个高优先级问题，开始修复循环...")
            result = self._run_fix_loop(route_dict, result, show_progress)
            route_dict = result["final_output"]
        else:
            print("\n✅ 无需要修复的问题")
            result["final_output"] = route_dict

        # 4. 保存结果
        if output_dir:
            self._save_results(result, output_dir)

        return result

    def _run_fix_loop(self, route_dict: Dict, result: Dict, show_progress: bool) -> Dict:
        """执行修复循环"""
        fix_round = 0
        current_route = route_dict

        while fix_round < self.MAX_FIX_ROUNDS:
            consistency_report = result["steps"]["consistency"]
            critical_issues = self._get_critical_issues(consistency_report)
            high_issues = self._get_high_issues(consistency_report)

            # 退出条件：无critical和high问题
            if len(critical_issues) == 0 and len(high_issues) == 0:
                log.info("修复完成：无关键或高优先级问题")
                break

            fix_round += 1
            print(f"\n🔧 第{fix_round}轮修复...")

            # 执行修复
            all_issues = critical_issues + high_issues
            fixed_route = self.agents["fixer"].process(
                route_framework=current_route,
                issues=all_issues
            )

            # 记录修复历史
            result["fix_history"].append({
                "round": fix_round,
                "issues_count": len(all_issues),
                "fix_count": fixed_route.get("fix_count", len(all_issues))
            })

            # 重新检查
            print("   重新检查...")
            new_report = self.agents["consistency"].process(route_framework=fixed_route)
            result["steps"]["consistency"] = new_report

            # 更新当前路线
            current_route = fixed_route
            result["final_output"] = current_route

            # 显示进度
            new_critical = self._get_critical_issues(new_report)
            new_high = self._get_high_issues(new_report)
            print(f"   修复后: {len(new_critical)}个关键问题, {len(new_high)}个高优先级问题")

            if len(new_critical) == 0 and len(new_high) == 0:
                print("   修复完成，结束循环")
                break

        if fix_round >= self.MAX_FIX_ROUNDS:
            print(f"\n⚠️ 已达到最大修复轮次({self.MAX_FIX_ROUNDS})")

        return result

    def _get_critical_issues(self, report: Dict) -> list:
        """获取关键问题列表"""
        issues = report.get("issues", []) if isinstance(report, dict) else []
        return [i for i in issues if i.get("severity") == "critical"]

    def _get_high_issues(self, report: Dict) -> list:
        """获取高优先级问题列表"""
        issues = report.get("issues", []) if isinstance(report, dict) else []
        return [i for i in issues if i.get("severity") == "high"]

    def _save_results(self, result: Dict, output_dir: str):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 使用时间戳目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_dir = output_path / timestamp
        timestamped_dir.mkdir(parents=True, exist_ok=True)

        # 保存主线框架
        route_file = timestamped_dir / "main_route_framework.json"
        final_output = result.get("final_output", {})
        with open(route_file, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)
        log.info(f"主线框架已保存到: {route_file}")

        # 保存检查报告
        consistency = result["steps"].get("consistency")
        if consistency:
            report_file = timestamped_dir / "consistency_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                report_dict = consistency.model_dump() if hasattr(consistency, "model_dump") else consistency
                json.dump(report_dict, f, ensure_ascii=False, indent=2)
            log.info(f"检查报告已保存到: {report_file}")

        # 保存完整结果
        full_file = timestamped_dir / "full_result.json"
        with open(full_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        log.info(f"完整结果已保存到: {full_file}")

        return timestamped_dir


def main():
    import argparse

    parser = argparse.ArgumentParser(description="GAL-Dreamer - 主线路线生成")
    parser.add_argument("--story-outline", "-s", help="故事大纲JSON文件路径")
    parser.add_argument("--strategy", "-t", help="路线策略文本文件路径")
    parser.add_argument("--output", "-o", help="输出目录", default="./output/main_route")
    parser.add_argument("--no-progress", action="store_true", help="不显示进度条")

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

    if not args.strategy:
        # 尝试使用默认路径
        default_strategy = "./output/route_strategy_test/route_strategy.txt"
        if Path(default_strategy).exists():
            args.strategy = default_strategy
            print(f"使用默认策略文件: {default_strategy}")

    if not args.story_outline or not Path(args.story_outline).exists():
        print("错误: 请提供有效的故事大纲JSON文件路径")
        return 1

    # 加载数据
    with open(args.story_outline, 'r', encoding='utf-8') as f:
        story_outline_data = json.load(f)

    strategy_text = ""
    if args.strategy and Path(args.strategy).exists():
        with open(args.strategy, 'r', encoding='utf-8') as f:
            content = f.read()
            # 跳过前两行（战略ID和来源大纲）
            lines = content.split('\n')
            if len(lines) > 2:
                strategy_text = '\n'.join(lines[2:])
            else:
                strategy_text = content

    pipeline = MainRoutePipeline()

    print("\n" + "=" * 60)
    print("GAL-Dreamer 主线路线生成")
    print("=" * 60)

    result = pipeline.generate(
        story_outline_data=story_outline_data,
        strategy_text=strategy_text,
        output_dir=args.output,
        show_progress=not args.no_progress
    )

    print("\n" + "=" * 60)
    print("生成完成!")
    print("=" * 60)

    final = result.get("final_output", {})
    consistency = result["steps"].get("consistency", {})

    print(f"\n📋 结构ID: {final.get('structure_id')}")
    print(f"📋 预计总章节: {final.get('total_estimated_chapters')}章")
    print(f"📋 共通线占比: {final.get('common_ratio')*100:.0f}%")
    print(f"📋 章节数: {len(final.get('chapters', []))}")
    print(f"📋 分支数: {len(final.get('branches', []))}")
    print(f"📋 结局数: {len(final.get('endings', []))}")

    consistency_status = consistency.get("overall_status") if isinstance(consistency, dict) else getattr(consistency, "overall_status", "unknown")
    consistency_issues = consistency.get("total_issues") if isinstance(consistency, dict) else getattr(consistency, "total_issues", 0)
    print(f"\n📊 检查状态: {consistency_status}")
    print(f"📊 问题数: {consistency_issues}")

    return 0


if __name__ == "__main__":
    exit(main())
