"""
Story Fixer Agent
故事大纲修复Agent - 协调各Agent修复问题
"""
from typing import Dict, Any, List, Optional, Union
import uuid

from agents.base_agent import BaseAgent
from prompts.story_outline.fixer_prompt import (
    STORY_FIXER_SYSTEM_PROMPT,
    STORY_FIXER_HUMAN_PROMPT
)
from models.story_outline.story_fix import StoryFixResult
from utils.logger import log


class StoryFixerAgent(BaseAgent):
    """
    故事大纲修复Agent

    功能:
    - 分析一致性和有趣度问题
    - 制定修复计划
    - 生成Agent修复指令
    - 协调修复顺序
    """

    # 类属性配置
    name = "StoryFixerAgent"
    system_prompt = STORY_FIXER_SYSTEM_PROMPT
    human_prompt_template = STORY_FIXER_HUMAN_PROMPT
    required_fields = ["fix_tasks", "should_continue", "summary"]
    output_model = StoryFixResult

    # 可用的Agent列表
    AVAILABLE_AGENTS = [
        "StoryPremiseAgent",
        "CastArcAgent",
        "ConflictOutlineAgent",
    ]

    def process(
        self,
        user_idea: str,
        consistency_report: Dict[str, Any],
        current_round: int = 1,
        validate: bool = True
    ) -> StoryFixResult:
        """
        处理修复计划生成

        Args:
            user_idea: 用户原始创意
            consistency_report: 一致性检查报告
            current_round: 当前修复轮次
            validate: 是否验证输出

        Returns:
            StoryFixResult: 修复计划
        """
        log.info(f"制定故事大纲修复计划 (第{current_round}轮)...")

        try:
            # 构建问题摘要
            issues = consistency_report.get("issues", [])
            critical_issues = [i for i in issues if i.get("severity") == "critical"]
            high_issues = [i for i in issues if i.get("severity") == "high"]
            priority_issues = critical_issues + high_issues

            issues_summary = self._format_issues_summary(priority_issues)

            result = self.run(
                user_idea=user_idea,
                issues_summary=issues_summary,
                current_round=current_round
            )

            if "fix_id" not in result:
                result["fix_id"] = f"story_fix_{uuid.uuid4().hex[:8]}"

            fix_result = StoryFixResult(**result)
            self._log_success(fix_result)
            return fix_result

        except Exception as e:
            log.error(f"StoryFixerAgent 处理失败: {e}")
            raise RuntimeError(f"修复计划制定失败: {e}") from e

    def _format_issues_summary(self, issues: List[Dict[str, Any]]) -> str:
        """格式化问题摘要"""
        if not issues:
            return "无问题需要修复"

        lines = []
        for issue in issues:
            severity_icon = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }.get(issue.get("severity", ""), "⚪")

            category_label = {
                "conflict": "矛盾",
                "inconsistency": "不一致",
                "missing": "缺失",
                "boring": "无趣",
                "weak": "薄弱",
                "suggestion": "建议"
            }.get(issue.get("category", ""), issue.get("category", ""))

            lines.append(
                f"{severity_icon} [{issue.get('severity')}] "
                f"{category_label} - {issue.get('source_agent')}: {issue.get('description')}"
            )
            lines.append(f"   建议: {issue.get('fix_suggestion')}")
            lines.append(f"   ID: {issue.get('issue_id')}")

        return "\n".join(lines)

    def _log_success(self, fix_result: StoryFixResult) -> None:
        """记录成功日志"""
        log.info(f"修复计划制定完成: {fix_result.summary}")
        log.info(f"  修复任务: {len(fix_result.fix_tasks)}个")
        log.info(f"  需要继续: {'是' if fix_result.should_continue else '否'}")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """验证输出"""
        # 检查fix_tasks
        fix_tasks = output.get("fix_tasks")
        if not isinstance(fix_tasks, list):
            return "fix_tasks必须是数组类型"

        for i, task in enumerate(fix_tasks):
            if not isinstance(task, dict):
                return f"fix_tasks[{i}]必须是对象"

            agent_name = task.get("agent_name")
            if agent_name not in self.AVAILABLE_AGENTS:
                return f"fix_tasks[{i}]的agent_name无效: {agent_name}"

            if not task.get("fix_instructions"):
                return f"fix_tasks[{i}]缺少fix_instructions"

            issues_list = task.get("issues_to_fix")
            if issues_list is not None and not isinstance(issues_list, list):
                return f"fix_tasks[{i}]的issues_to_fix必须是数组类型"

        # 检查should_continue
        should_continue = output.get("should_continue")
        if not isinstance(should_continue, bool):
            return "should_continue必须是布尔类型"

        # 检查summary
        if not output.get("summary"):
            return "summary不能为空"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        return {
            "fix_id": f"story_fix_fallback_{uuid.uuid4().hex[:8]}",
            "round": 1,
            "fix_tasks": [],
            "applied_fixes": {},
            "remaining_issues": [],
            "should_continue": False,
            "summary": "无法制定修复计划，跳过修复",
            "fallback": True
        }
