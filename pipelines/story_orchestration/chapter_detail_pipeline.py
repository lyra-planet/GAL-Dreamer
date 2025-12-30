"""
GAL-Dreamer 章节剧情细化 Pipeline (Phase 2)
基于路线战略规划生成每章的具体剧情内容
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from tqdm import tqdm

# Agents
from agents.story_orchestration.chapter_detail_agent import ChapterDetailAgent

# 数据模型
from utils.logger import log
from utils.config import config


class ChapterDetailPipeline:
    """
    章节剧情细化 Pipeline (Phase 2)

    基于路线战略规划生成每章的具体剧情内容

    Agent依赖关系:
    1. ChapterDetailAgent → 章节详情（逐章生成）

    输入: 路线战略JSON + 故事大纲JSON + 世界观JSON
    输出: 章节详情JSON
    """

    def __init__(self):
        """初始化 Pipeline"""
        self.agents = {
            "chapter_detail": ChapterDetailAgent(),
        }
        log.info("ChapterDetailPipeline 初始化完成")

    def generate(
        self,
        route_strategy_path: Optional[str] = None,
        route_strategy_data: Optional[Dict[str, Any]] = None,
        story_outline_path: Optional[str] = None,
        story_outline_data: Optional[Dict[str, Any]] = None,
        world_setting_path: Optional[str] = None,
        world_setting_data: Optional[Dict[str, Any]] = None,
        output_dir: Optional[str] = None,
        show_progress: bool = True,
        start_chapter: int = 1,
        end_chapter: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        生成章节详情

        Args:
            route_strategy_path: 路线战略JSON文件路径
            route_strategy_data: 直接传入的路线战略数据
            story_outline_path: 故事大纲JSON文件路径
            story_outline_data: 直接传入的故事大纲数据
            world_setting_path: 世界观JSON文件路径
            world_setting_data: 直接传入的世界观数据
            output_dir: 输出目录
            show_progress: 是否显示进度
            start_chapter: 起始章节（默认1）
            end_chapter: 结束章节（默认全部）

        Returns:
            章节详情结果字典
        """
        # 加载路线战略数据
        if route_strategy_data:
            route_strategy_json = route_strategy_data
        elif route_strategy_path:
            with open(route_strategy_path, 'r', encoding='utf-8') as f:
                route_strategy_json = json.load(f)
        else:
            raise ValueError("必须提供 route_strategy_path 或 route_strategy_data")

        # 加载故事大纲数据
        if story_outline_data:
            story_outline_json = story_outline_data
        elif story_outline_path:
            with open(story_outline_path, 'r', encoding='utf-8') as f:
                story_outline_json = json.load(f)
        else:
            raise ValueError("必须提供 story_outline_path 或 story_outline_data")

        # 加载世界观数据
        if world_setting_data:
            world_setting_json = world_setting_data
        elif world_setting_path:
            with open(world_setting_path, 'r', encoding='utf-8') as f:
                world_setting_json = json.load(f)
        else:
            raise ValueError("必须提供 world_setting_path 或 world_setting_data")

        # 提取章节规划
        route_strategy = route_strategy_json.get("steps", {}).get("route_strategy", {})
        chapters = route_strategy.get("chapters", [])
        if not chapters:
            raise ValueError("路线战略中缺少章节规划")

        # 确定生成范围
        if end_chapter is None:
            end_chapter = len(chapters)
        else:
            end_chapter = min(end_chapter, len(chapters))

        target_chapters = chapters[start_chapter - 1:end_chapter]

        result = {
            "input": {
                "route_strategy_source": route_strategy_path or "direct_data",
                "story_outline_source": story_outline_path or "direct_data",
                "world_setting_source": world_setting_path or "direct_data",
                "user_idea": route_strategy_json.get("input", {}).get("user_idea", "")
            },
            "steps": {},
            "final_output": {},
        }

        # 生成章节详情
        self._run_chapter_steps(
            target_chapters, route_strategy_json, story_outline_json, world_setting_json, result, show_progress
        )

        # 格式化最终输出
        result["final_output"] = self._format_output(result)

        # 保存结果
        if output_dir:
            self._save_results(result, output_dir)

        return result

    def _run_chapter_steps(
        self, chapters: list, route_strategy_json: Dict, story_outline_json: Dict,
        world_setting_json: Dict, result: Dict, show_progress: bool
    ):
        """执行章节生成步骤"""
        agent = self.agents["chapter_detail"]

        # 创建临时保存目录
        temp_save_dir = Path(result.get("temp_save_dir", "./temp_chapters"))
        temp_save_dir.mkdir(parents=True, exist_ok=True)
        result["temp_save_dir"] = str(temp_save_dir)

        pbar = tqdm(chapters, desc="ChapterDetailPipeline: 章节生成", disable=not show_progress)
        for chapter_plan in pbar:
            chapter_num = chapter_plan.get("chapter", 0)
            chapter_id = chapter_plan.get("id", "")
            pbar.set_description(f"第{chapter_num}章 ({chapter_id})")

            try:
                # 获取前一章节
                previous_chapter = agent.get_previous_chapter(chapter_id)
                if not previous_chapter:
                    previous_chapter = None

                chapter_detail = agent.process(
                    chapter_plan=chapter_plan,
                    route_strategy_data=route_strategy_json,
                    story_outline_data=story_outline_json,
                    world_setting_data=world_setting_json,
                    previous_chapter=previous_chapter
                )

                result["steps"][chapter_id] = chapter_detail.model_dump()
                pbar.write(f"✅ 第{chapter_num}章 完成 ({len(chapter_detail.scenes)}幕)")

                # 立即保存当前章节
                chapter_file = temp_save_dir / f"{chapter_id}.json"
                with open(chapter_file, "w", encoding="utf-8") as f:
                    json.dump(chapter_detail.model_dump(), f, ensure_ascii=False, indent=2)
                pbar.write(f"   💾 已保存: {chapter_file}")

            except Exception as e:
                pbar.write(f"❌ 第{chapter_num}章 失败: {e}")
                log.error(f"第{chapter_num}章 失败: {e}")
                raise

    def _format_output(self, result: Dict) -> Dict[str, Any]:
        """格式化最终输出"""
        output = {
            "total_chapters": len(result["steps"]),
            "chapters": []
        }

        for chapter_id, chapter_detail in result["steps"].items():
            chapter_info = {
                "chapter": chapter_detail.get("chapter", 0),
                "chapter_id": chapter_detail.get("chapter_id", ""),
                "scene_count": len(chapter_detail.get("scenes", [])),
                "scenes": []
            }

            for scene in chapter_detail.get("scenes", []):
                scene_info = {
                    "scene": scene.get("scene", 0),
                    "title": scene.get("title", ""),
                    "location": scene.get("location", ""),
                    "time_of_day": scene.get("time_of_day", ""),
                    "event_count": len(scene.get("events", []))
                }
                chapter_info["scenes"].append(scene_info)

            output["chapters"].append(chapter_info)

        return output

    def _save_results(self, result: Dict, output_dir: str):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 使用时间戳目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_dir = output_path / timestamp
        timestamped_dir.mkdir(parents=True, exist_ok=True)

        json_file = timestamped_dir / "chapter_details.json"
        with open(json_file, "w", encoding="utf-8") as f:
            serializable_result = self._make_serializable(result)
            json.dump(serializable_result, f, ensure_ascii=False, indent=2, default=str)
        log.info(f"结果已保存到: {json_file}")

        # 章节目录：从临时目录复制已保存的章节文件
        chapters_dir = timestamped_dir / "chapters"
        chapters_dir.mkdir(parents=True, exist_ok=True)

        # 从临时目录复制章节文件
        temp_save_dir = result.get("temp_save_dir")
        if temp_save_dir:
            temp_path = Path(temp_save_dir)
            if temp_path.exists():
                import shutil
                for chapter_file in temp_path.glob("*.json"):
                    dest_file = chapters_dir / chapter_file.name
                    shutil.copy2(chapter_file, dest_file)

        log.info(f"章节文件已保存到: {chapters_dir}")

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

    parser = argparse.ArgumentParser(description="GAL-Dreamer - 章节剧情细化生成")
    parser.add_argument("--route-strategy", "-r", help="路线战略JSON文件路径")
    parser.add_argument("--story-outline", "-s", help="故事大纲JSON文件路径")
    parser.add_argument("--world-setting", "-w", help="世界观JSON文件路径")
    parser.add_argument("--output", "-o", help="输出目录", default="./output")
    parser.add_argument("--start", "-st", type=int, default=1, help="起始章节")
    parser.add_argument("--end", "-e", type=int, help="结束章节")
    parser.add_argument("--no-progress", action="store_true", help="不显示进度条")

    args = parser.parse_args()

    # 自动使用固定目录的文件
    base_dir = Path("/Users/lyra/Desktop/GAL-Dreamer/output/20251230_050843")

    if not args.route_strategy:
        route_strategy_path = base_dir / "route_strategy.json"
        if route_strategy_path.exists():
            args.route_strategy = str(route_strategy_path)
            print(f"使用路线战略: {route_strategy_path}")
        else:
            print(f"错误: 找不到 {route_strategy_path}")

    if not args.story_outline:
        story_outline_path = base_dir / "story_outline.json"
        if story_outline_path.exists():
            args.story_outline = str(story_outline_path)
            print(f"使用故事大纲: {story_outline_path}")
        else:
            print(f"错误: 找不到 {story_outline_path}")

    if not args.world_setting:
        world_setting_path = base_dir / "world_setting.json"
        if world_setting_path.exists():
            args.world_setting = str(world_setting_path)
            print(f"使用世界观: {world_setting_path}")
        else:
            print(f"错误: 找不到 {world_setting_path}")

    # 验证必需参数
    if not args.route_strategy or not Path(args.route_strategy).exists():
        print("错误: 请提供有效的路线战略JSON文件路径")
        return 1
    if not args.story_outline or not Path(args.story_outline).exists():
        print("错误: 请提供有效的故事大纲JSON文件路径")
        return 1
    if not args.world_setting or not Path(args.world_setting).exists():
        print("错误: 请提供有效的世界观JSON文件路径")
        return 1

    pipeline = ChapterDetailPipeline()

    print("\n" + "=" * 60)
    print("GAL-Dreamer 章节剧情细化生成 (Phase 2)")
    print("=" * 60)

    result = pipeline.generate(
        route_strategy_path=args.route_strategy,
        story_outline_path=args.story_outline,
        world_setting_path=args.world_setting,
        output_dir=args.output,
        show_progress=not args.no_progress,
        start_chapter=args.start,
        end_chapter=args.end
    )

    print("\n" + "=" * 60)
    print("生成完成!")
    print("=" * 60)

    final = result["final_output"]
    print(f"\n📖 总章节数: {final['total_chapters']}")

    for chapter in final["chapters"]:
        print(f"  第{chapter['chapter']}章: {len(chapter['scenes'])}幕")

    return 0


if __name__ == "__main__":
    exit(main())
