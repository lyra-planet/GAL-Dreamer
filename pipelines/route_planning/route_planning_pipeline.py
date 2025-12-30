"""
Route Planning Pipeline
路线规划 Pipeline (Phase 1)
基于故事大纲生成路线结构和情绪曲线
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from tqdm import tqdm

# Agents
from agents.route_planning.route_structure_agent import RouteStructureAgent
from agents.route_planning.common_route_agent import CommonRouteAgent
from agents.route_planning.heroine_route_agent import HeroineRouteAgent
from agents.route_planning.true_route_agent import TrueRouteAgent
from agents.route_planning.pacing_atmosphere_agent import PacingAtmosphereAgent

# 数据模型
from utils.logger import log
from utils.config import config
from models.route_planning.route_structure import RouteStructure
from models.route_planning.detailed_route import DetailedRoutePlan, DetailedCommonRoute, DetailedHeroineRoute, DetailedTrueRoute
from models.route_planning.mood_curve import MoodCurve


class RoutePlanningPipeline:
    """
    路线规划 Pipeline (Phase 1)

    Agent依赖关系:
    1. RouteStructureAgent      → 路线结构框架规划
    2. CommonRouteAgent         → 共通线详细内容
    3. HeroineRouteAgent (xN)   → 每个女主的个人线详细内容
    4. TrueRouteAgent           → 真结局路线详细内容
    5. PacingAtmosphereAgent    → 节奏与情绪曲线设计

    输入: 故事大纲JSON文件路径或数据
    输出: routes.json
    """

    def __init__(self):
        """初始化 Pipeline"""
        self.agents = {
            "route_structure": RouteStructureAgent(),
            "common_route": CommonRouteAgent(),
            "heroine_route": HeroineRouteAgent(),
            "true_route": TrueRouteAgent(),
            "pacing_atmosphere": PacingAtmosphereAgent(),
        }
        log.info("RoutePlanningPipeline 初始化完成")

    def generate(
        self,
        story_outline_path: Optional[str] = None,
        story_outline_data: Optional[Dict[str, Any]] = None,
        output_dir: Optional[str] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        生成路线规划

        Args:
            story_outline_path: 故事大纲JSON文件路径
            story_outline_data: 直接传入的故事大纲数据
            output_dir: 输出目录
            show_progress: 是否显示进度

        Returns:
            路线规划结果字典
        """
        # 加载故事大纲数据
        if story_outline_data:
            outline_data = story_outline_data
        elif story_outline_path:
            with open(story_outline_path, 'r', encoding='utf-8') as f:
                outline_data = json.load(f)
        else:
            raise ValueError("必须提供 story_outline_path 或 story_outline_data")

        # 验证数据结构
        if "steps" not in outline_data:
            raise ValueError("story_outline_data必须包含steps字段")

        user_idea = outline_data.get("input", {}).get("user_idea", "")

        result = {
            "input": {
                "story_outline_source": story_outline_path or "direct_data",
                "user_idea": user_idea
            },
            "steps": {},
            "final_output": {},
        }

        # 步骤列表（动态生成，取决于 heroine 数量）
        steps_list = self._build_steps_list(outline_data)
        pbar = tqdm(steps_list, desc="RoutePlanningPipeline", disable=not show_progress)

        for step_name, step_key, step_func in pbar:
            pbar.set_description(f"{step_name}")
            try:
                step_result = step_func(outline_data, result, user_idea)
                result["steps"][step_key] = step_result
                pbar.write(f"✅ {step_name} 完成")
            except Exception as e:
                pbar.write(f"❌ {step_name} 失败: {e}")
                log.error(f"{step_name} 失败: {e}")
                raise

        # 格式化最终输出
        result["final_output"] = self._format_output(result)

        # 保存结果
        if output_dir:
            self._save_results(result, output_dir)

        return result

    def _build_steps_list(self, outline_data: Dict[str, Any]) -> list:
        """根据女主数量构建步骤列表"""
        steps = outline_data.get("steps", {})
        cast_arc = steps.get("cast_arc", {})
        heroines = cast_arc.get("heroines", [])

        base_steps = [
            ("1️⃣ 路线结构规划", "route_structure", self._step_route_structure),
            ("2️⃣ 共通线生成", "common_route", self._step_common_route),
        ]

        # 添加每个女主的个人线
        for i, heroine in enumerate(heroines):
            heroine_name = heroine.get("character_name", f"女主{i+1}")
            base_steps.append((
                f"3️⃣-{i+1} {heroine_name}个人线",
                f"heroine_route_{i}",
                lambda data, result, idea, idx=i: self._step_heroine_route(data, result, idea, idx)
            ))

        base_steps.extend([
            ("4️⃣ 真结局路线", "true_route", self._step_true_route),
            ("5️⃣ 节奏与情绪", "mood_curve", self._step_mood_curve),
        ])

        return base_steps

    def _step_route_structure(
        self,
        story_outline_data: Dict[str, Any],
        result: Dict[str, Any],
        user_idea: str
    ) -> RouteStructure:
        """步骤1: 路线结构框架规划"""
        structure = self.agents["route_structure"].process(
            story_outline_data=story_outline_data,
            user_idea=user_idea
        )
        return structure

    def _step_common_route(
        self,
        story_outline_data: Dict[str, Any],
        result: Dict[str, Any],
        user_idea: str
    ) -> DetailedCommonRoute:
        """步骤2: 共通线详细内容"""
        structure = result["steps"]["route_structure"]
        structure_dict = structure.model_dump() if hasattr(structure, "model_dump") else structure

        common_route = self.agents["common_route"].process(
            story_outline_data=story_outline_data,
            structure_framework=structure_dict,
            user_idea=user_idea
        )
        return common_route

    def _step_heroine_route(
        self,
        story_outline_data: Dict[str, Any],
        result: Dict[str, Any],
        user_idea: str,
        heroine_index: int
    ) -> DetailedHeroineRoute:
        """步骤3: 个人路线详细内容"""
        structure = result["steps"]["route_structure"]
        structure_dict = structure.model_dump() if hasattr(structure, "model_dump") else structure

        # 获取对应的女主框架和弧光
        heroine_frameworks = structure_dict.get("heroine_route_frameworks", [])
        if heroine_index >= len(heroine_frameworks):
            raise ValueError(f"女主索引{heroine_index}超出范围")

        route_framework = heroine_frameworks[heroine_index]

        # 获取女主弧光数据
        steps = story_outline_data.get("steps", {})
        cast_arc = steps.get("cast_arc", {})
        heroines = cast_arc.get("heroines", [])

        heroine_id = route_framework.get("heroine_id", "")
        heroine_arc = next((h for h in heroines if h.get("character_id") == heroine_id), heroines[heroine_index] if heroine_index < len(heroines) else {})

        heroine_route = self.agents["heroine_route"].process(
            story_outline_data=story_outline_data,
            route_framework=route_framework,
            heroine_arc=heroine_arc,
            user_idea=user_idea
        )
        return heroine_route

    def _step_true_route(
        self,
        story_outline_data: Dict[str, Any],
        result: Dict[str, Any],
        user_idea: str
    ) -> Optional[DetailedTrueRoute]:
        """步骤4: 真结局路线详细内容"""
        structure = result["steps"]["route_structure"]
        structure_dict = structure.model_dump() if hasattr(structure, "model_dump") else structure

        true_framework = structure_dict.get("true_route_framework")
        if not true_framework:
            log.info("没有真结局路线，跳过")
            return None

        true_route = self.agents["true_route"].process(
            story_outline_data=story_outline_data,
            route_framework=true_framework,
            user_idea=user_idea
        )
        return true_route

    def _step_mood_curve(
        self,
        story_outline_data: Dict[str, Any],
        result: Dict[str, Any],
        user_idea: str
    ) -> MoodCurve:
        """步骤5: 节奏与情绪曲线"""
        # 构建路线规划摘要用于情绪设计
        route_summary = self._format_route_for_mood(result)

        mood_curve = self.agents["pacing_atmosphere"].process(
            story_outline_data=story_outline_data,
            route_plan=route_summary,
            user_idea=user_idea
        )
        return mood_curve

    def _format_route_for_mood(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """格式化路线规划用于情绪设计"""
        structure = result["steps"]["route_structure"]
        structure_dict = structure.model_dump() if hasattr(structure, "model_dump") else structure

        common = result["steps"]["common_route"]
        common_dict = common.model_dump() if hasattr(common, "model_dump") else common

        # 收集所有个人线
        heroine_routes = []
        for key, value in result["steps"].items():
            if key.startswith("heroine_route_"):
                route_dict = value.model_dump() if hasattr(value, "model_dump") else value
                heroine_routes.append(route_dict)

        return {
            "route_plan_id": f"route_plan_{structure_dict.get('structure_id', '')}",
            "common_route": common_dict,
            "heroine_routes": heroine_routes,
            "true_route": structure_dict.get("true_route_framework")
        }

    def _format_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """格式化最终输出（新架构：共通线是主线）"""
        common = result["steps"]["common_route"]
        structure = result["steps"]["route_structure"]

        # 收集个人线
        heroine_routes = []
        for key, value in result["steps"].items():
            if key.startswith("heroine_route_"):
                heroine_routes.append(value)

        true_route = result["steps"].get("true_route")

        def get_field(obj, field, default=""):
            if hasattr(obj, field):
                val = getattr(obj, field)
                if callable(val):
                    return val()
                return val
            elif isinstance(obj, dict):
                return obj.get(field, default)
            return default

        # 获取结构框架
        structure_dict = structure.model_dump() if hasattr(structure, "model_dump") else structure

        # 收集选择点信息（共通线中的选择点，累积好感度）
        choice_points = []
        common_dict = common.model_dump() if hasattr(common, "model_dump") else common
        for cp in common_dict.get("choice_points", []):
            choice_points.append({
                "point_id": cp.get("point_id"),
                "chapter_id": cp.get("chapter_id"),
                "scene_id": cp.get("scene_id"),
                "point_name": cp.get("point_name"),
                "context_description": cp.get("context_description", ""),
                "choices": cp.get("choices", [])
            })

        # 收集结局条件
        ending_conditions = structure_dict.get("ending_conditions", [])

        # 统计章节类型
        common_chapters = [ch for ch in common_dict.get("chapters", []) if ch.get("chapter_type") == "common"]
        interlude_chapters = [ch for ch in common_dict.get("chapters", []) if ch.get("chapter_type") == "interlude"]

        output = {
            "route_structure": {
                "total_chapters": get_field(structure, "total_estimated_chapters", 0),
                "common_ratio": get_field(structure, "common_ratio", 0.7),
                "common_chapters_count": len(common_chapters),
                "interlude_chapters_count": len(interlude_chapters),
                "heroine_routes_count": len(heroine_routes),
                "has_true_route": true_route is not None
            },
            "choice_points": choice_points,
            "ending_conditions": ending_conditions,
            "heroine_routes_summary": [
                {
                    "heroine_name": get_field(hr, "heroine_name", ""),
                    "heroine_id": get_field(hr, "heroine_id", ""),
                    "route_type": get_field(hr, "route_type", ""),
                    "interlude_chapters_count": len(get_field(hr, "interlude_chapters", [])),
                    "has_ending_chapter": get_field(hr, "ending_chapter", None) is not None,
                    "route_theme": get_field(hr, "route_theme", ""),
                    "required_affection": get_field(hr, "ending_conditions", {}).get("required_affection", 0),
                    "ending_summary": get_field(hr, "ending_summary", "")
                }
                for hr in heroine_routes
            ],
            "true_route_summary": {
                "exists": true_route is not None,
                "chapters_count": len(get_field(true_route, "chapters", [])) if true_route else 0,
                "unlock_conditions": get_field(true_route, "unlock_conditions", []) if true_route else [],
                "unlock_from_heroine_endings": get_field(true_route, "unlock_from_heroine_endings", []) if true_route else []
            } if true_route else None,
            "mood_summary": {}
        }

        # 添加情绪摘要
        mood = result["steps"].get("mood_curve")
        if mood:
            output["mood_summary"] = {
                "mood_distribution": get_field(mood, "mood_distribution", {}),
                "common_scenes_count": len(get_field(mood, "common_route_mood", {}).get("scenes", [])) if hasattr(get_field(mood, "common_route_mood", {}), "get") else 0
            }

        return output

    def _save_results(self, result: Dict[str, Any], output_dir: str):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_dir = output_path / timestamp
        timestamped_dir.mkdir(parents=True, exist_ok=True)

        json_file = timestamped_dir / "routes.json"
        with open(json_file, "w", encoding="utf-8") as f:
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
    parser.add_argument(
        "--story-outline", "-s",
        help="故事大纲JSON文件路径"
    )
    parser.add_argument(
        "--output", "-o",
        help="输出目录",
        default="./output"
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="不显示进度条"
    )

    args = parser.parse_args()

    if not args.story_outline:
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

    if not args.story_outline or not Path(args.story_outline).exists():
        print("错误: 请提供有效的故事大纲JSON文件路径")
        return 1

    pipeline = RoutePlanningPipeline()

    print("\n" + "=" * 60)
    print("GAL-Dreamer 路线规划生成 (Phase 1)")
    print("=" * 60)

    result = pipeline.generate(
        story_outline_path=args.story_outline,
        output_dir=args.output,
        show_progress=not args.no_progress
    )

    print("\n" + "=" * 60)
    print("生成完成!")
    print("=" * 60)

    final = result["final_output"]
    structure = final["route_structure"]

    print(f"\n📋 路线结构（新架构：共通线是主线）:")
    print(f"  共通线占比: {structure['common_ratio']*100:.0f}%")
    print(f"  共通线章节: {structure['common_chapters_count']}章（主线）")
    print(f"  插曲章节: {structure.get('interlude_chapters_count', 0)}章（穿插在共通线中）")
    print(f"  总章节: {structure['total_chapters']}章")
    print(f"  个人路线: {structure['heroine_routes_count']}条")

    print(f"\n👩 女主路线:")
    for route in final['heroine_routes_summary']:
        print(f"  - {route['heroine_name']} ({route['route_type']})")
        print(f"    插曲章节: {route['interlude_chapters_count']}个")
        print(f"    结局章节: {'有' if route['has_ending_chapter'] else '无'}")
        print(f"    需要好感度: {route['required_affection']}")
        print(f"    主题: {route['route_theme']}")
        print(f"    结局摘要: {route['ending_summary']}")

    if final.get('true_route_summary'):
        tr = final['true_route_summary']
        print(f"\n🌟 真结局路线:")
        print(f"  章节数: {tr['chapters_count']}章")
        print(f"  解锁条件: {', '.join(tr['unlock_conditions'])}")
        print(f"  前置结局: {', '.join(tr.get('unlock_from_heroine_endings', []))}")

    # 显示选择点（累积好感度）
    if final.get('choice_points'):
        print(f"\n🔀 选择点（累积好感度）:")
        for cp in final['choice_points']:
            print(f"  [{cp['point_id']}] {cp['point_name']}")
            print(f"    章节: {cp['chapter_id']}, 场景: {cp.get('scene_id', 'N/A')}")
            for choice in cp.get('choices', []):
                affection = choice.get('affection_changes', {})
                affection_str = ", ".join([f"{hid}:{val}" for hid, val in affection.items()])
                flags = f" Flag: {choice.get('flags_set', [])}" if choice.get('flags_set') else ""
                print(f"      - {choice.get('choice_text', 'N/A')}")
                print(f"        好感度变化: {affection_str}{flags}")

    # 显示结局条件
    if final.get('ending_conditions'):
        print(f"\n🏁 结局条件:")
        for ec in final['ending_conditions']:
            print(f"  {ec['heroine_name']} ({ec['ending_type']}):")
            print(f"    需要好感度: {ec['required_affection']}")
            if ec.get('required_flags'):
                print(f"    必需Flag: {', '.join(ec['required_flags'])}")
            if ec.get('forbidden_flags'):
                print(f"    互斥Flag: {', '.join(ec['forbidden_flags'])}")

    mood = final.get('mood_summary', {})
    if mood:
        print(f"\n🎭 情绪分布: {mood.get('mood_distribution', {})}")

    return 0


if __name__ == "__main__":
    exit(main())
