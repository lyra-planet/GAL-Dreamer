"""
Route Consistency Agent
路线一致性检查 Agent - 检查路线设计问题（使用脚本检查）
"""
from typing import Dict, Any, List, Optional, Union
import uuid
import json

from agents.base_agent import BaseAgent
from utils.route_consistency_checker import check_route_consistency
from utils.logger import log


class RouteConsistencyAgent(BaseAgent):
    """
    路线一致性检查Agent

    使用脚本直接检查，不使用LLM

    功能:
    - 检查分支可达性
    - 检查结局可达性
    - 检查数值平衡
    - 检查分支跨度
    - 检查选择意义
    """

    name = "RouteConsistencyAgent"
    # 不再需要 system_prompt 和 human_prompt_template
    required_fields = ["overall_status", "total_issues", "summary"]

    # 问题类型
    CATEGORIES = [
        "branch_unreachable",    # 分支不可达
        "ending_unreachable",    # 结局不可达
        "numeric_issue",         # 数值问题
        "span_issue",            # 跨度问题
        "invalid_choice",        # 无效选择
        "missing_field"          # 缺失字段
    ]
    # 严重程度
    SEVERITIES = ["low", "medium", "high", "critical"]

    def process(
        self,
        route_framework: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理路线一致性检查

        Args:
            route_framework: 主线框架数据

        Returns:
            检查报告
        """
        log.info("执行路线一致性检查（脚本模式）...")

        try:
            result = check_route_consistency(route_framework)

            if "report_id" not in result:
                result["report_id"] = f"route_consistency_{uuid.uuid4().hex[:8]}"

            self._log_success(result)
            return result

        except Exception as e:
            log.error(f"RouteConsistencyAgent 处理失败: {e}")
            raise RuntimeError(f"路线一致性检查失败: {e}") from e

    def _log_success(self, report: Dict[str, Any]) -> None:
        """记录成功日志"""
        log.info(f"路线一致性检查完成: {report.get('overall_status')}")
        log.info(f"  总问题: {report.get('total_issues')}个")

        issues = report.get("issues", [])
        critical = [i for i in issues if i.get("severity") == "critical"]
        high = [i for i in issues if i.get("severity") == "high"]

        if critical:
            log.warning(f"  关键问题: {len(critical)}个")
        if high:
            log.warning(f"  高优先级: {len(high)}个")
