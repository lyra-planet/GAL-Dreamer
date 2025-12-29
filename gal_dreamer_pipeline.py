"""
GAL-Dreamer 主流程控制器
串联所有 8 个 Agent，从用户输入生成完整的 Galgame 故事
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from tqdm import tqdm

from agents.story_intake_agent import StoryIntakeAgent
from agents.worldbuilding_agent import WorldbuildingAgent
from agents.cast_design_agent import CastDesignAgent
from agents.macro_plot_agent import MacroPlotAgent
from agents.route_design_agent import RouteDesignAgent
from agents.conflict_emotion_agent import ConflictEmotionAgent
from agents.consistency_agent import ConsistencyAgent
from agents.narrator_agent import NarratorAgent
from agents.director_agent import DirectorAgent
from agents.script_agents import ScriptOrchestrator

from utils.logger import log
from utils.config import config
from models.story import StoryConstraints
from models.world import WorldSetting
from models.character import CharacterProfile
from models.plot import MacroPlot, RouteDesign, ConflictDesign, ConsistencyReport
from models.director import StorySnapshot


class GALDreamerPipeline:
    """GAL-Dreamer 主流程 - 从故事创意到完整 Galgame 脚本"""

    def __init__(self):
        """初始化所有 Agent"""
        self.agents = {
            "story_intake": StoryIntakeAgent(),
            "worldbuilding": WorldbuildingAgent(),
            "cast_design": CastDesignAgent(),
            "macro_plot": MacroPlotAgent(),
            "route_design": RouteDesignAgent(),
            "conflict_emotion": ConflictEmotionAgent(),
            "consistency": ConsistencyAgent(),
            "narrator": NarratorAgent(),
        }
        # 全局统筹Agent
        self.director = DirectorAgent()
        # 脚本生成编排器
        self.script_orchestrator = ScriptOrchestrator()
        log.info("GAL-Dreamer Pipeline 初始化完成 (含DirectorAgent + ScriptOrchestrator)")

    def generate(
        self,
        user_idea: str,
        num_routes: int = 3,
        skip_consistency: bool = False,
        output_dir: Optional[str] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        从用户创意生成完整 Galgame 故事

        Args:
            user_idea: 用户的故事创意描述
            num_routes: 需要的攻略线路数量
            skip_consistency: 是否跳过一致性检查（加快速度）
            output_dir: 输出目录，如果不指定则使用配置文件中的PROJECT_OUTPUT_DIR(默认./output)
            show_progress: 是否显示进度条

        Returns:
            包含所有生成结果的字典
        """
        # 如果未指定输出目录，使用配置文件中的默认值
        if output_dir is None:
            output_dir = str(config.PROJECT_OUTPUT_DIR)
        result = {
            "input": {"user_idea": user_idea, "num_routes": num_routes},
            "steps": {},
            "final_output": {}
        }

        # 定义执行步骤
        steps = [
            ("1️⃣ 故事理解", "story_intake", self._step_story_intake),
            ("2️⃣ 世界观构建", "worldbuilding", self._step_worldbuilding),
            ("3️⃣ 角色设计", "cast_design", self._step_cast_design),
            ("4️⃣ 大剧情结构", "macro_plot", self._step_macro_plot),
            ("5️⃣ 线路设计", "route_design", self._step_route_design),
            ("6️⃣ 冲突设计", "conflict_emotion", self._step_conflict_emotion),
        ]

        if not skip_consistency:
            steps.append(("7️⃣ 一致性检查", "consistency", self._step_consistency))

        steps.append(("8️⃣ 文本生成", "narrator", self._step_narrator))

        # 执行所有步骤
        pbar = tqdm(steps, desc="GAL-Dreamer 生成中", disable=not show_progress)
        for step_name, step_key, step_func in pbar:
            pbar.set_description(f"{step_name}")
            try:
                step_result = step_func(result)
                result["steps"][step_key] = step_result
                pbar.write(f"✅ {step_name} 完成")
            except Exception as e:
                pbar.write(f"❌ {step_name} 失败: {e}")
                log.error(f"{step_name} 失败: {e}")
                raise

        # 整理最终输出
        result["final_output"] = self._format_final_output(result)

        # 保存到文件
        if output_dir:
            self._save_results(result, output_dir)

        return result

    def _step_story_intake(self, result: Dict) -> StoryConstraints:
        """步骤1: 故事理解"""
        constraints = self.agents["story_intake"].process(result["input"]["user_idea"])
        result["constraints"] = constraints.model_dump()
        return constraints

    def _step_worldbuilding(self, result: Dict) -> WorldSetting:
        """步骤2: 世界观构建"""
        constraints = result["steps"]["story_intake"]
        world = self.agents["worldbuilding"].process(
            story_constraints=constraints.model_dump(),
            genre=constraints.genre,
            themes=constraints.themes
        )
        result["world"] = world.model_dump()
        return world

    def _step_cast_design(self, result: Dict) -> CharacterProfile:
        """步骤3: 角色设计"""
        world = result["steps"]["worldbuilding"]
        constraints = result["steps"]["story_intake"]
        cast = self.agents["cast_design"].process(
            world_setting=world.model_dump(),
            themes=constraints.themes,
            required_routes=result["input"]["num_routes"]
        )
        result["cast"] = cast.model_dump()
        return cast

    def _step_macro_plot(self, result: Dict) -> MacroPlot:
        """步骤4: 大剧情结构"""
        world = result["steps"]["worldbuilding"]
        cast = result["steps"]["cast_design"]
        constraints = result["steps"]["story_intake"]

        # 构建角色摘要
        cast_summary = self._build_cast_summary(cast)

        plot = self.agents["macro_plot"].process(
            world_setting=world.model_dump(),
            cast_summary=cast_summary,
            themes=constraints.themes
        )
        result["macro_plot"] = plot.model_dump()
        return plot

    def _step_route_design(self, result: Dict) -> RouteDesign:
        """步骤5: 线路设计"""
        plot = result["steps"]["macro_plot"]
        cast = result["steps"]["cast_design"]

        routes = self.agents["route_design"].process(
            macro_plot=plot.model_dump(),
            heroine_list=[h.model_dump() for h in cast.heroines]
        )
        result["route_design"] = routes.model_dump()
        return routes

    def _step_conflict_emotion(self, result: Dict) -> ConflictDesign:
        """步骤6: 冲突与情绪设计"""
        routes = result["steps"]["route_design"]
        cast = result["steps"]["cast_design"]

        conflict = self.agents["conflict_emotion"].process(
            route_plots=routes.model_dump(),
            character_states=cast.model_dump()
        )
        result["conflict_design"] = conflict.model_dump()
        return conflict

    def _step_consistency(self, result: Dict) -> ConsistencyReport:
        """
        步骤7: 一致性检查（使用DirectorAgent全局统筹修复）

        工作流程:
        1. ConsistencyAgent检查一致性问题
        2. 如果有问题，DirectorAgent分析并制定全局修订计划
        3. DirectorAgent统筹各Agent进行修改
        4. 重新检查，最多3轮
        """
        # 一致性审查最大轮数
        max_consistency_rounds = 3
        consistency_round = 0

        while consistency_round < max_consistency_rounds:
            consistency_round += 1
            log.info(f"="*60)
            log.info(f"一致性审查第{consistency_round}轮")
            log.info(f"="*60)

            # 构建故事快照
            snapshot = self._build_story_snapshot(result)

            # 运行一致性检查
            report = self._run_consistency_check(snapshot, result)

            result["consistency_report"] = report.model_dump()

            # 如果通过审查，退出循环
            if report.valid:
                log.success(f"一致性审查通过 (第{consistency_round}轮)")
                return report

            # 如果没有详细问题，退出
            if not report.detailed_issues:
                log.warning(f"一致性审查发现问题但没有详细描述")
                return report

            # 使用DirectorAgent进行全局统筹修复
            log.info(f"发现{len(report.detailed_issues)}个问题，调用DirectorAgent进行全局统筹...")
            success = self._director_guided_revision(snapshot, report, result)

            # 更新快照
            snapshot = self._build_story_snapshot(result)

            if not success:
                log.warning(f"第{consistency_round}轮修复失败")
                break

            log.info(f"第{consistency_round}轮修复完成，重新审查...")

        # 达到最大轮数
        log.warning(f"一致性审查达到最大轮数({max_consistency_rounds})，仍有问题")
        return report

    def _build_story_snapshot(self, result: Dict) -> StorySnapshot:
        """构建故事快照"""
        snapshot = StorySnapshot()

        if "story_intake" in result.get("steps", {}):
            snapshot.story_intake = result["steps"]["story_intake"].model_dump()
        if "worldbuilding" in result.get("steps", {}):
            snapshot.worldbuilding = result["steps"]["worldbuilding"].model_dump()
        if "cast_design" in result.get("steps", {}):
            snapshot.cast_design = result["steps"]["cast_design"].model_dump()
        if "macro_plot" in result.get("steps", {}):
            snapshot.macro_plot = result["steps"]["macro_plot"].model_dump()
        if "route_design" in result.get("steps", {}):
            snapshot.route_design = result["steps"]["route_design"].model_dump()
        if "conflict_emotion" in result.get("steps", {}):
            snapshot.conflict_emotion = result["steps"]["conflict_emotion"].model_dump()

        return snapshot

    def _run_consistency_check(self, snapshot: StorySnapshot, result: Dict) -> ConsistencyReport:
        """运行一致性检查"""
        world = result["steps"]["worldbuilding"]
        cast = result["steps"]["cast_design"]

        full_story = snapshot.to_full_dict()

        report = self.agents["consistency"].process(
            full_story_structure=full_story,
            world_rules=world.rules,
            character_profiles=cast.model_dump()
        )

        return report

    def _director_guided_revision(
        self,
        snapshot: StorySnapshot,
        report: ConsistencyReport,
        result: Dict
    ) -> bool:
        """
        DirectorAgent统筹修复

        Returns:
            修复是否成功
        """
        log.info(f"🎬 DirectorAgent 开始全局统筹...")

        try:
            # Director分析问题并制定修订计划
            revision_plan = self.director.analyze_and_plan(
                story_snapshot=snapshot,
                consistency_issues=report.detailed_issues
            )

            if not revision_plan.has_issues:
                log.success("DirectorAgent评估后认为无需修改")
                return True

            log.info(f"修订策略: {revision_plan.revision_strategy}")
            log.info(f"执行顺序: {' -> '.join(revision_plan.execution_order)}")

            # Director执行修订计划
            updated_snapshot_dict = self.director.execute_revision(
                plan=revision_plan,
                agents=self.agents,
                story_snapshot=snapshot
            )

            # 更新result
            self._update_result_from_snapshot(result, updated_snapshot_dict)

            log.success("DirectorAgent统筹修复完成")
            return True

        except Exception as e:
            log.error(f"DirectorAgent统筹失败: {e}")
            import traceback
            log.error(traceback.format_exc())
            return False

    def _update_result_from_snapshot(self, result: Dict, snapshot_dict: Dict):
        """从快照字典更新result"""
        model_mapping = {
            "worldbuilding": ("steps", "world", WorldSetting),
            "cast_design": ("steps", "cast", CharacterProfile),
            "macro_plot": ("steps", "macro_plot", MacroPlot),
            "route_design": ("steps", "route_design", RouteDesign),
            "conflict_emotion": ("steps", "conflict_design", ConflictDesign),
        }

        for agent_key, (step_key, result_key, model_class) in model_mapping.items():
            if agent_key in snapshot_dict:
                try:
                    model_obj = model_class(**snapshot_dict[agent_key])
                    result["steps"][agent_key] = model_obj
                    result[result_key] = model_obj.model_dump()
                except Exception as e:
                    log.warning(f"更新{agent_key}失败: {e}")

    def _get_agent_original_kwargs(self, agent_name: str, result: Dict) -> Dict[str, Any]:
        """获取Agent重做时需要的原始参数"""
        constraints = result["steps"]["story_intake"]
        world = result["steps"]["worldbuilding"]
        cast = result["steps"]["cast_design"]
        plot = result.get("steps", {}).get("macro_plot")
        routes = result.get("steps", {}).get("route_design")

        kwargs_mapping = {
            "worldbuilding": {
                "story_constraints": constraints.model_dump(),
                "genre": constraints.genre,
                "themes": constraints.themes
            },
            "cast_design": {
                "world_setting": world.model_dump(),
                "themes": constraints.themes,
                "required_routes": result["input"]["num_routes"]
            },
            "macro_plot": {
                "world_setting": world.model_dump(),
                "cast_summary": self._build_cast_summary(cast),
                "themes": constraints.themes
            },
            "route_design": {
                "macro_plot": plot.model_dump() if plot else {},
                "heroine_list": [h.model_dump() for h in cast.heroines]
            },
            "conflict_emotion": {
                "route_plots": routes.model_dump() if routes else {},
                "character_states": cast.model_dump()
            }
        }

        return kwargs_mapping.get(agent_name, {})

    def _convert_dict_to_model(self, agent_name: str, data: Dict[str, Any]):
        """将字典转换回对应的Pydantic模型"""
        from models.world import WorldSetting
        from models.character import CharacterProfile
        from models.plot import MacroPlot, RouteDesign, ConflictDesign

        model_mapping = {
            "worldbuilding": WorldSetting,
            "cast_design": CharacterProfile,
            "macro_plot": MacroPlot,
            "route_design": RouteDesign,
            "conflict_emotion": ConflictDesign
        }

        model_class = model_mapping.get(agent_name)
        if model_class:
            return model_class(**data)
        return data

    def _step_key_mapping(self) -> Dict[str, str]:
        """Agent名称到result中key的映射"""
        return {
            "worldbuilding": "world",
            "cast_design": "cast",
            "macro_plot": "macro_plot",
            "route_design": "route_design",
            "conflict_emotion": "conflict_design"
        }

    def _update_full_story(self, full_story: Dict, agent_name: str, new_result):
        """更新full_story中的对应部分"""
        key_mapping = self._step_key_mapping()
        if agent_name in key_mapping:
            full_story[key_mapping[agent_name]] = new_result.model_dump()

    def _step_narrator(self, result: Dict) -> Dict[str, Any]:
        """
        步骤8: 文本生成 - 生成完整游戏脚本

        使用 ScriptOrchestrator 生成:
        - 开场场景
        - 共通线场景
        - 各线路专属场景
        - 各线路结局
        """
        constraints = result["steps"]["story_intake"]
        cast = result["steps"]["cast_design"]
        routes = result.get("route_design", result.get("steps", {}).get("route_design"))
        macro_plot = result.get("macro_plot", result.get("steps", {}).get("macro_plot"))

        log.info("开始生成完整游戏脚本...")

        # 准备故事数据
        story_data = {
            "title": f"《{constraints.genre}之恋》",
            "genre": constraints.genre,
            "tone": constraints.tone,
            "protagonist": cast.protagonist.model_dump() if hasattr(cast.protagonist, 'model_dump') else cast.protagonist,
            "world": {
                "era": result.get("world", {}).get("era", "现代"),
                "location": result.get("world", {}).get("location", "日本"),
                "description": result.get("world", {}).get("description", "")
            },
            "macro_plot": macro_plot.model_dump() if hasattr(macro_plot, 'model_dump') else macro_plot,
            "routes": []
        }

        # 准备线路数据
        if routes:
            routes_list = routes.routes if hasattr(routes, 'routes') else routes.get('routes', [])
            for route in routes_list:
                route_dict = route.model_dump() if hasattr(route, 'model_dump') else route

                # 找到对应的女主
                heroine_id = route_dict.get('heroine_id', '')
                heroine = None
                for h in cast.heroines:
                    h_dict = h.model_dump() if hasattr(h, 'model_dump') else h
                    if h_dict.get('character_id') == heroine_id or h_dict.get('name') == heroine_id:
                        heroine = h_dict
                        break

                # 确保 heroine 是字典，如果找不到就使用空字典
                if heroine is None or not isinstance(heroine, dict):
                    heroine = {}
                    log.warning(f"线路 {route_dict.get('route_name', '')} 找不到对应女主，使用空字典")

                # 构建 route 数据，确保 heroine 字段是字典
                route_data = {
                    "route_id": route_dict.get("route_id", ""),
                    "route_name": route_dict.get("route_name", ""),
                    "heroine": heroine,
                    "climax_aftermath": route_dict.get("climax_aftermath", "经历高潮后，主角面临最终选择"),
                    "ending_types": route_dict.get("ending_types", ["Happy End"])
                }

                story_data["routes"].append(route_data)

        # 使用 ScriptOrchestrator 生成完整脚本
        try:
            game_script = self.script_orchestrator.generate_full_script(
                story_data=story_data,
                common_scene_count=3,  # 共通线场景数
                route_scene_count=4,   # 每条线路场景数
                progress_callback=lambda msg: log.info(f"  {msg}")
            )

            # 保存完整脚本到结果
            result["game_script"] = game_script.model_dump()

            # 构建适合 _save_results 的输出格式
            scenes_output = {}
            scenes_output["完整脚本"] = game_script.full_text
            scenes_output["场景统计"] = f"共 {game_script.get_scene_count()} 个场景，{len(game_script.full_text)} 字符"

            result["narrator_output"] = scenes_output

            log.success(f"脚本生成完成: {game_script.get_scene_count()}个场景, {len(game_script.full_text)}字符")

        except Exception as e:
            log.error(f"脚本生成失败: {e}")
            import traceback
            log.error(traceback.format_exc())
            result["narrator_output"] = {"错误": f"脚本生成失败: {str(e)}"}

        return result.get("narrator_output", {})

    def _generate_default_scene(self, cast: CharacterProfile, tone: str) -> Dict[str, str]:
        """生成默认场景（当没有线路设计时）"""
        scene = {
            "location": "教室",
            "time": "放学后",
            "scene_type": "对话",
            "characters_present": ["protagonist"],
            "actions": []
        }

        characters_dict = {
            "protagonist": cast.protagonist.model_dump(),
        }

        if cast.heroines:
            scene["characters_present"].append(cast.heroines[0].character_id)
            characters_dict[cast.heroines[0].character_id] = cast.heroines[0].model_dump()

        text = self.agents["narrator"].generate_scene_text(
            scene=scene,
            characters_dict=characters_dict,
            tone=tone
        )

        return {"默认场景": text}

    def _build_cast_summary(self, cast: CharacterProfile) -> str:
        """构建角色摘要"""
        lines = [
            f"主角: {cast.protagonist.name} (核心缺陷: {cast.protagonist.core_flaw})",
            f"可攻略角色: {', '.join([h.name for h in cast.heroines])}",
            f"配角: {', '.join([s.name for s in cast.side_characters])}"
        ]
        return "\n".join(lines)

    def _format_final_output(self, result: Dict) -> Dict[str, Any]:
        """格式化最终输出"""
        return {
            "故事设定": {
                "题材": result["steps"]["story_intake"].genre,
                "主题": result["steps"]["story_intake"].themes,
                "基调": result["steps"]["story_intake"].tone,
                "必备元素": result["steps"]["story_intake"].must_have,
            },
            "世界观": {
                "时代": result["steps"]["worldbuilding"].era,
                "地点": result["steps"]["worldbuilding"].location,
                "类型": result["steps"]["worldbuilding"].type,
                "核心冲突": result["steps"]["worldbuilding"].core_conflict_source,
            },
            "角色": {
                "主角": result["steps"]["cast_design"].protagonist.name,
                "可攻略角色": [h.name for h in result["steps"]["cast_design"].heroines],
            },
            "故事结构": {
                "故事弧": result["steps"]["macro_plot"].story_arc,
                "高潮": result["steps"]["macro_plot"].climax_point,
            },
            "线路": {
                "数量": len(result["steps"]["route_design"].routes),
                "线路列表": [
                    {
                        "名称": r.route_name,
                        "冲突": r.conflict_focus,
                        "结局": r.ending_types,
                    }
                    for r in result["steps"]["route_design"].routes
                ]
            },
            "生成文本": result.get("narrator_output", {}),
        }

    def _save_results(self, result: Dict, output_dir: str):
        """保存结果到文件"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 创建带时间戳的子目录，避免覆盖之前的结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_dir = output_path / timestamp
        timestamped_dir.mkdir(parents=True, exist_ok=True)

        # 保存完整 JSON
        json_file = timestamped_dir / "galgame_story.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        log.info(f"完整结果已保存到: {json_file}")

        # 保存文本摘要
        summary_file = timestamped_dir / "story_summary.txt"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("GAL-Dreamer 生成故事\n")
            f.write("=" * 60 + "\n\n")

            final = result["final_output"]
            f.write(f"题材: {final['故事设定']['题材']}\n")
            f.write(f"主题: {', '.join(final['故事设定']['主题'])}\n")
            f.write(f"基调: {final['故事设定']['基调']}\n\n")

            f.write(f"世界观: {final['世界观']['时代']} - {final['世界观']['地点']}\n")
            f.write(f"核心冲突: {final['世界观']['核心冲突']}\n\n")

            f.write(f"角色:\n")
            f.write(f"  主角: {final['角色']['主角']}\n")
            f.write(f"  可攻略: {', '.join(final['角色']['可攻略角色'])}\n\n")

            f.write(f"故事弧: {final['故事结构']['故事弧']}\n\n")

            f.write("=" * 60 + "\n")
            f.write("生成的场景文本:\n")
            f.write("=" * 60 + "\n\n")

            for scene_name, scene_text in final.get("生成文本", {}).items():
                f.write(f"\n【{scene_name}】\n")
                f.write("-" * 40 + "\n")
                # 确保 scene_text 是字符串
                if not isinstance(scene_text, str):
                    scene_text = str(scene_text)
                f.write(scene_text)
                f.write("\n\n")

        log.info(f"文本摘要已保存到: {summary_file}")
        log.info(f"所有文件已保存到: {timestamped_dir}")

        return timestamped_dir


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="GAL-Dreamer - 从创意生成 Galgame 故事")
    parser.add_argument("idea", help="故事创意描述")
    parser.add_argument("--routes", type=int, default=3, help="攻略线路数量")
    parser.add_argument("--output", "-o", help=f"输出目录 (默认: {config.PROJECT_OUTPUT_DIR})")
    parser.add_argument("--skip-consistency", action="store_true", help="跳过一致性检查")
    parser.add_argument("--no-progress", action="store_true", help="不显示进度条")

    args = parser.parse_args()

    pipeline = GALDreamerPipeline()

    print("\n" + "=" * 60)
    print("GAL-Dreamer 开始生成")
    print("=" * 60)
    print(f"输入创意: {args.idea[:100]}...")
    print(f"线路数量: {args.routes}")
    print("=" * 60 + "\n")

    result = pipeline.generate(
        user_idea=args.idea,
        num_routes=args.routes,
        skip_consistency=args.skip_consistency,
        output_dir=args.output,
        show_progress=not args.no_progress
    )

    print("\n" + "=" * 60)
    print("生成完成!")
    print("=" * 60)

    final = result["final_output"]
    print(f"题材: {final['故事设定']['题材']}")
    print(f"可攻略角色: {', '.join(final['角色']['可攻略角色'])}")
    print(f"线路数量: {final['线路']['数量']}")

    # 显示输出目录
    output_path = args.output if args.output else str(config.PROJECT_OUTPUT_DIR)
    print(f"\n结果已保存到: {output_path}")


if __name__ == "__main__":
    main()
