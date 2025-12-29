"""
Consistency Agent
一致性审查 Agent
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from prompts.consistency_prompt import (
    CONSISTENCY_SYSTEM_PROMPT,
    CONSISTENCY_HUMAN_PROMPT
)
from models.plot import ConsistencyReport
from utils.logger import log


class ConsistencyAgent(BaseAgent):
    """一致性审查Agent - 检查剧情一致性"""

    def __init__(self):
        """初始化Consistency Agent"""
        super().__init__(
            name="ConsistencyAgent",
            system_prompt=CONSISTENCY_SYSTEM_PROMPT,
            human_prompt_template=CONSISTENCY_HUMAN_PROMPT
        )

    def _get_required_fields(self) -> List[str]:
        """返回必填字段列表"""
        return ["valid", "issues", "fix_suggestions", "lore_violations", "character_ooc"]

    def process(self, full_story_structure: Dict[str, Any], world_rules: list, character_profiles: Dict[str, Any]) -> ConsistencyReport:
        """
        处理一致性审查

        Args:
            full_story_structure: 完整剧情结构
            world_rules: 世界观规则
            character_profiles: 角色设定

        Returns:
            ConsistencyReport: 一致性报告
        """
        log.info("进行一致性审查...")

        # 格式化世界观规则
        rules_str = "\n".join([f"- {r.get('description', r) if isinstance(r, dict) else r}" for r in world_rules])

        # 运行Agent (带自动验证和修复)
        result = self.run(
            full_story_structure=full_story_structure,
            world_rules=rules_str,
            character_profiles=character_profiles
        )

        # 转换为ConsistencyReport对象
        report = ConsistencyReport(**result)

        if report.valid:
            log.success(f"一致性审查通过!")
        else:
            log.warning(f"一致性审查发现问题: {len(report.issues)}个")

        # 显示详细问题
        if report.detailed_issues:
            log.info(f"详细问题: {len(report.detailed_issues)}个")
            for issue in report.detailed_issues:
                severity_icon = {
                    "low": "🟢",
                    "medium": "🟡",
                    "high": "🟠",
                    "critical": "🔴"
                }.get(issue.severity, "⚪")
                log.warning(f"  {severity_icon} [{issue.source_agent}] {issue.description}")

        if report.agents_to_redo:
            log.warning(f"需要重做的Agent: {', '.join(report.agents_to_redo)}")

        return report

    def validate_output(self, output: Dict[str, Any]):
        """
        验证输出是否有效（只验证不修复）

        Args:
            output: Agent输出

        Returns:
            True: 验证通过
            str: 验证失败的错误信息
        """
        # 先调用父类的基础验证
        base_result = super().validate_output(output)
        if base_result is not True:
            return base_result

        # 检查valid是布尔值
        if not isinstance(output.get("valid"), bool):
            return "valid必须是布尔值"

        # 检查其他字段是列表
        list_fields = ["issues", "fix_suggestions", "lore_violations", "character_ooc"]
        for field in list_fields:
            if not isinstance(output.get(field), list):
                return f"{field}必须是数组类型"

        # 检查detailed_issues是列表
        if "detailed_issues" in output and not isinstance(output.get("detailed_issues"), list):
            return "detailed_issues必须是数组类型"

        # 检查agents_to_redo是列表
        if "agents_to_redo" in output and not isinstance(output.get("agents_to_redo"), list):
            return "agents_to_redo必须是数组类型"

        return True


if __name__ == "__main__":
    # 测试Consistency Agent
    agent = ConsistencyAgent()

    test_story = {
        "acts": {
            "act1": "主角遇到转校生",
            "act2": "逐渐了解",
            "act3": "真相揭露",
            "act4": "结局"
        },
        "routes": [
            {"route_name": "A线", "ending": "Good End"}
        ]
    }

    test_rules = [
        {"description": "没有超自然元素"},
        {"description": "现代校园背景"}
    ]

    test_characters = {
        "protagonist": {"name": "主角", "personality": ["普通"]},
        "heroines": [
            {"name": "A", "personality": ["温柔"], "secret": "无"}
        ]
    }

    try:
        report = agent.process(
            full_story_structure=test_story,
            world_rules=test_rules,
            character_profiles=test_characters
        )
        print("\n" + "="*50)
        print("Consistency Agent 测试成功!")
        print("="*50)
        print(f"通过审查: {'是' if report.valid else '否'}")
        print(f"问题数量: {len(report.issues)}")
        print(f"世界规则违规: {len(report.lore_violations)}")
        print(f"角色OOC: {len(report.character_ooc)}")
        print("="*50)
    except Exception as e:
        print(f"测试失败: {e}")
