"""
GAL-Dreamer 主 Pipeline
调用各个子模块完成完整流程
"""
import argparse
from typing import Optional, Dict, Any
from pathlib import Path

from utils.logger import log
from utils.config import config
from pipelines.worldbuilding.worldbuilding_pipeline import WorldbuildingPipeline
from pipelines.story_outline.story_outline_pipeline import StoryOutlinePipeline


class MainPipeline:
    """GAL-Dreamer 主 Pipeline"""

    def __init__(self):
        """初始化主 Pipeline"""
        self.modules = {
            "worldbuilding": WorldbuildingPipeline(),
            "story_outline": StoryOutlinePipeline(),
        }
        log.info("MainPipeline 初始化完成")

    def generate(
        self,
        user_idea: str = None,
        world_setting_path: str = None,
        modules: list = None,
        output_dir: Optional[str] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        执行完整或部分流程

        Args:
            user_idea: 用户创意描述 (worldbuilding模块需要)
            world_setting_path: 世界观JSON文件路径 (story_outline模块需要)
            modules: 要执行的模块列表，如 ["worldbuilding"]，None 表示执行所有模块
            output_dir: 输出目录
            show_progress: 是否显示进度
        """
        if modules is None:
            modules = list(self.modules.keys())

        if output_dir is None:
            output_dir = str(config.PROJECT_OUTPUT_DIR)

        results = {}
        world_setting_result = None

        for module_name in modules:
            if module_name not in self.modules:
                log.warning(f"模块 {module_name} 不存在，跳过")
                continue

            log.info(f"执行模块: {module_name}")
            module = self.modules[module_name]

            if module_name == "worldbuilding":
                if not user_idea:
                    log.error("worldbuilding模块需要user_idea参数")
                    continue
                result = module.generate(
                    user_idea=user_idea,
                    output_dir=output_dir,
                    show_progress=show_progress
                )
                world_setting_result = result

            elif module_name == "story_outline":
                # story_outline需要world_setting数据
                if world_setting_result:
                    # 使用刚生成的world_setting
                    result = module.generate(
                        world_setting_data=world_setting_result,
                        output_dir=output_dir,
                        show_progress=show_progress
                    )
                elif world_setting_path:
                    # 使用指定的world_setting文件
                    result = module.generate(
                        world_setting_path=world_setting_path,
                        output_dir=output_dir,
                        show_progress=show_progress
                    )
                else:
                    log.error("story_outline模块需要world_setting_path或先执行worldbuilding模块")
                    continue
            else:
                result = module.generate(
                    user_idea=user_idea,
                    output_dir=output_dir,
                    show_progress=show_progress
                )

            results[module_name] = result

        return results


def main():
    parser = argparse.ArgumentParser(description="GAL-Dreamer - 主Pipeline")
    parser.add_argument("idea", nargs='?', help="故事创意描述 (worldbuilding模块需要)")
    parser.add_argument("--world-setting", "-w", help="世界观JSON文件路径 (story_outline模块使用)")
    parser.add_argument("--modules", "-m", nargs="*",
                        choices=["worldbuilding", "story_outline"],
                        help="要执行的模块 (默认执行所有模块: worldbuilding, story_outline)")
    parser.add_argument("--output", "-o", help="输出目录")
    parser.add_argument("--no-progress", action="store_true", help="不显示进度条")

    args = parser.parse_args()

    # 如果没有指定模块，执行所有模块
    if not args.modules:
        args.modules = ["worldbuilding", "story_outline"]

    pipeline = MainPipeline()

    print("\n" + "=" * 60)
    print("GAL-Dreamer 主 Pipeline")
    print("=" * 60)
    if args.idea:
        print(f"输入创意: {args.idea[:100]}...")
    if args.world_setting:
        print(f"世界观文件: {args.world_setting}")
    print(f"执行模块: {', '.join(args.modules)}")
    print("=" * 60 + "\n")

    results = pipeline.generate(
        user_idea=args.idea,
        world_setting_path=args.world_setting,
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

        if module_name == "worldbuilding":
            world = final.get("world_setting", {})
            print(f"  世界观: {world.get('era', '')} - {world.get('location', '')}")
            print(f"  势力: {final.get('factions', {}).get('factions_count', 0)}个")
            print(f"  NPC: {final.get('factions', {}).get('npcs_count', 0)}个")

        elif module_name == "story_outline":
            premise = final.get("story_premise", {})
            print(f"  核心钩子: {premise.get('hook', '')}")
            print(f"  主类型: {premise.get('primary_genre', '')}")

            chars = final.get("character_arcs", {})
            protagonist = chars.get("protagonist", {})
            print(f"  主角: {protagonist.get('name', '')} ({protagonist.get('arc_type', '')}弧光)")
            print(f"  女主: {chars.get('heroines_count', 0)}个")
            for h in chars.get('heroines', []):
                print(f"    - {h.get('name', '')}: {h.get('arc_type', '')}弧光")

            conflict = final.get("conflict_engine", {})
            print(f"  主冲突: {conflict.get('main_conflicts_count', 0)}个")
            for mc in conflict.get('main_conflicts', []):
                print(f"    - {mc.get('name', '')} ({mc.get('type', '')})")
            print(f"  危机节点: {conflict.get('escalation_nodes_count', 0)}个")

    return results


if __name__ == "__main__":
    main()
