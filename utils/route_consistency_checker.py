"""
路线一致性检查脚本 - 直接检查不使用LLM
"""
import json
from typing import Dict, Any, List
from pathlib import Path


class RouteConsistencyChecker:
    """路线一致性检查器"""

    def __init__(self, route_framework: Dict[str, Any]):
        self.route = route_framework
        self.issues = []

    def check_all(self) -> Dict[str, Any]:
        """执行所有检查"""
        self.issues = []

        self.check_branch_reachability()
        self.check_ending_reachability()
        self.check_numeric_balance()
        self.check_span_issues()
        self.check_invalid_choices()

        # 确定整体状态
        critical_count = sum(1 for i in self.issues if i['severity'] == 'critical')
        high_count = sum(1 for i in self.issues if i['severity'] == 'high')

        if critical_count > 0:
            overall_status = "failed"
        elif high_count > 0:
            overall_status = "warning"
        else:
            overall_status = "passed"

        return {
            "overall_status": overall_status,
            "total_issues": len(self.issues),
            "summary": self._generate_summary(),
            "issues": self.issues
        }

    def check_branch_reachability(self):
        """检查分支可达性"""
        branches = self.route.get('branches', [])
        branch_ids = [b['id'] for b in branches]

        # 收集被引用的branch
        referenced_branches = self._get_referenced_branches()

        # 找出未引用的分支
        for branch_id in branch_ids:
            if branch_id not in referenced_branches:
                self.issues.append({
                    "issue_id": f"branch_{branch_id}",
                    "category": "branch_unreachable",
                    "severity": "high",
                    "description": f"分支 {branch_id} 没有被任何选择的branch字段引用",
                    "location": f"branches.{branch_id}",
                    "fix_suggestion": f"在某个章节的choices中添加一个选项，branch指向 {branch_id}"
                })

        # 检查分支入口数量
        branch_ref_count = {}
        for ch in self.route.get('chapters', []):
            for choice in ch.get('choices', []):
                branch = choice.get('branch')
                if branch and branch.startswith('branch_'):
                    branch_ref_count[branch] = branch_ref_count.get(branch, 0) + 1

        for branch_id, count in branch_ref_count.items():
            if count > 2:
                self.issues.append({
                    "issue_id": f"branch_multiple_{branch_id}",
                    "category": "branch_unreachable",
                    "severity": "medium",
                    "description": f"分支 {branch_id} 有 {count} 个入口，建议不超过2个",
                    "location": f"branches.{branch_id}",
                    "fix_suggestion": f"删除多余的入口，只保留1-2个"
                })

    def check_ending_reachability(self):
        """检查结局可达性"""
        endings = self.route.get('endings', [])
        ending_ids = [e['id'] for e in endings]

        # 收集被引用的ending
        referenced_endings = self._get_referenced_endings()

        # 找出未引用的结局
        for ending_id in ending_ids:
            if ending_id not in referenced_endings:
                self.issues.append({
                    "issue_id": f"ending_{ending_id}",
                    "category": "ending_unreachable",
                    "severity": "critical",
                    "description": f"结局 {ending_id} 没有被任何选择的branch字段引用",
                    "location": f"endings.{ending_id}",
                    "fix_suggestion": f"在最终章的choices中添加一个选项，branch指向 {ending_id}"
                })

    def check_numeric_balance(self):
        """检查数值平衡"""
        chapters = self.route.get('chapters', [])
        chapter_index = {ch['id']: i for i, ch in enumerate(chapters, 1)}

        for ch in chapters:
            ch_id = ch['id']
            idx = chapter_index.get(ch_id, 0)

            for choice in ch.get('choices', []):
                # 检查visible条件
                visible = choice.get('visible')
                if visible and isinstance(visible, dict):
                    for heroine_id, value in visible.items():
                        if idx <= 3 and value > 10:
                            self.issues.append({
                                "issue_id": f"visible_{ch_id}_{choice.get('id')}",
                                "category": "numeric_issue",
                                "severity": "medium",
                                "description": f"第{idx}章 {ch_id} 的选项 {choice.get('id')} visible条件过高({value})",
                                "location": f"chapters.{ch_id}.choices.{choice.get('id')}.visible",
                                "fix_suggestion": f"将visible改为null或不超过10的数值"
                            })
                        elif value > 70:
                            self.issues.append({
                                "issue_id": f"visible_{ch_id}_{choice.get('id')}",
                                "category": "numeric_issue",
                                "severity": "medium",
                                "description": f"第{idx}章 {ch_id} 的选项 {choice.get('id')} visible条件过高({value})",
                                "location": f"chapters.{ch_id}.choices.{choice.get('id')}.visible",
                                "fix_suggestion": f"将visible改为不超过70的数值"
                            })

                # 检查effect数值
                effect = choice.get('effect', {})
                if effect and isinstance(effect, dict):
                    for heroine_id, value in effect.items():
                        if isinstance(value, int) and abs(value) > 20:
                            self.issues.append({
                                "issue_id": f"effect_{ch_id}_{choice.get('id')}",
                                "category": "numeric_issue",
                                "severity": "medium",
                                "description": f"选项 {choice.get('id')} 的effect值({value})超出合理范围",
                                "location": f"chapters.{ch_id}.choices.{choice.get('id')}.effect",
                                "fix_suggestion": f"将effect调整为+10到+20之间"
                            })

        # 检查分支reward
        for branch in self.route.get('branches', []):
            reward = branch.get('reward', {})
            if reward and isinstance(reward, dict):
                for heroine_id, value in reward.items():
                    if isinstance(value, int) and (value < 20 or value > 45):
                        self.issues.append({
                            "issue_id": f"reward_{branch.get('id')}",
                            "category": "numeric_issue",
                            "severity": "low",
                            "description": f"分支 {branch.get('id')} 的reward值({value})可能不合理",
                            "location": f"branches.{branch.get('id')}.reward",
                            "fix_suggestion": f"将reward调整为+25到+40之间"
                        })

    def check_span_issues(self):
        """检查分支跨度"""
        chapters = self.route.get('chapters', [])
        chapter_index = {ch['id']: i for i, ch in enumerate(chapters, 1)}

        for branch in self.route.get('branches', []):
            branch_id = branch.get('id')
            return_ch = branch.get('return')

            # 找到这个分支的入口章节
            entry_chapter = None
            for ch in chapters:
                for choice in ch.get('choices', []):
                    if choice.get('branch') == branch_id:
                        entry_chapter = ch['id']
                        break
                if entry_chapter:
                    break

            if entry_chapter and return_ch:
                entry_idx = chapter_index.get(entry_chapter, 0)
                return_idx = chapter_index.get(return_ch, 0)

                if entry_idx > 0 and return_idx > 0:
                    span = return_idx - entry_idx
                    if span > 3:
                        self.issues.append({
                            "issue_id": f"span_{branch_id}",
                            "category": "span_issue",
                            "severity": "high",
                            "description": f"分支 {branch_id} 从第{entry_idx}章进入，返回第{return_idx}章，跨度{span}章超过限制",
                            "location": f"branches.{branch_id}",
                            "fix_suggestion": f"将return章节改为第{entry_idx + 3}章或更早的章节"
                        })

    def check_invalid_choices(self):
        """检查无效选择"""
        for ch in self.route.get('chapters', []):
            ch_id = ch['id']
            for choice in ch.get('choices', []):
                choice_id = choice.get('id', 'unknown')
                branch = choice.get('branch')
                effect = choice.get('effect')

                if branch is None and (not effect or effect == {}):
                    self.issues.append({
                        "issue_id": f"invalid_{ch_id}_{choice_id}",
                        "category": "invalid_choice",
                        "severity": "medium",
                        "description": f"选项 {choice_id} 的branch为null且effect为空",
                        "location": f"chapters.{ch_id}.choices.{choice_id}",
                        "fix_suggestion": f"给该选项添加effect或设置branch"
                    })

    def _get_referenced_branches(self) -> set:
        """获取所有被引用的branch"""
        referenced = set()
        for ch in self.route.get('chapters', []):
            for choice in ch.get('choices', []):
                branch = choice.get('branch')
                if branch and branch.startswith('branch_'):
                    referenced.add(branch)
        return referenced

    def _get_referenced_endings(self) -> set:
        """获取所有被引用的ending"""
        referenced = set()
        for ch in self.route.get('chapters', []):
            for choice in ch.get('choices', []):
                branch = choice.get('branch')
                if branch and branch.startswith('ending_'):
                    referenced.add(branch)
        return referenced

    def _generate_summary(self) -> str:
        """生成摘要"""
        if not self.issues:
            return "没有发现问题"

        # 统计各类问题
        category_count = {}
        for issue in self.issues:
            cat = issue['category']
            category_count[cat] = category_count.get(cat, 0) + 1

        parts = []
        for cat, count in category_count.items():
            cat_name = {
                'branch_unreachable': '分支不可达',
                'ending_unreachable': '结局不可达',
                'numeric_issue': '数值问题',
                'span_issue': '跨度问题',
                'invalid_choice': '无效选择',
                'missing_field': '缺失字段'
            }.get(cat, cat)
            parts.append(f"{count}个{cat_name}")

        return "发现" + "、".join(parts)


def check_route_consistency(route_framework: Dict[str, Any]) -> Dict[str, Any]:
    """
    检查路线一致性

    Args:
        route_framework: 主线框架数据

    Returns:
        检查报告
    """
    checker = RouteConsistencyChecker(route_framework)
    return checker.check_all()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python route_consistency_checker.py <main_route_framework.json>")
        sys.exit(1)

    json_file = sys.argv[1]

    with open(json_file, 'r', encoding='utf-8') as f:
        route_data = json.load(f)

    print("=" * 60)
    print("路线一致性检查")
    print("=" * 60)

    report = check_route_consistency(route_data)

    print(f"\n状态: {report['overall_status']}")
    print(f"问题总数: {report['total_issues']}")
    print(f"摘要: {report['summary']}")

    if report['issues']:
        print("\n发现的问题:")
        for i, issue in enumerate(report['issues'], 1):
            print(f"\n{i}. [{issue['severity']}] {issue['category']}")
            print(f"   描述: {issue['description']}")
            print(f"   位置: {issue['location']}")
            print(f"   建议: {issue['fix_suggestion']}")
    else:
        print("\n✓ 没有发现问题!")

    # 保存报告
    report_file = json_file.replace('.json', '_consistency_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n报告已保存到: {report_file}")
