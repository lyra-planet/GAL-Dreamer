"""
World Consistency Agent
世界观一致性Agent - 检查所有输出的一致性
"""
from typing import Dict, Any, List, Optional, Union
import uuid
import json

from agents.base_agent import BaseAgent
from prompts.worldbuilding.consistency_prompt import (
    CONSISTENCY_SYSTEM_PROMPT,
    CONSISTENCY_HUMAN_PROMPT
)
from models.worldbuilding.consistency import ConsistencyReport
from utils.logger import log


class WorldConsistencyAgent(BaseAgent):
    """
    世界观一致性Agent

    功能:
    - 检查规则一致性
    - 检查历史一致性
    - 检查元素一致性
    - 检查氛围一致性
    - 检查势力一致性
    - 生成一致性报告
    """

    # 类属性配置
    name = "WorldConsistencyAgent"
    system_prompt = CONSISTENCY_SYSTEM_PROMPT
    human_prompt_template = CONSISTENCY_HUMAN_PROMPT
    required_fields = ["overall_status", "total_issues", "summary"]
    output_model = ConsistencyReport

    # 问题类型
    CATEGORIES = ["conflict", "inconsistency", "missing", "suggestion"]
    # 严重程度
    SEVERITIES = ["low", "medium", "high", "critical"]
    # 状态
    STATUSES = ["passed", "warning", "failed"]

    def process(
        self,
        story_constraints: Dict[str, Any],
        world_setting: Dict[str, Any],
        key_elements: Dict[str, Any],
        timeline: Dict[str, Any],
        atmosphere: Dict[str, Any],
        factions: Dict[str, Any],
        validate: bool = True
    ) -> ConsistencyReport:
        """
        处理一致性检查

        Args:
            story_constraints: 故事约束条件
            world_setting: 世界观设定
            key_elements: 关键元素
            timeline: 时间线
            atmosphere: 氛围设定
            factions: 势力设定
            validate: 是否验证输出

        Returns:
            ConsistencyReport: 一致性检查报告
        """
        log.info("执行一致性检查...")

        # 参数检查
        for name, value in [
            ("world_setting", world_setting),
            ("key_elements", key_elements),
            ("timeline", timeline),
            ("atmosphere", atmosphere),
            ("factions", factions),
        ]:
            if not value:
                raise ValueError(f"{name}不能为空")

        try:
            # 构建完整的输入数据
            world_rules = world_setting.get("rules", [])
            key_items = key_elements.get("items", [])
            key_locations = key_elements.get("locations", [])
            organizations = key_elements.get("organizations", [])
            terms = key_elements.get("terms", [])

            events = timeline.get("events", [])

            scene_presets = atmosphere.get("scene_presets", [])

            factions_list = factions.get("factions", [])
            key_npcs = factions.get("key_npcs", [])
            relation_map = factions.get("relation_map", {})

            result = self.run(
                genre=story_constraints.get("genre", ""),
                themes=", ".join(story_constraints.get("themes", [])),
                tone=story_constraints.get("tone", ""),
                # 世界观完整数据
                world_type=world_setting.get("type", ""),
                era=world_setting.get("era", ""),
                location=world_setting.get("location", ""),
                core_conflict=world_setting.get("core_conflict_source", ""),
                world_description=world_setting.get("description", ""),
                world_rules=json.dumps(world_rules, ensure_ascii=False),
                # 关键元素完整数据
                key_items=json.dumps(key_items, ensure_ascii=False),
                key_locations=json.dumps(key_locations, ensure_ascii=False),
                organizations=json.dumps(organizations, ensure_ascii=False),
                terms=json.dumps(terms, ensure_ascii=False),
                # 时间线完整数据
                current_year=timeline.get("current_year", ""),
                era_summary=timeline.get("era_summary", ""),
                events=json.dumps(events, ensure_ascii=False),
                # 氛围完整数据
                overall_mood=atmosphere.get("overall_mood", ""),
                visual_style=atmosphere.get("visual_style", ""),
                scene_presets=json.dumps(scene_presets, ensure_ascii=False),
                # 势力完整数据
                factions_json=json.dumps(factions_list, ensure_ascii=False),
                key_npcs=json.dumps(key_npcs, ensure_ascii=False),
                relation_map=json.dumps(relation_map, ensure_ascii=False),
                conflict_points=", ".join(factions.get("conflict_points", []))
            )

            if "report_id" not in result:
                result["report_id"] = f"consistency_{uuid.uuid4().hex[:8]}"

            report = ConsistencyReport(**result)
            self._log_success(report)
            return report

        except Exception as e:
            log.error(f"WorldConsistencyAgent 处理失败: {e}")
            raise RuntimeError(f"一致性检查失败: {e}") from e

    def _log_success(self, report: ConsistencyReport) -> None:
        """记录成功日志"""
        log.info(f"一致性检查完成: {report.overall_status}")
        log.info(f"  发现问题: {report.total_issues}个")

        critical = report.get_critical_issues()
        high = report.get_issues_by_severity("high")

        if critical:
            log.warning(f"  关键问题: {len(critical)}个")
        if high:
            log.info(f"  高优先级: {len(high)}个")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """验证输出"""
        # 检查overall_status
        status = output.get("overall_status")
        if status not in self.STATUSES:
            return f"overall_status必须是: {', '.join(self.STATUSES)}"

        # 检查total_issues
        total_issues = output.get("total_issues")
        if not isinstance(total_issues, int) or total_issues < 0:
            return "total_issues必须是非负整数"

        # 检查summary
        if not output.get("summary"):
            return "summary不能为空"

        # 检查issues
        issues = output.get("issues")
        if issues is not None:
            if not isinstance(issues, list):
                return "issues必须是数组类型"

            for i, issue in enumerate(issues):
                if not isinstance(issue, dict):
                    return f"issues[{i}]必须是对象"

                if not issue.get("issue_id"):
                    return f"issues[{i}]缺少issue_id"

                category = issue.get("category")
                if category not in self.CATEGORIES:
                    return f"issues[{i}]的category必须是: {', '.join(self.CATEGORIES)}"

                severity = issue.get("severity")
                if severity not in self.SEVERITIES:
                    return f"issues[{i}]的severity必须是: {', '.join(self.SEVERITIES)}"

                if not issue.get("source_agent"):
                    return f"issues[{i}]缺少source_agent"
                if not issue.get("description"):
                    return f"issues[{i}]缺少description"
                if not issue.get("fix_suggestion"):
                    return f"issues[{i}]缺少fix_suggestion"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        return {
            "report_id": f"consistency_fallback_{uuid.uuid4().hex[:8]}",
            "overall_status": "warning",
            "total_issues": 1,
            "issues": [
                {
                    "issue_id": "fallback_1",
                    "category": "suggestion",
                    "severity": "low",
                    "source_agent": "System",
                    "description": "使用降级响应，请手动检查一致性",
                    "fix_suggestion": "请人工审核世界观设定",
                    "is_fixed": False
                }
            ],
            "summary": "由于系统错误，无法完成完整的一致性检查，请人工审核",
            "fallback": True
        }


if __name__ == "__main__":
    # 测试WorldConsistencyAgent
    agent = WorldConsistencyAgent()

    test_data = {
        "story_constraints": {
            "genre": "恋爱",
            "themes": ["青春", "成长"],
            "tone": "温馨"
        },
        "world_setting": {
            "era": "现代",
            "location": "高中",
            "type": "现实",
            "core_conflict_source": "青春的选择",
            "description": "普通的高中校园",
            "rules": [{"rule_id": "r1", "description": "规则1"}]
        },
        "key_elements": {
            "items": [{"item_id": "i1", "name": "道具1"}],
            "locations": [{"location_id": "l1", "name": "地点1"}],
            "organizations": [],
            "terms": []
        },
        "timeline": {
            "current_year": "2024年",
            "era_summary": "普通的时代",
            "events": []
        },
        "atmosphere": {
            "overall_mood": "温馨",
            "visual_style": "清新治愈",
            "scene_presets": []
        },
        "factions": {
            "factions": [],
            "key_npcs": [],
            "relation_map": {},
            "conflict_points": []
        }
    }

    try:
        report = agent.process(**test_data)
        print("\n" + "=" * 50)
        print("WorldConsistencyAgent 测试成功!")
        print("=" * 50)
        print(f"状态: {report.overall_status}")
        print(f"问题数: {report.total_issues}")
        print(f"总结: {report.summary}")
        print("=" * 50)
    except Exception as e:
        print(f"测试失败: {e}")
