"""
GAL-Dreamer 故事大纲 Pipeline (Phase 0)
基于世界观JSON生成故事大纲 - 包含5个Agent + 修复循环
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from tqdm import tqdm

# Agents
from agents.story_outline.story_premise_agent import StoryPremiseAgent
from agents.story_outline.cast_arc_agent import CastArcAgent
from agents.story_outline.conflict_outline_agent import ConflictOutlineAgent
from agents.story_outline.conflict_engine_agent import ConflictEngineAgent
from agents.story_outline.story_consistency_agent import StoryConsistencyAgent
from agents.story_outline.story_fixer_agent import StoryFixerAgent

# 数据模型
from utils.logger import log
from utils.config import config
from models.story_outline.premise import StoryPremise
from models.story_outline.cast_arc import CastArc
from models.story_outline.conflict_map import ConflictMap
from models.story_outline.consistency import StoryConsistencyReport


class StoryOutlinePipeline:
    """
    故事大纲 Pipeline (Phase 0)

    Agent依赖关系（每个步骤基于前面所有步骤）:
    1. StoryPremiseAgent      → 故事前提（基于worldbuilding JSON）
    2. CastArcAgent           → 角色弧光（基于worldbuilding + premise）
    3. ConflictOutlineAgent   → 冲突大纲（基于worldbuilding + premise + cast_arc）
    4. StoryConsistencyAgent  → 一致性&有趣度检查（基于前提+角色+大纲）
    5. StoryFixerAgent        → 修复计划（基于检查报告）
    6. ConflictEngineAgent    → 具体冲突（基于worldbuilding + premise + cast_arc + outline）

    提前一致性检查（在大纲阶段）:
    - 冲突大纲完成后立即检查
    - 发现问题先修复，再生成具体冲突
    - 避免生成大量具体冲突后发现框架问题需要重做

    输入: 世界观JSON文件路径或数据
    输出: 故事大纲JSON
    """

    MAX_FIX_ROUNDS = 4

    def __init__(self):
        """初始化 Pipeline"""
        self.agents = {
            "premise": StoryPremiseAgent(),
            "cast_arc": CastArcAgent(),
            "conflict_outline": ConflictOutlineAgent(),
            "conflict_engine": ConflictEngineAgent(),
            "consistency": StoryConsistencyAgent(),
            "fixer": StoryFixerAgent(),
        }
        log.info("StoryOutlinePipeline 初始化完成")

    def generate(
        self,
        world_setting_path: Optional[str] = None,
        world_setting_data: Optional[Dict[str, Any]] = None,
        output_dir: Optional[str] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        生成故事大纲

        Args:
            world_setting_path: 世界观JSON文件路径
            world_setting_data: 直接传入的世界观数据（如果提供则忽略path）
            output_dir: 输出目录
            show_progress: 是否显示进度

        Returns:
            故事大纲结果字典
        """
        # 加载世界观数据
        if world_setting_data:
            world_setting_json = world_setting_data
        elif world_setting_path:
            with open(world_setting_path, 'r', encoding='utf-8') as f:
                world_setting_json = json.load(f)
        else:
            raise ValueError("必须提供 world_setting_path 或 world_setting_data")

        # 验证世界观数据
        if "steps" not in world_setting_json:
            raise ValueError("world_setting_json必须包含steps字段")

        result = {
            "input": {
                "world_setting_source": world_setting_path or "direct_data",
                "user_idea": world_setting_json.get("input", {}).get("user_idea", "")
            },
            "steps": {},
            "fix_history": [],
            "final_output": {},
        }

        # 生成世界观摘要（用于日志）
        world_summary = self._format_world_summary(world_setting_json.get("steps", {}))

        # 1. 执行基础生成步骤（前提 + 角色 + 冲突大纲）
        self._run_outline_steps(world_setting_json, result, show_progress)

        # 2. 大纲阶段一致性检查（基于前提+角色+大纲）
        outline_consistency = self._run_outline_consistency_check(
            world_setting_json, result
        )
        result["steps"]["outline_consistency"] = outline_consistency

        # 3. 大纲阶段修复循环（只有critical问题时才进入）
        critical_issues = outline_consistency.get_critical_issues()

        should_fix = len(critical_issues) > 0

        if should_fix:
            print(f"\n🔧 大纲阶段发现{len(critical_issues)}个关键问题，开始修复循环...")
            result = self._run_outline_fix_loop(
                world_setting_json, result, show_progress
            )

        # 4. 生成具体冲突（基于已验证的大纲）
        self._generate_conflict_details(world_setting_json, result, show_progress)

        # 5. 格式化最终输出
        result["final_output"] = self._format_output(result)

        # 6. 保存结果
        if output_dir:
            self._save_results(result, output_dir)

        return result

    def _format_world_summary(self, steps: Dict) -> str:
        """格式化世界观摘要"""
        lines = ["世界观摘要:"]
        for key, value in steps.items():
            # 直接把每个元素当字符串处理，不截断
            lines.append(f"- {key}: {str(value)}")
        return "\n".join(lines)

    def _run_outline_steps(self, world_setting_json: Dict, result: Dict, show_progress: bool):
        """执行大纲生成步骤（前提 + 角色 + 冲突大纲）"""
        steps = [
            ("1️⃣ 故事前提", "premise", self._step_premise),
            ("2️⃣ 角色弧光", "cast_arc", self._step_cast_arc),
            ("3️⃣ 冲突大纲", "conflict_outline", self._step_conflict_outline),
        ]

        pbar = tqdm(steps, desc="StoryOutlinePipeline: 大纲生成", disable=not show_progress)
        for step_name, step_key, step_func in pbar:
            pbar.set_description(f"{step_name}")
            try:
                step_result = step_func(world_setting_json, result)
                result["steps"][step_key] = step_result
                pbar.write(f"✅ {step_name} 完成")
            except Exception as e:
                pbar.write(f"❌ {step_name} 失败: {e}")
                log.error(f"{step_name} 失败: {e}")
                raise

    def _run_outline_consistency_check(
        self, world_setting_json: Dict, result: Dict
    ) -> StoryConsistencyReport:
        """大纲阶段一致性检查（基于前提+角色+大纲，不含具体冲突细节）"""
        log.info("执行大纲阶段一致性检查...")

        user_idea = world_setting_json.get("input", {}).get("user_idea", "")

        # 转换数据为dict
        premise = result["steps"]["premise"]
        premise_dict = premise.model_dump() if hasattr(premise, "model_dump") else premise

        cast_arc = result["steps"]["cast_arc"]
        cast_arc_dict = cast_arc.model_dump() if hasattr(cast_arc, "model_dump") else cast_arc

        # 冲突大纲
        conflict_outline = result["steps"]["conflict_outline"]

        # 创建空的conflict_map用于检查（大纲阶段没有具体冲突）
        empty_conflict_map = {
            "main_conflicts": [],
            "secondary_conflicts": [],
            "background_conflicts": [],
            "escalation_curve": [],
            "conflict_chain": [],
            "faction_conflicts": {},
            "unbreakable_rules": [],
            "conflict_constraints": []
        }

        report = self.agents["consistency"].process(
            user_idea=user_idea,
            world_setting_json=world_setting_json,
            premise=premise_dict,
            cast_arc=cast_arc_dict,
            conflict_map=empty_conflict_map,
            conflict_outline=conflict_outline
        )

        # 打印检查结果
        print(f"\n📊 大纲阶段一致性检查: {report.overall_status}")
        print(f"   问题: {report.total_issues}个")

        if report.get_critical_issues():
            print(f"   🔴 关键问题: {len(report.get_critical_issues())}个")
        if report.get_issues_by_severity("high"):
            print(f"   🟠 高优先级: {len(report.get_issues_by_severity('high'))}个")

        return report

    def _run_consistency_check(
        self, world_setting_json: Dict, result: Dict
    ) -> StoryConsistencyReport:
        """执行一致性检查"""
        log.info("执行一致性&有趣度检查...")

        user_idea = world_setting_json.get("input", {}).get("user_idea", "")

        # 转换数据为dict
        premise = result["steps"]["premise"]
        premise_dict = premise.model_dump() if hasattr(premise, "model_dump") else premise

        cast_arc = result["steps"]["cast_arc"]
        cast_arc_dict = cast_arc.model_dump() if hasattr(cast_arc, "model_dump") else cast_arc

        # 冲突数据现在是包含outline和map的结构
        conflict_data = result["steps"]["conflict_engine"]
        if isinstance(conflict_data, dict) and "outline" in conflict_data:
            # 新结构：包含outline和map
            conflict_outline = conflict_data["outline"]
            conflict_map = conflict_data["map"]
            conflict_map_dict = conflict_map.model_dump() if hasattr(conflict_map, "model_dump") else conflict_map
        else:
            # 兼容旧结构
            conflict_outline = None
            conflict_map_dict = conflict_data.model_dump() if hasattr(conflict_data, "model_dump") else conflict_data

        report = self.agents["consistency"].process(
            user_idea=user_idea,
            world_setting_json=world_setting_json,
            premise=premise_dict,
            cast_arc=cast_arc_dict,
            conflict_map=conflict_map_dict,
            conflict_outline=conflict_outline  # 传递冲突大纲
        )

        # 打印检查结果
        print(f"\n📊 一致性检查: {report.overall_status}")
        print(f"   问题: {report.total_issues}个")

        if report.get_critical_issues():
            print(f"   🔴 关键问题: {len(report.get_critical_issues())}个")
        if report.get_issues_by_severity("high"):
            print(f"   🟠 高优先级: {len(report.get_issues_by_severity('high'))}个")

        return report

    def _run_outline_fix_loop(
        self, world_setting_json: Dict, result: Dict, show_progress: bool
    ) -> Dict:
        """大纲阶段修复循环（只修复前提、角色、大纲，不涉及具体冲突）"""
        user_idea = world_setting_json.get("input", {}).get("user_idea", "")
        fix_round = 0

        while fix_round < self.MAX_FIX_ROUNDS:
            consistency_report = result["steps"]["outline_consistency"]
            critical_issues = consistency_report.get_critical_issues()

            # 退出条件：没有critical问题
            if len(critical_issues) == 0:
                log.info("大纲修复完成：无关键问题")
                break

            fix_round += 1
            print(f"\n🔧 大纲第{fix_round}轮修复...")

            # 生成修复计划
            report_dict = consistency_report.model_dump() if hasattr(consistency_report, "model_dump") else consistency_report
            fix_plan = self.agents["fixer"].process(
                user_idea=user_idea,
                consistency_report=report_dict,
                current_round=fix_round
            )

            if not fix_plan.fix_tasks:
                print("   无修复任务，结束")
                break

            print(f"   修复任务: {len(fix_plan.fix_tasks)}个")
            for task in fix_plan.fix_tasks:
                print(f"   - {task.agent_name}: {task.fix_instructions[:50]}...")

            # 记录修复历史
            result["fix_history"].append({
                "stage": "outline",
                "round": fix_round,
                "fix_plan": fix_plan.model_dump() if hasattr(fix_plan, "model_dump") else fix_plan,
            })

            # 执行大纲修复
            self._apply_outline_fixes(world_setting_json, result, fix_plan.fix_tasks)

            # 重新检查大纲
            print("   重新检查大纲...")
            new_report = self._run_outline_consistency_check(world_setting_json, result)
            result["steps"]["outline_consistency"] = new_report

            if not fix_plan.should_continue:
                print("   大纲修复完成，结束循环")
                break

        if fix_round >= self.MAX_FIX_ROUNDS:
            print(f"\n⚠️ 已达到最大修复轮次({self.MAX_FIX_ROUNDS})")

        return result

    def _apply_outline_fixes(self, world_setting_json: Dict, result: Dict, fix_tasks):
        """应用大纲阶段的修复"""
        user_idea = world_setting_json.get("input", {}).get("user_idea", "")

        for task in fix_tasks:
            agent_name = task.agent_name

            if agent_name == "StoryPremiseAgent":
                premise = self._redo_premise(world_setting_json, result, task.fix_instructions)
                result["steps"]["premise"] = premise

            elif agent_name == "CastArcAgent":
                cast_arc = self._redo_cast_arc(world_setting_json, result, task.fix_instructions)
                result["steps"]["cast_arc"] = cast_arc

            elif agent_name == "ConflictOutlineAgent":
                conflict_outline = self._redo_conflict_outline_only(world_setting_json, result, task.fix_instructions)
                result["steps"]["conflict_outline"] = conflict_outline

    def _redo_conflict_outline_only(self, world_setting_json: Dict, result: Dict, fix_instructions: str):
        """重新生成冲突大纲（不带具体冲突）"""
        user_idea = world_setting_json.get("input", {}).get("user_idea", "")
        premise = result["steps"]["premise"]
        cast_arc = result["steps"]["cast_arc"]

        premise_dict = premise.model_dump() if hasattr(premise, "model_dump") else premise
        cast_arc_dict = cast_arc.model_dump() if hasattr(cast_arc, "model_dump") else cast_arc

        conflict_outline = self.agents["conflict_outline"].generate_outline(
            world_setting_json=world_setting_json,
            premise_json=premise_dict,
            cast_arc_json=cast_arc_dict,
            user_idea=user_idea,
            fix_instructions=fix_instructions
        )
        return conflict_outline

    def _generate_conflict_details(self, world_setting_json: Dict, result: Dict, show_progress: bool):
        """基于已验证的大纲生成具体冲突"""
        print("\n📝 生成具体冲突...")
        user_idea = world_setting_json.get("input", {}).get("user_idea", "")
        premise = result["steps"]["premise"]
        cast_arc = result["steps"]["cast_arc"]
        conflict_outline = result["steps"]["conflict_outline"]

        premise_dict = premise.model_dump() if hasattr(premise, "model_dump") else premise
        cast_arc_dict = cast_arc.model_dump() if hasattr(cast_arc, "model_dump") else cast_arc

        conflict_map = self._generate_conflicts_from_outline(
            world_setting_json, premise_dict, cast_arc_dict, conflict_outline, user_idea
        )

        result["steps"]["conflict_engine"] = {
            "outline": conflict_outline,
            "map": conflict_map
        }
        print("✅ 具体冲突生成完成")

    def _run_fix_loop(
        self, world_setting_json: Dict, result: Dict, show_progress: bool
    ) -> Dict:
        """执行修复循环"""
        user_idea = world_setting_json.get("input", {}).get("user_idea", "")
        fix_round = 0

        while fix_round < self.MAX_FIX_ROUNDS:
            consistency_report = result["steps"]["consistency"]
            critical_issues = consistency_report.get_critical_issues()

            # 退出条件：没有critical问题
            if len(critical_issues) == 0:
                log.info("修复完成：无关键问题")
                break

            fix_round += 1
            print(f"\n🔧 第{fix_round}轮修复...")

            # 生成修复计划
            report_dict = consistency_report.model_dump() if hasattr(consistency_report, "model_dump") else consistency_report
            fix_plan = self.agents["fixer"].process(
                user_idea=user_idea,
                consistency_report=report_dict,
                current_round=fix_round
            )

            if not fix_plan.fix_tasks:
                print("   无修复任务，结束")
                break

            print(f"   修复任务: {len(fix_plan.fix_tasks)}个")
            for task in fix_plan.fix_tasks:
                print(f"   - {task.agent_name}: {task.fix_instructions[:50]}...")

            # 记录修复历史
            result["fix_history"].append({
                "round": fix_round,
                "fix_plan": fix_plan.model_dump() if hasattr(fix_plan, "model_dump") else fix_plan,
            })

            # 执行修复
            self._apply_fixes(world_setting_json, result, fix_plan)

            # 重新检查
            print("   重新检查...")
            new_report = self._run_consistency_check(world_setting_json, result)
            result["steps"]["consistency"] = new_report

            if not fix_plan.should_continue:
                print("   修复完成，结束循环")
                break

        if fix_round >= self.MAX_FIX_ROUNDS:
            print(f"\n⚠️ 已达到最大修复轮次({self.MAX_FIX_ROUNDS})")

        return result

    def _apply_fixes(self, world_setting_json: Dict, result: Dict, fix_plan):
        """应用修复"""
        user_idea = world_setting_json.get("input", {}).get("user_idea", "")

        for task in fix_plan.fix_tasks:
            agent_name = task.agent_name

            if agent_name == "StoryPremiseAgent":
                premise = self._redo_premise(world_setting_json, result, task.fix_instructions)
                result["steps"]["premise"] = premise

            elif agent_name == "CastArcAgent":
                cast_arc = self._redo_cast_arc(world_setting_json, result, task.fix_instructions)
                result["steps"]["cast_arc"] = cast_arc

            elif agent_name == "ConflictOutlineAgent":
                # 重新生成冲突大纲和冲突细节
                conflict = self._redo_conflict_outline(world_setting_json, result, task.fix_instructions)
                result["steps"]["conflict_engine"] = conflict

            elif agent_name == "ConflictEngineAgent":
                # 只重新生成冲突细节，保持大纲不变
                conflict = self._redo_conflict_detail_only(world_setting_json, result, task.fix_instructions)
                result["steps"]["conflict_engine"] = conflict

    def _redo_premise(self, world_setting_json: Dict, result: Dict, fix_instructions: str) -> StoryPremise:
        """重新执行premise（带修复指令）"""
        user_idea = world_setting_json.get("input", {}).get("user_idea", "")
        premise = self.agents["premise"].process(
            world_setting_json=world_setting_json,
            user_idea=user_idea,
            fix_instructions=fix_instructions
        )
        return premise

    def _redo_cast_arc(self, world_setting_json: Dict, result: Dict, fix_instructions: str) -> CastArc:
        """重新执行cast_arc（带修复指令）"""
        user_idea = world_setting_json.get("input", {}).get("user_idea", "")
        premise = result["steps"]["premise"]
        premise_dict = premise.model_dump() if hasattr(premise, "model_dump") else premise

        cast_arc = self.agents["cast_arc"].process(
            world_setting_json=world_setting_json,
            premise_json=premise_dict,
            user_idea=user_idea,
            fix_instructions=fix_instructions
        )
        return cast_arc

    def _redo_conflict_outline(self, world_setting_json: Dict, result: Dict, fix_instructions: str):
        """重新执行conflict_outline和conflict_engine（带修复指令）- 修复框架层面问题"""
        user_idea = world_setting_json.get("input", {}).get("user_idea", "")
        premise = result["steps"]["premise"]
        cast_arc = result["steps"]["cast_arc"]

        premise_dict = premise.model_dump() if hasattr(premise, "model_dump") else premise
        cast_arc_dict = cast_arc.model_dump() if hasattr(cast_arc, "model_dump") else cast_arc

        # 重新生成冲突大纲
        print("     🔧 重新生成冲突大纲...")
        conflict_outline = self.agents["conflict_outline"].generate_outline(
            world_setting_json=world_setting_json,
            premise_json=premise_dict,
            cast_arc_json=cast_arc_dict,
            user_idea=user_idea,
            fix_instructions=fix_instructions
        )

        # 基于新大纲重新生成冲突细节
        print("     🔧 基于新大纲重新生成冲突细节...")
        conflict_map = self._generate_conflicts_from_outline(
            world_setting_json, premise_dict, cast_arc_dict, conflict_outline, user_idea, fix_instructions
        )
        # 返回和_step_conflict_engine一样的结构
        return {
            "outline": conflict_outline,
            "map": conflict_map
        }

    def _redo_conflict_detail_only(self, world_setting_json: Dict, result: Dict, fix_instructions: str):
        """只重新生成冲突细节（带修复指令）- 保留大纲不变"""
        user_idea = world_setting_json.get("input", {}).get("user_idea", "")
        premise = result["steps"]["premise"]
        cast_arc = result["steps"]["cast_arc"]

        premise_dict = premise.model_dump() if hasattr(premise, "model_dump") else premise
        cast_arc_dict = cast_arc.model_dump() if hasattr(cast_arc, "model_dump") else cast_arc

        # 获取现有的冲突大纲
        conflict_data = result["steps"]["conflict_engine"]
        if isinstance(conflict_data, dict) and "outline" in conflict_data:
            conflict_outline = conflict_data["outline"]
        else:
            # 如果没有大纲，需要先生成
            print("     🔧 未找到大纲，先生成冲突大纲...")
            conflict_outline = self.agents["conflict_outline"].generate_outline(
                world_setting_json=world_setting_json,
                premise_json=premise_dict,
                cast_arc_json=cast_arc_dict,
                user_idea=user_idea,
                fix_instructions=fix_instructions
            )

        # 基于大纲重新生成冲突细节
        print("     🔧 重新生成冲突细节（保留大纲）...")
        conflict_map = self._generate_conflicts_from_outline(
            world_setting_json, premise_dict, cast_arc_dict, conflict_outline, user_idea, fix_instructions
        )
        # 返回和_step_conflict_engine一样的结构
        return {
            "outline": conflict_outline,
            "map": conflict_map
        }

    def _redo_conflict_engine(self, world_setting_json: Dict, result: Dict, fix_instructions: str):
        """重新执行conflict_engine（兼容性方法，现在调用_redo_conflict_outline）"""
        return self._redo_conflict_outline(world_setting_json, result, fix_instructions)

    def _step_premise(self, world_setting_json: Dict, result: Dict) -> StoryPremise:
        """步骤1: 故事前提（基于worldbuilding）"""
        user_idea = world_setting_json.get("input", {}).get("user_idea", "")
        premise = self.agents["premise"].process(
            world_setting_json=world_setting_json,
            user_idea=user_idea
        )
        return premise

    def _step_cast_arc(self, world_setting_json: Dict, result: Dict) -> CastArc:
        """步骤2: 角色弧光（基于worldbuilding + premise）"""
        user_idea = world_setting_json.get("input", {}).get("user_idea", "")
        premise = result["steps"]["premise"]

        # 将premise转为dict
        if hasattr(premise, "model_dump"):
            premise_dict = premise.model_dump()
        else:
            premise_dict = premise

        cast_arc = self.agents["cast_arc"].process(
            world_setting_json=world_setting_json,
            premise_json=premise_dict,
            user_idea=user_idea
        )
        return cast_arc

    def _step_conflict_outline(self, world_setting_json: Dict, result: Dict):
        """步骤3: 冲突大纲（仅框架，不含具体冲突）"""
        user_idea = world_setting_json.get("input", {}).get("user_idea", "")
        premise = result["steps"]["premise"]
        cast_arc = result["steps"]["cast_arc"]

        premise_dict = premise.model_dump() if hasattr(premise, "model_dump") else premise
        cast_arc_dict = cast_arc.model_dump() if hasattr(cast_arc, "model_dump") else cast_arc

        conflict_outline = self.agents["conflict_outline"].generate_outline(
            world_setting_json=world_setting_json,
            premise_json=premise_dict,
            cast_arc_json=cast_arc_dict,
            user_idea=user_idea
        )
        return conflict_outline

    def _step_conflict_engine(self, world_setting_json: Dict, result: Dict):
        """步骤3: 矛盾引擎（先大纲，后具体）- 保留用于兼容"""
        user_idea = world_setting_json.get("input", {}).get("user_idea", "")
        premise = result["steps"]["premise"]
        cast_arc = result["steps"]["cast_arc"]

        # 转为dict
        premise_dict = premise.model_dump() if hasattr(premise, "model_dump") else premise
        cast_arc_dict = cast_arc.model_dump() if hasattr(cast_arc, "model_dump") else cast_arc

        # 第一步：生成冲突大纲
        print("   📋 生成冲突大纲...")
        conflict_outline = self.agents["conflict_outline"].generate_outline(
            world_setting_json=world_setting_json,
            premise_json=premise_dict,
            cast_arc_json=cast_arc_dict,
            user_idea=user_idea
        )

        # 第二步：基于大纲，逐步生成具体冲突
        conflict_map = self._generate_conflicts_from_outline(
            world_setting_json, premise_dict, cast_arc_dict, conflict_outline, user_idea
        )

        # 返回包含大纲和细节的结构
        return {
            "outline": conflict_outline,
            "map": conflict_map
        }

    def _generate_conflicts_from_outline(
        self, world_setting_json: Dict, premise_dict: Dict, cast_arc_dict: Dict,
        conflict_outline: Dict, user_idea: str, fix_instructions: str = ""
    ) -> ConflictMap:
        """基于冲突大纲生成具体冲突"""
        from models.story_outline.conflict_map import ConflictMap
        import uuid
        import json

        # 格式化世界观数据
        world_setting_str = self._format_world_setting(world_setting_json.get("steps", {}))

        # 第一阶段：生成主冲突列表（至少3个）
        print("   📌 生成主冲突列表...")
        main_conflicts = self.agents["conflict_engine"].generate_main_conflicts(
            world_setting_json=world_setting_str,
            premise_json=json.dumps(premise_dict, ensure_ascii=False),
            cast_arc_json=json.dumps(cast_arc_dict, ensure_ascii=False),
            main_conflicts_outline=json.dumps(conflict_outline.get("main_conflicts_outline", []), ensure_ascii=False),
            user_idea=user_idea,
            fix_instructions=fix_instructions
        )
        print(f"     生成了 {len(main_conflicts)} 个主冲突")

        # 第二阶段：生成次要冲突
        print("   📌 生成次要冲突...")
        secondary_conflicts = []
        secondary_outlines = conflict_outline.get("secondary_conflicts_outline", [])
        for i, sec_outline in enumerate(secondary_outlines):
            print(f"     - 次要冲突 {i+1}/{len(secondary_outlines)}...")
            prev_conflicts = {
                "main_conflicts": [c.model_dump() if hasattr(c, "model_dump") else c for c in main_conflicts],
                "secondary_conflicts": [c.model_dump() if hasattr(c, "model_dump") else c for c in secondary_conflicts]
            }
            new_conflict = self.agents["conflict_engine"].generate_secondary_conflict(
                world_setting_json=world_setting_str,
                premise_json=json.dumps(premise_dict, ensure_ascii=False),
                previous_conflicts=json.dumps(prev_conflicts, ensure_ascii=False),
                conflict_outline=json.dumps(sec_outline, ensure_ascii=False),
                conflict_index=i+1,
                user_idea=user_idea,
                fix_instructions=fix_instructions
            )
            secondary_conflicts.append(new_conflict)

        # 第三阶段：生成背景冲突
        print("   📌 生成背景冲突...")
        background_conflicts = []
        bg_outlines = conflict_outline.get("background_conflicts_outline", [])
        for i, bg_outline in enumerate(bg_outlines):
            print(f"     - 背景冲突 {i+1}/{len(bg_outlines)}...")
            prev_conflicts = {
                "main_conflicts": [c.model_dump() if hasattr(c, "model_dump") else c for c in main_conflicts],
                "secondary_conflicts": [c.model_dump() if hasattr(c, "model_dump") else c for c in secondary_conflicts],
                "background_conflicts": [c.model_dump() if hasattr(c, "model_dump") else c for c in background_conflicts]
            }
            new_conflict = self.agents["conflict_engine"].generate_background_conflict(
                world_setting_json=world_setting_str,
                previous_conflicts=json.dumps(prev_conflicts, ensure_ascii=False),
                conflict_outline=json.dumps(bg_outline, ensure_ascii=False),
                conflict_index=i+1,
                user_idea=user_idea,
                fix_instructions=fix_instructions
            )
            background_conflicts.append(new_conflict)

        # 第四阶段：生成升级曲线
        print("   📌 生成危机升级曲线...")
        all_conflicts = {
            "main_conflicts": [c.model_dump() if hasattr(c, "model_dump") else c for c in main_conflicts],
            "secondary_conflicts": [c.model_dump() if hasattr(c, "model_dump") else c for c in secondary_conflicts],
            "background_conflicts": [c.model_dump() if hasattr(c, "model_dump") else c for c in background_conflicts]
        }
        escalation_curve = self.agents["conflict_engine"].generate_escalation_curve(
            world_setting_json=world_setting_str,
            premise_json=json.dumps(premise_dict, ensure_ascii=False),
            all_conflicts_json=json.dumps(all_conflicts, ensure_ascii=False),
            escalation_structure=json.dumps(conflict_outline.get("escalation_structure", {}), ensure_ascii=False),
            critical_choices=json.dumps(conflict_outline.get("critical_choice_outline", []), ensure_ascii=False),
            user_idea=user_idea,
            fix_instructions=fix_instructions
        )

        # 第五阶段：生成冲突链和势力博弈
        print("   📌 生成冲突链和势力博弈...")
        conflict_chain_data = self.agents["conflict_engine"].generate_conflict_chain(
            all_conflicts_json=json.dumps(all_conflicts, ensure_ascii=False),
            cast_arc_json=json.dumps(cast_arc_dict, ensure_ascii=False),
            user_idea=user_idea,
            fix_instructions=fix_instructions
        )

        # 组装完整的ConflictMap
        conflict_map = ConflictMap(
            conflict_map_id=f"conflict_{uuid.uuid4().hex[:8]}",
            main_conflicts=main_conflicts,
            secondary_conflicts=secondary_conflicts,
            background_conflicts=background_conflicts,
            escalation_curve=escalation_curve,
            conflict_chain=conflict_chain_data.get("conflict_chain", []),
            faction_conflicts=conflict_chain_data.get("faction_conflicts", {}),
            unbreakable_rules=conflict_chain_data.get("unbreakable_rules", []),
            conflict_constraints=conflict_chain_data.get("conflict_constraints", [])
        )

        return conflict_map

    def _format_world_setting(self, steps: Dict) -> str:
        """格式化世界观数据为字符串（每个元素当str处理，不解析）"""
        lines = []
        for key, value in steps.items():
            # 直接转字符串，不做JSON序列化
            lines.append(f"【{key}】")
            lines.append(str(value))
            lines.append("")  # 空行分隔
        return "\n".join(lines)

    def _format_output(self, result: Dict) -> Dict[str, Any]:
        """格式化最终输出"""
        premise = result["steps"]["premise"]
        cast_arc = result["steps"]["cast_arc"]
        conflict_data = result["steps"]["conflict_engine"]
        # 使用大纲阶段的一致性报告
        consistency = result["steps"].get("outline_consistency")

        # 处理冲突数据（可能是新结构或旧结构）
        if isinstance(conflict_data, dict) and "map" in conflict_data:
            conflict_map = conflict_data["map"]
            conflict_outline = conflict_data.get("outline", {})
        else:
            conflict_map = conflict_data
            conflict_outline = {}

        # 辅助函数
        def get_field(data, field, default=None):
            if hasattr(data, field):
                return getattr(data, field)
            elif isinstance(data, dict):
                return data.get(field, default)
            return default

        output = {
            "story_premise": {
                "hook": get_field(premise, "hook", ""),
                "core_question": get_field(premise, "core_question", ""),
                "selling_points": get_field(premise, "selling_points", []),
                "primary_genre": get_field(premise, "primary_genre", ""),
                "core_themes": get_field(premise, "core_themes", []),
                "emotional_tone": get_field(premise, "emotional_tone", ""),
                "creative_boundaries": get_field(premise, "creative_boundaries", ""),
            },
            "character_arcs": {
                "protagonist": {
                    "name": get_field(get_field(cast_arc, "protagonist", {}), "character_name", ""),
                    "arc_type": get_field(get_field(cast_arc, "protagonist", {}), "character_arc_type", ""),
                },
                "heroines_count": len(get_field(cast_arc, "heroines", [])),
                "supporting_count": len(get_field(cast_arc, "supporting_cast", [])),
                "antagonists_count": len(get_field(cast_arc, "antagonists", [])),
                "heroines": [
                    {
                        "name": get_field(h, "character_name", ""),
                        "arc_type": get_field(h, "character_arc_type", ""),
                    }
                    for h in get_field(cast_arc, "heroines", [])
                ]
            },
            "conflict_engine": {
                "main_conflicts_count": len(get_field(conflict_map, "main_conflicts", [])),
                "main_conflicts": [
                    {
                        "name": get_field(mc, "conflict_name", ""),
                        "type": get_field(mc, "conflict_type", "")
                    }
                    for mc in get_field(conflict_map, "main_conflicts", [])
                ],
                "secondary_conflicts_count": len(get_field(conflict_map, "secondary_conflicts", [])),
                "background_conflicts_count": len(get_field(conflict_map, "background_conflicts", [])),
                "escalation_nodes_count": len(get_field(conflict_map, "escalation_curve", [])),
                "critical_choices_count": len(conflict_outline.get("critical_choice_outline", [])),
                "faction_conflicts_count": len(get_field(conflict_map, "faction_conflicts", {})),
            },
            "consistency": {
                "status": get_field(consistency, "overall_status", ""),
                "total_issues": get_field(consistency, "total_issues", 0),
            }
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

        json_file = timestamped_dir / "story_outline.json"
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

    parser = argparse.ArgumentParser(description="GAL-Dreamer - 故事大纲生成")
    parser.add_argument("--world-setting", "-w", help="世界观JSON文件路径")
    parser.add_argument("--output", "-o", help="输出目录", default="./output")
    parser.add_argument("--no-progress", action="store_true", help="不显示进度条")

    args = parser.parse_args()

    if not args.world_setting:
        # 尝试使用最新的世界观数据
        output_dir = Path(args.output)
        if output_dir.exists():
            import re
            timestamp_dirs = [d for d in output_dir.iterdir() if d.is_dir() and re.match(r"\d{8}_\d{6}", d.name)]

            if timestamp_dirs:
                latest_dir = sorted(timestamp_dirs)[-1]
                world_setting_path = latest_dir / "world_setting.json"
                if world_setting_path.exists():
                    args.world_setting = str(world_setting_path)
                    print(f"使用最新的世界观数据: {world_setting_path}")

    if not args.world_setting or not Path(args.world_setting).exists():
        print("错误: 请提供有效的世界观JSON文件路径")
        return 1

    pipeline = StoryOutlinePipeline()

    print("\n" + "=" * 60)
    print("GAL-Dreamer 故事大纲生成 (Phase 0)")
    print("=" * 60)

    result = pipeline.generate(
        world_setting_path=args.world_setting,
        output_dir=args.output,
        show_progress=not args.no_progress
    )

    print("\n" + "=" * 60)
    print("生成完成!")
    print("=" * 60)

    final = result["final_output"]
    consistency = final["consistency"]

    print(f"\n📖 故事前提:")
    print(f"  核心钩子: {final['story_premise']['hook']}")
    print(f"  核心问题: {final['story_premise']['core_question']}")
    print(f"  主类型: {final['story_premise']['primary_genre']}")

    print(f"\n👥 角色弧光:")
    print(f"  主角: {final['character_arcs']['protagonist']['name']} ({final['character_arcs']['protagonist']['arc_type']}弧光)")
    print(f"  女主: {final['character_arcs']['heroines_count']}个")
    for h in final['character_arcs']['heroines']:
        print(f"    - {h['name']}: {h['arc_type']}弧光")

    print(f"\n⚔️ 矛盾引擎:")
    print(f"  主冲突: {final['conflict_engine']['main_conflicts_count']}个")
    for mc in final['conflict_engine']['main_conflicts']:
        print(f"    - {mc['name']} ({mc['type']})")
    print(f"  次要冲突: {final['conflict_engine']['secondary_conflicts_count']}个")
    print(f"  危机节点: {final['conflict_engine']['escalation_nodes_count']}个")

    print(f"\n📊 质量评估:")
    print(f"  状态: {consistency['status']}")
    print(f"  问题数: {consistency['total_issues']}")

    return 0


if __name__ == "__main__":
    exit(main())
