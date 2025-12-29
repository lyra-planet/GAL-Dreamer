"""
GAL-Dreamer 世界观构建 Pipeline (模块1)
完整版本 - 包含8个Agent，支持自动修复一致性问题
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from tqdm import tqdm

# Agents
from agents.worldbuilding.story_intake_agent import StoryIntakeAgent
from agents.worldbuilding.worldbuilding_agent import WorldbuildingAgent
from agents.worldbuilding.key_element_agent import KeyElementAgent
from agents.worldbuilding.timeline_agent import TimelineAgent
from agents.worldbuilding.atmosphere_agent import AtmosphereAgent
from agents.worldbuilding.npc_faction_agent import NpcFactionAgent
from agents.worldbuilding.world_consistency_agent import WorldConsistencyAgent
from agents.worldbuilding.world_fixer_agent import WorldFixerAgent
from agents.worldbuilding.world_summary_agent import WorldSummaryAgent

# 数据模型
from utils.logger import log
from utils.config import config
from models.story import StoryConstraints
from models.worldbuilding.world import WorldSetting
from models.worldbuilding.key_element import KeyElements
from models.worldbuilding.timeline import WorldTimeline
from models.worldbuilding.atmosphere import WorldAtmosphere
from models.worldbuilding.faction import WorldFactions
from models.worldbuilding.consistency import ConsistencyReport
from models.worldbuilding.world_summary import WorldSummary
from models.worldbuilding.world_fix import WorldFixResult


class WorldbuildingPipeline:
    """
    世界观构建 Pipeline (模块1) - 完整版

    Agent依赖关系（每个步骤基于前面所有步骤）:
    1. StoryIntakeAgent      → 故事约束
    2. WorldbuildingAgent     → 基于步骤1
    3. KeyElementAgent        → 基于步骤1,2
    4. TimelineAgent          → 基于步骤1,2,3
    5. AtmosphereAgent        → 基于步骤1,2,3,4
    6. NpcFactionAgent        → 基于步骤1,2,3,4,5
    7. WorldConsistencyAgent  → 基于步骤1,2,3,4,5,6 (一致性检查)
    8. WorldFixerAgent        → 基于所有步骤 (协调修复，最多4轮)
    9. WorldSummaryAgent      → 基于所有步骤 (生成自然语言摘要)
    """

    # 最大修复轮次
    MAX_FIX_ROUNDS = 4

    def __init__(self, enable_auto_fix: bool = True):
        """
        初始化 Pipeline

        Args:
            enable_auto_fix: 是否启用自动修复功能
        """
        self.enable_auto_fix = enable_auto_fix

        self.agents = {
            "story_intake": StoryIntakeAgent(),
            "worldbuilding": WorldbuildingAgent(),
            "key_element": KeyElementAgent(),
            "timeline": TimelineAgent(),
            "atmosphere": AtmosphereAgent(),
            "npc_faction": NpcFactionAgent(),
            "consistency": WorldConsistencyAgent(),
            "fixer": WorldFixerAgent(),
            "summary": WorldSummaryAgent(),
        }
        log.info(f"WorldbuildingPipeline 初始化完成 (自动修复: {enable_auto_fix})")

    def generate(
        self,
        user_idea: str,
        output_dir: Optional[str] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """生成世界观"""
        if output_dir is None:
            output_dir = str(config.PROJECT_OUTPUT_DIR)

        result = {
            "input": {"user_idea": user_idea},
            "steps": {},
            "fix_history": [],
            "final_output": {},
        }

        # 初始生成步骤
        initial_steps = [
            ("1️⃣ 故事理解", "story_intake", self._step_story_intake),
            ("2️⃣ 世界观构建", "worldbuilding", self._step_worldbuilding),
            ("3️⃣ 关键元素", "key_element", self._step_key_element),
            ("4️⃣ 时间线", "timeline", self._step_timeline),
            ("5️⃣ 氛围基调", "atmosphere", self._step_atmosphere),
            ("6️⃣ 势力NPC", "npc_faction", self._step_npc_faction),
            ("7️⃣ 一致性检查", "consistency", self._step_consistency),
        ]

        # 执行初始生成
        pbar = tqdm(initial_steps, desc="WorldbuildingPipeline", disable=not show_progress)
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

        # 自动修复循环
        if self.enable_auto_fix:
            result = self._run_fix_loop(result, show_progress)

        # 生成世界观摘要 (在修复完成后)
        if show_progress:
            print("\n8️⃣ 世界观摘要...")
        summary = self._step_summary(result)
        result["steps"]["summary"] = summary
        if show_progress:
            print(f"✅ 世界观摘要完成")
            print(f"   概览: {summary.world_overview}")
            print(f"   可攻略角色: {len(summary.available_heroines)}个")

        result["final_output"] = self._format_output(result)

        if output_dir:
            self._save_results(result, output_dir)

        return result

    def _run_fix_loop(self, result: Dict, show_progress: bool) -> Dict:
        """运行修复循环"""
        for round_num in range(1, self.MAX_FIX_ROUNDS + 1):
            consistency = result["steps"]["consistency"]

            # 检查是否需要修复
            if consistency.overall_status == "passed":
                log.info(f"✅ 一致性检查通过，无需修复")
                break

            priority_issues = len(consistency.get_critical_issues()) + len(consistency.get_issues_by_severity("high"))
            if priority_issues == 0:
                log.info(f"✅ 无高优先级问题，停止修复")
                break

            # 第N轮修复
            if show_progress:
                print(f"\n🔧 第{round_num}轮修复...")

            # 制定修复计划
            fix_result = self._step_fixer(result, round_num)
            result["fix_history"].append(fix_result.model_dump())

            # 输出修复计划
            if show_progress:
                print(f"   📋 修复计划: {fix_result.summary}")
                for task in fix_result.fix_tasks:
                    print(f"      - {task.agent_name}: {task.fix_instructions[:80]}{'...' if len(task.fix_instructions) > 80 else ''}")

            # 如果没有修复任务，直接结束
            if not fix_result.fix_tasks:
                if show_progress:
                    print(f"   ℹ️  无需修复")
                log.info(f"修复完成 (共{round_num}轮)")
                break

            # 执行修复任务
            for task in fix_result.fix_tasks:
                agent_name = task.agent_name
                if show_progress:
                    print(f"   ⚙️  修复 {agent_name}...")

                # 获取完整的问题对象
                all_issues = result["steps"]["consistency"].issues
                issue_objects = [issue for issue in all_issues if issue.issue_id in task.issues_to_fix]

                updated_data = self._apply_fix(result, task, issue_objects)

                # 更新结果
                if updated_data:
                    result["steps"][self._get_step_key(agent_name)] = updated_data
                    if show_progress:
                        print(f"      ✅ 完成")
                else:
                    if show_progress:
                        print(f"      ⚠️  修复未执行 (Agent不支持redo_with_feedback)")

            # 重新进行一致性检查
            if show_progress:
                print(f"   🔄 重新检查一致性...")
            consistency = self._step_consistency(result)
            result["steps"]["consistency"] = consistency

            # 显示修复后的一致性状态
            if show_progress:
                status_icon = {"passed": "✅", "warning": "⚠️", "failed": "❌"}.get(consistency.overall_status, "❓")
                priority_issues = len(consistency.get_critical_issues()) + len(consistency.get_issues_by_severity("high"))
                print(f"      {status_icon} 状态: {consistency.overall_status}, 高优先级问题: {priority_issues}个")

            # 检查是否需要继续下一轮（由一致性检查结果决定）
            if consistency.overall_status == "passed":
                log.info(f"✅ 一致性检查通过，修复完成")
                break

            priority_issues = len(consistency.get_critical_issues()) + len(consistency.get_issues_by_severity("high"))
            if priority_issues == 0:
                log.info(f"✅ 无高优先级问题，修复完成")
                break

            if round_num >= self.MAX_FIX_ROUNDS:
                log.info(f"⚠️ 达到最大修复轮次({self.MAX_FIX_ROUNDS})，修复结束")
                break

        return result

    def _get_step_key(self, agent_name: str) -> str:
        """获取Agent对应的步骤key"""
        mapping = {
            "WorldbuildingAgent": "worldbuilding",
            "KeyElementAgent": "key_element",
            "TimelineAgent": "timeline",
            "AtmosphereAgent": "atmosphere",
            "NpcFactionAgent": "npc_faction",
        }
        return mapping.get(agent_name)

    def _apply_fix(self, result: Dict, task, issue_objects: List) -> Optional[Any]:
        """应用修复任务"""
        agent_name = task.agent_name
        fix_instructions = task.fix_instructions
        step_key = self._get_step_key(agent_name)

        if not step_key:
            log.warning(f"未找到Agent: {agent_name}")
            return None

        # 获取当前数据
        current_data = result["steps"][step_key]
        if hasattr(current_data, "model_dump"):
            current_data = current_data.model_dump()

        # 调用Agent的redo_with_feedback方法（如果可用）
        agent = self.agents.get(step_key)
        if agent and hasattr(agent, "redo_with_feedback"):
            # 使用完整的问题对象
            original_kwargs = self._build_agent_kwargs(result, step_key)

            try:
                fixed_result = agent.redo_with_feedback(
                    previous_output=current_data,
                    feedback_issues=issue_objects,  # 传入完整的问题对象
                    original_kwargs=original_kwargs
                )
                return fixed_result
            except Exception as e:
                log.error(f"{agent_name} 修复失败: {e}")

        return None

    def _to_dict(self, data) -> Dict:
        """确保数据为dict格式"""
        if hasattr(data, "model_dump"):
            return data.model_dump()
        return data

    def _build_agent_kwargs(self, result: Dict, step_key: str) -> Dict:
        """构建Agent调用参数"""
        constraints = self._to_dict(result["steps"]["story_intake"])
        user_idea = result["input"].get("user_idea", "")

        kwargs = {
            "story_constraints": constraints,
            "user_idea": user_idea  # 添加用户原始创意
        }

        if step_key == "worldbuilding":
            kwargs["genre"] = constraints.get("genre", "")
            kwargs["themes"] = constraints.get("themes", [])

        elif step_key == "key_element":
            kwargs["world_setting"] = self._to_dict(result["steps"]["worldbuilding"])

        elif step_key == "timeline":
            kwargs["world_setting"] = self._to_dict(result["steps"]["worldbuilding"])
            kwargs["key_elements"] = self._to_dict(result["steps"]["key_element"])

        elif step_key == "atmosphere":
            kwargs["world_setting"] = self._to_dict(result["steps"]["worldbuilding"])
            kwargs["key_elements"] = self._to_dict(result["steps"]["key_element"])
            kwargs["timeline"] = self._to_dict(result["steps"]["timeline"])

        elif step_key == "npc_faction":
            kwargs["world_setting"] = self._to_dict(result["steps"]["worldbuilding"])
            kwargs["key_elements"] = self._to_dict(result["steps"]["key_element"])
            kwargs["timeline"] = self._to_dict(result["steps"]["timeline"])
            kwargs["atmosphere"] = self._to_dict(result["steps"]["atmosphere"])

        return kwargs

    # ========== 步骤方法 ==========

    def _step_story_intake(self, result: Dict) -> StoryConstraints:
        """步骤1: 故事理解"""
        constraints = self.agents["story_intake"].process(result["input"]["user_idea"])
        result["constraints"] = constraints.model_dump()
        return constraints

    def _step_worldbuilding(self, result: Dict) -> WorldSetting:
        """步骤2: 世界观构建 (基于步骤1)"""
        constraints = result["steps"]["story_intake"]
        world = self.agents["worldbuilding"].process(
            story_constraints=constraints.model_dump(),
            genre=constraints.genre,
            themes=constraints.themes
        )
        result["world"] = world.model_dump()
        return world

    def _step_key_element(self, result: Dict) -> KeyElements:
        """步骤3: 关键元素生成 (基于步骤1,2)"""
        constraints = result["steps"]["story_intake"]
        world = result["steps"]["worldbuilding"]

        elements = self.agents["key_element"].process(
            story_constraints=constraints.model_dump(),
            world_setting=world.model_dump()
        )
        result["key_elements"] = elements.model_dump()
        return elements

    def _step_timeline(self, result: Dict) -> WorldTimeline:
        """步骤4: 时间线生成 (基于步骤1,2,3)"""
        constraints = result["steps"]["story_intake"]
        world = result["steps"]["worldbuilding"]
        elements = result["steps"]["key_element"]

        timeline = self.agents["timeline"].process(
            story_constraints=constraints.model_dump(),
            world_setting=world.model_dump(),
            key_elements=elements.model_dump()
        )
        result["timeline"] = timeline.model_dump()
        return timeline

    def _step_atmosphere(self, result: Dict) -> WorldAtmosphere:
        """步骤5: 氛围基调生成 (基于步骤1,2,3,4)"""
        constraints = result["steps"]["story_intake"]
        world = result["steps"]["worldbuilding"]
        elements = result["steps"]["key_element"]
        timeline = result["steps"]["timeline"]

        atmosphere = self.agents["atmosphere"].process(
            story_constraints=constraints.model_dump(),
            world_setting=world.model_dump(),
            key_elements=elements.model_dump(),
            timeline=timeline.model_dump()
        )
        result["atmosphere"] = atmosphere.model_dump()
        return atmosphere

    def _step_npc_faction(self, result: Dict) -> WorldFactions:
        """步骤6: 势力NPC生成 (基于步骤1,2,3,4,5)"""
        constraints = result["steps"]["story_intake"]
        world = result["steps"]["worldbuilding"]
        elements = result["steps"]["key_element"]
        timeline = result["steps"]["timeline"]
        atmosphere = result["steps"]["atmosphere"]

        factions = self.agents["npc_faction"].process(
            story_constraints=constraints.model_dump(),
            world_setting=world.model_dump(),
            key_elements=elements.model_dump(),
            timeline=timeline.model_dump(),
            atmosphere=atmosphere.model_dump()
        )
        result["factions"] = factions.model_dump()
        return factions

    def _step_consistency(self, result: Dict) -> ConsistencyReport:
        """步骤7: 一致性检查 (基于所有前置步骤)"""
        report = self.agents["consistency"].process(
            story_constraints=self._to_dict(result["steps"]["story_intake"]),
            world_setting=self._to_dict(result["steps"]["worldbuilding"]),
            key_elements=self._to_dict(result["steps"]["key_element"]),
            timeline=self._to_dict(result["steps"]["timeline"]),
            atmosphere=self._to_dict(result["steps"]["atmosphere"]),
            factions=self._to_dict(result["steps"]["npc_faction"])
        )
        result["consistency"] = report

        # 如果一致性检查失败，发出警告
        if report.overall_status == "failed":
            log.error(f"一致性检查失败: {report.summary}")
        elif report.overall_status == "warning":
            log.warning(f"一致性检查警告: {report.summary}")

        # 输出问题详情
        if report.issues:
            log.info(f"🔍 发现的问题:")
            severity_icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
            for issue in report.issues:
                icon = severity_icons.get(issue.severity, "⚪")
                log.info(f"  {icon} [{issue.severity}] {issue.source_agent}: {issue.description}")
                log.info(f"     建议: {issue.fix_suggestion}")

        return report

    def _step_summary(self, result: Dict) -> WorldSummary:
        """步骤8: 世界观摘要 (基于所有前置步骤)"""
        summary = self.agents["summary"].process(
            story_constraints=self._to_dict(result["steps"]["story_intake"]),
            world_setting=self._to_dict(result["steps"]["worldbuilding"]),
            key_elements=self._to_dict(result["steps"]["key_element"]),
            timeline=self._to_dict(result["steps"]["timeline"]),
            atmosphere=self._to_dict(result["steps"]["atmosphere"]),
            factions=self._to_dict(result["steps"]["npc_faction"]),
            user_idea=result["input"].get("user_idea", "")
        )
        result["summary"] = summary
        return summary

    def _step_fixer(self, result: Dict, round_num: int) -> WorldFixResult:
        """修复步骤: 制定修复计划"""
        fix_result = self.agents["fixer"].process(
            story_constraints=self._to_dict(result["steps"]["story_intake"]),
            world_setting=self._to_dict(result["steps"]["worldbuilding"]),
            key_elements=self._to_dict(result["steps"]["key_element"]),
            timeline=self._to_dict(result["steps"]["timeline"]),
            atmosphere=self._to_dict(result["steps"]["atmosphere"]),
            factions=self._to_dict(result["steps"]["npc_faction"]),
            consistency_report=self._to_dict(result["steps"]["consistency"]),
            current_round=round_num
        )
        return fix_result

    # ========== 辅助方法 ==========

    def _format_output(self, result: Dict) -> Dict[str, Any]:
        """格式化输出"""
        world = result["steps"]["worldbuilding"]
        elements = result["steps"]["key_element"]
        timeline = result["steps"]["timeline"]
        atmosphere = result["steps"]["atmosphere"]
        factions = result["steps"]["npc_faction"]
        consistency = result["steps"]["consistency"]

        # 辅助函数：从对象或dict中获取字段
        def get_field(data, field, default=None):
            if hasattr(data, field):
                return getattr(data, field)
            elif isinstance(data, dict):
                return data.get(field, default)
            return default

        constraints = result["steps"]["story_intake"]

        output = {
            "story_setting": {
                "genre": get_field(constraints, "genre", ""),
                "themes": get_field(constraints, "themes", []),
                "tone": get_field(constraints, "tone", ""),
            },
            "world_setting": {
                "era": get_field(world, "era", ""),
                "location": get_field(world, "location", ""),
                "type": get_field(world, "type", ""),
                "core_conflict": get_field(world, "core_conflict_source", ""),
                "description": get_field(world, "description", ""),
            },
            "key_elements": {
                "items_count": len(get_field(elements, "items", [])),
                "locations_count": len(get_field(elements, "locations", [])),
                "organizations_count": len(get_field(elements, "organizations", [])),
                "critical_items": [
                    item.get("name") if isinstance(item, dict) else item.name
                    for item in get_field(elements, "items", [])
                    if (item.get("importance") if isinstance(item, dict) else getattr(item, "importance", None)) == "critical"
                ],
            },
            "timeline": {
                "current_year": get_field(timeline, "current_year", ""),
                "events_count": len(get_field(timeline, "events", [])),
                "critical_events": [
                    e.get("name") if isinstance(e, dict) else e.name
                    for e in get_field(timeline, "events", [])
                    if (e.get("importance") if isinstance(e, dict) else getattr(e, "importance", None)) == "critical"
                ],
            },
            "atmosphere": {
                "overall_mood": get_field(atmosphere, "overall_mood", ""),
                "visual_style": get_field(atmosphere, "visual_style", ""),
                "scene_presets_count": len(get_field(atmosphere, "scene_presets", [])),
            },
            "factions": {
                "factions_count": len(get_field(factions, "factions", [])),
                "npcs_count": len(get_field(factions, "key_npcs", [])),
                "conflict_points": get_field(factions, "conflict_points", ""),
            },
            "consistency": {
                "status": get_field(consistency, "overall_status", ""),
                "total_issues": get_field(consistency, "total_issues", 0),
                "critical_issues": len(consistency.get_critical_issues()) if hasattr(consistency, "get_critical_issues") else 0,
                "high_issues": len(consistency.get_issues_by_severity("high")) if hasattr(consistency, "get_issues_by_severity") else 0,
                "summary": get_field(consistency, "summary", ""),
            },
        }

        # 添加修复历史信息
        if result.get("fix_history"):
            output["fix_history"] = {
                "rounds": len(result["fix_history"]),
                "final_status": get_field(consistency, "overall_status", ""),
            }

        return output

    def _save_results(self, result: Dict, output_dir: str):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_dir = output_path / timestamp
        timestamped_dir.mkdir(parents=True, exist_ok=True)

        json_file = timestamped_dir / "world_setting.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        log.info(f"结果已保存到: {json_file}")

        return timestamped_dir


def main():
    import argparse

    parser = argparse.ArgumentParser(description="GAL-Dreamer - 世界观构建")
    parser.add_argument("idea", help="故事创意描述")
    parser.add_argument("--output", "-o", help="输出目录")
    parser.add_argument("--no-progress", action="store_true", help="不显示进度条")
    parser.add_argument("--no-fix", action="store_true", help="禁用自动修复")

    args = parser.parse_args()

    pipeline = WorldbuildingPipeline(enable_auto_fix=not args.no_fix)

    print("\n" + "=" * 60)
    print("GAL-Dreamer 世界观构建 (完整版)")
    print("=" * 60)

    result = pipeline.generate(
        user_idea=args.idea,
        output_dir=args.output,
        show_progress=not args.no_progress
    )

    print("\n" + "=" * 60)
    print("生成完成!")
    print("=" * 60)

    final = result["final_output"]
    print(f"题材: {final['story_setting']['genre']}")
    print(f"世界观: {final['world_setting']['era']} - {final['world_setting']['location']}")
    print(f"关键道具: {final['key_elements']['items_count']}个")
    print(f"历史事件: {final['timeline']['events_count']}个")
    print(f"势力: {final['factions']['factions_count']}个")
    print(f"NPC: {final['factions']['npcs_count']}个")

    consistency = final["consistency"]
    status_icon = {"passed": "✅", "warning": "⚠️", "failed": "❌"}.get(consistency["status"], "❓")
    print(f"\n{status_icon} 一致性检查: {consistency['status']}")
    print(f"   问题数: {consistency['total_issues']}")
    if consistency['critical_issues'] > 0:
        print(f"   ⚠️  关键问题: {consistency['critical_issues']}个")
    if consistency['high_issues'] > 0:
        print(f"   ⚠️  高优先级问题: {consistency['high_issues']}个")
    print(f"   {consistency['summary']}")

    if result.get("fix_history"):
        print(f"\n🔧 修复轮次: {len(result['fix_history'])}")

    return result


if __name__ == "__main__":
    main()
