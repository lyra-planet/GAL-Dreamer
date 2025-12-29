"""
GAL-Dreamer 主 Pipeline
调用各个子模块完成完整流程
"""
import argparse
from typing import Optional, Dict, Any
from pathlib import Path

from utils.logger import log
from utils.config import config
from pipelines.worldbuilding_pipeline import WorldbuildingPipeline


class MainPipeline:
    """GAL-Dreamer 主 Pipeline"""

    def __init__(self):
        """初始化主 Pipeline"""
        self.modules = {
            "worldbuilding": WorldbuildingPipeline(),
        }
        log.info("MainPipeline 初始化完成")

    def generate(
        self,
        user_idea: str,
        modules: list = None,
        output_dir: Optional[str] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        执行完整或部分流程

        Args:
            user_idea: 用户创意描述
            modules: 要执行的模块列表，如 ["worldbuilding"]，None 表示执行所有模块
            output_dir: 输出目录
            show_progress: 是否显示进度
        """
        if modules is None:
            modules = list(self.modules.keys())

        if output_dir is None:
            output_dir = str(config.PROJECT_OUTPUT_DIR)

        results = {}

        for module_name in modules:
            if module_name not in self.modules:
                log.warning(f"模块 {module_name} 不存在，跳过")
                continue

            log.info(f"执行模块: {module_name}")
            module = self.modules[module_name]

            result = module.generate(
                user_idea=user_idea,
                output_dir=output_dir,
                show_progress=show_progress
            )
            results[module_name] = result

        return results


def main():
    parser = argparse.ArgumentParser(description="GAL-Dreamer - 主Pipeline")
    parser.add_argument("idea", help="故事创意描述")
    parser.add_argument("--modules", "-m", nargs="+", default=["worldbuilding"],
                        choices=["worldbuilding"], help="要执行的模块")
    parser.add_argument("--output", "-o", help="输出目录")
    parser.add_argument("--no-progress", action="store_true", help="不显示进度条")

    args = parser.parse_args()

    pipeline = MainPipeline()

    print("\n" + "=" * 60)
    print("GAL-Dreamer 主 Pipeline")
    print("=" * 60)
    print(f"输入创意: {args.idea[:100]}...")
    print(f"执行模块: {', '.join(args.modules)}")
    print("=" * 60 + "\n")

    results = pipeline.generate(
        user_idea=args.idea,
        modules=args.modules,
        output_dir=args.output,
        show_progress=not args.no_progress
    )

    print("\n" + "=" * 60)
    print("全部完成!")
    print("=" * 60)

    for module_name, result in results.items():
        print(f"\n[{module_name}]")
        final = result.get("final_output", {})
        if "world_setting" in final:
            world = final["world_setting"]
            print(f"  世界观: {world.get('era')} - {world.get('location')}")

    return results


if __name__ == "__main__":
    main()
