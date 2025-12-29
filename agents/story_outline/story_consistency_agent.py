"""
Story Consistency Agent
故事大纲一致性Agent - 检查一致性和有趣度
"""
from typing import Dict, Any, List, Optional, Union
import uuid
import json

from agents.base_agent import BaseAgent
from prompts.story_outline.consistency_prompt import (
    STORY_CONSISTENCY_SYSTEM_PROMPT,
    STORY_CONSISTENCY_HUMAN_PROMPT
)
from models.story_outline.consistency import StoryConsistencyReport
from utils.logger import log


class StoryConsistencyAgent(BaseAgent):
    """
    故事大纲一致性Agent

    功能:
    - 检查前提、角色、冲突的一致性
    - 评估故事的有趣度/吸引力
    - 识别老套/无聊的元素
    - 生成改进建议
    """

    # 类属性配置
    name = "StoryConsistencyAgent"
    system_prompt = STORY_CONSISTENCY_SYSTEM_PROMPT
    human_prompt_template = STORY_CONSISTENCY_HUMAN_PROMPT
    required_fields = ["overall_status", "total_issues", "summary"]
    output_model = StoryConsistencyReport

    # 问题类型
    CATEGORIES = ["conflict", "inconsistency", "missing", "suggestion"]
    # 严重程度
    SEVERITIES = ["low", "medium", "high", "critical"]
    # 状态
    STATUSES = ["passed", "warning", "failed"]

    def process(
        self,
        user_idea: str,
        world_setting_json: Dict[str, Any],
        premise: Dict[str, Any],
        cast_arc: Dict[str, Any],
        conflict_map: Dict[str, Any],
        conflict_outline: Optional[Dict[str, Any]] = None,
        validate: bool = True
    ) -> StoryConsistencyReport:
        """
        处理一致性和有趣度检查

        Args:
            user_idea: 用户原始创意
            world_setting_json: 完整的世界观数据（用于一致性检查）
            premise: 故事前提
            cast_arc: 角色弧光
            conflict_map: 矛盾引擎（包含outline和map的结构）
            conflict_outline: 冲突大纲（可选，如果conflict_map是完整结构则从中提取）
            validate: 是否验证输出

        Returns:
            StoryConsistencyReport: 检查报告
        """
        log.info("执行故事大纲检查...")

        # 构建世界观字符串（每个元素当str处理，不解析）
        world_setting_str = self._format_world_setting(world_setting_json)

        # 如果conflict_outline没传，尝试从conflict_map中提取
        if conflict_outline is None and isinstance(conflict_map, dict):
            if "outline" in conflict_map:
                conflict_outline = conflict_map["outline"]
                conflict_map = conflict_map.get("map", conflict_map)

        # 构建摘要信息
        protagonist_summary = self._format_protagonist(cast_arc.get("protagonist", {}))
        heroines_summary = self._format_heroines(cast_arc.get("heroines", []))
        supporting_summary = self._format_supporting(cast_arc.get("supporting_cast", []))
        antagonists_summary = self._format_antagonists(cast_arc.get("antagonists", []))

        # 冲突大纲信息（优先使用conflict_outline）
        if conflict_outline:
            main_conflicts_outline = conflict_outline.get("main_conflicts_outline", [])
            main_conflict_type = ", ".join([mc.get("conflict_type", "") for mc in main_conflicts_outline])
            main_conflicts_count = len(main_conflicts_outline)
            secondary_conflicts_count = len(conflict_outline.get("secondary_conflicts_outline", []))
            critical_choices_count = len(conflict_outline.get("critical_choice_outline", []))
            conflict_chain_summary = "; ".join(conflict_outline.get("conflict_chain_outline", [])[:3])
        else:
            main_conflicts_list = conflict_map.get("main_conflicts", [])
            main_conflict_type = ", ".join([mc.get("conflict_type", "") for mc in main_conflicts_list])
            main_conflicts_count = len(main_conflicts_list)
            secondary_conflicts_count = len(conflict_map.get("secondary_conflicts", []))
            critical_choices_count = self._count_critical_choices(conflict_map.get("escalation_curve", []))
            conflict_chain_summary = self._format_conflict_chain(conflict_map.get("conflict_chain", []))

        # 冲突细节信息
        main_conflicts_list = conflict_map.get("main_conflicts", [])
        main_conflict_names = [mc.get("conflict_name", "") for mc in main_conflicts_list]
        main_conflict_summary = "; ".join(main_conflict_names) if main_conflict_names else "无"
        secondary_conflicts_list = conflict_map.get("secondary_conflicts", [])
        background_conflicts_list = conflict_map.get("background_conflicts", [])

        secondary_conflicts = self._format_secondary_conflicts(secondary_conflicts_list)
        background_conflicts = self._format_background_conflicts(background_conflicts_list)
        escalation_summary = self._format_escalation_curve(conflict_map.get("escalation_curve", []))

        try:
            result = self.run(
                user_idea=user_idea,
                world_setting_json=world_setting_str,
                hook=premise.get("hook", ""),
                core_question=premise.get("core_question", ""),
                primary_genre=premise.get("primary_genre", ""),
                core_themes=", ".join(premise.get("core_themes", [])),
                emotional_tone=premise.get("emotional_tone", ""),
                must_have_elements=premise.get("must_have_elements", []),
                forbidden_elements=premise.get("forbidden_elements", []),
                creative_boundaries=premise.get("creative_boundaries", ""),
                protagonist_summary=protagonist_summary,
                heroines_summary=heroines_summary,
                supporting_summary=supporting_summary,
                antagonists_summary=antagonists_summary,
                # 冲突大纲信息
                main_conflict_type=main_conflict_type,
                main_conflicts_count=main_conflicts_count,
                secondary_conflicts_count=len(secondary_conflicts_list),
                critical_choices_count=self._count_critical_choices(conflict_map.get("escalation_curve", [])),
                conflict_chain_summary=conflict_chain_summary,
                # 冲突细节信息
                main_conflict=main_conflict_summary,
                secondary_conflicts=secondary_conflicts,
                background_conflicts=background_conflicts,
                escalation_summary=escalation_summary
            )

            if "report_id" not in result:
                result["report_id"] = f"story_consistency_{uuid.uuid4().hex[:8]}"

            report = StoryConsistencyReport(**result)
            self._log_success(report)
            return report

        except Exception as e:
            log.error(f"StoryConsistencyAgent 处理失败: {e}")
            raise RuntimeError(f"故事大纲检查失败: {e}") from e

    def _format_protagonist(self, protagonist: Dict) -> str:
        """格式化主角摘要"""
        if not protagonist:
            return "无"
        return f"{protagonist.get('character_name', '')}: {protagonist.get('role_type', '')}弧光, {protagonist.get('arc_type', '')}型"

    def _format_heroines(self, heroines: List) -> str:
        """格式化女主摘要"""
        if not heroines:
            return "无"
        summaries = []
        for h in heroines:
            summaries.append(f"{h.get('character_name', '')}: {h.get('character_arc_type', '')}弧光")
        return "; ".join(summaries)

    def _format_supporting(self, supporting: List) -> str:
        """格式化配角摘要"""
        if not supporting:
            return "无"
        return f"{len(supporting)}个配角"

    def _format_antagonists(self, antagonists: List) -> str:
        """格式化反派摘要"""
        if not antagonists:
            return "无"
        summaries = []
        for a in antagonists:
            summaries.append(f"{a.get('character_name', '')}")
        return "; ".join(summaries)

    def _format_secondary_conflicts(self, conflicts: List) -> str:
        """格式化次要矛盾摘要"""
        if not conflicts:
            return "无"
        summaries = []
        for c in conflicts:
            c_dict = c.model_dump() if hasattr(c, "model_dump") else c
            summaries.append(f"{c_dict.get('conflict_name', '')}({c_dict.get('conflict_type', '')})")
        return "; ".join(summaries)

    def _format_background_conflicts(self, conflicts: List) -> str:
        """格式化背景矛盾摘要"""
        if not conflicts:
            return "无"
        summaries = []
        for c in conflicts:
            c_dict = c.model_dump() if hasattr(c, "model_dump") else c
            summaries.append(f"{c_dict.get('conflict_name', '')}({c_dict.get('conflict_type', '')})")
        return "; ".join(summaries)

    def _format_conflict_chain(self, chain: List) -> str:
        """格式化冲突链摘要"""
        if not chain:
            return "无"
        return "; ".join(chain[:3])  # 只显示前3个

    def _count_critical_choices(self, curve: List) -> int:
        """统计关键抉择点数量"""
        count = 0
        for n in curve:
            n_dict = n.model_dump() if hasattr(n, "model_dump") else n
            node_type = n_dict.get("node_type", "")
            if "critical_choice" in node_type or n_dict.get("is_branching_point"):
                count += 1
        return count

    def _format_escalation_curve(self, curve: List) -> str:
        """格式化升级曲线摘要"""
        if not curve:
            return "无"
        summaries = []
        for n in curve:
            n_dict = n.model_dump() if hasattr(n, "model_dump") else n
            summaries.append(f"{n_dict.get('node_name', '')}({n_dict.get('emotional_intensity', 5)}/10)")
        return " -> ".join(summaries)

    def _log_success(self, report: StoryConsistencyReport) -> None:
        """记录成功日志"""
        log.info(f"故事大纲检查完成: {report.overall_status}")
        log.info(f"  总问题: {report.total_issues}个")

        critical = report.get_critical_issues()
        high = report.get_issues_by_severity("high")

        if critical:
            log.warning(f"  关键问题: {len(critical)}个")
        if high:
            log.warning(f"  高优先级: {len(high)}个")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """验证输出"""
        # 检查overall_status - 只要是非空字符串即可
        status = output.get("overall_status")
        if not status or not isinstance(status, str):
            return "overall_status不能为空"

        # 检查total_issues
        total_issues = output.get("total_issues")
        if not isinstance(total_issues, int) or total_issues < 0:
            return "total_issues必须是非负整数"

        # 检查summary
        if not output.get("summary"):
            return "summary不能为空"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        return {
            "report_id": f"story_consistency_fallback_{uuid.uuid4().hex[:8]}",
            "overall_status": "warning",
            "total_issues": 1,
            "consistency_issues": 0,
            "issues": [
                {
                    "issue_id": "fallback_1",
                    "category": "suggestion",
                    "severity": "low",
                    "source_agent": "StoryPremiseAgent",
                    "description": "无法完成完整检查，请人工审核",
                    "fix_suggestion": "请人工审核故事大纲",
                    "is_fixed": False
                }
            ],
            "summary": "由于系统错误，无法完成完整检查，请人工审核",
            "fallback": True
        }

    def _format_world_setting(self, world_setting: Dict[str, Any]) -> str:
        """格式化世界观数据为字符串（每个元素当str处理，不解析）"""
        lines = []
        # 只需要steps部分
        steps = world_setting.get("steps", {})
        for key, value in steps.items():
            lines.append(f"【{key}】")
            lines.append(str(value))
            lines.append("")  # 空行分隔
        return "\n".join(lines)
