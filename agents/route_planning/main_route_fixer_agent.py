"""
Main Route Fixer Agent
主线框架修复 Agent - 直接修改主线框架中的路线设计问题
"""
from typing import Dict, Any, List, Optional, Union
import uuid
import json

from agents.base_agent import BaseAgent
from prompts.route_planning.main_route_fixer_prompt import (
    MAIN_ROUTE_FIXER_SYSTEM_PROMPT,
    MAIN_ROUTE_FIXER_PROMPT
)
from utils.logger import log


class MainRouteFixerAgent(BaseAgent):
    """
    主线框架修复Agent

    功能:
    - 直接修改主线框架中的路线设计问题
    - 修复分支可达性问题
    - 修复结局可达性问题
    - 修复数值平衡问题
    - 修复分支跨度问题
    - 修复无效选择问题
    - 不修改剧情内容（summary、scene、desc等）
    """

    name = "MainRouteFixerAgent"
    system_prompt = MAIN_ROUTE_FIXER_SYSTEM_PROMPT
    human_prompt_template = MAIN_ROUTE_FIXER_PROMPT
    required_fields = ["structure_id", "state", "branches", "endings", "chapters"]

    def process(
        self,
        route_framework: Dict[str, Any],
        issues: List[Dict[str, Any]],
        fix_round: int = 1
    ) -> Dict[str, Any]:
        """
        处理主线框架修复

        Args:
            route_framework: 主线框架数据
            issues: 检查报告中的问题列表
            fix_round: 当前修复轮次

        Returns:
            修复后的主线框架
        """
        log.info(f"执行主线框架修复（第{fix_round}轮），共{len(issues)}个问题...")

        route_json = json.dumps(route_framework, ensure_ascii=False, indent=2)
        issues_json = json.dumps(issues, ensure_ascii=False, indent=2)

        # 构建轮次信息
        fix_round_info = ""
        if fix_round > 1:
            fix_round_info = f"【修复轮次】这是第{fix_round}轮修复。之前的修复可能没有完全解决问题，请继续修复以下问题。\n"
        else:
            fix_round_info = "【修复轮次】这是第1轮修复。请仔细修复以下问题。\n"

        try:
            result = self.run(
                route_framework_json=route_json,
                issues_json=issues_json,
                fix_round_info=fix_round_info
            )

            # 保留原始ID
            if "structure_id" not in result:
                result["structure_id"] = route_framework.get("structure_id", f"route_fixed_{uuid.uuid4().hex[:8]}")

            # 添加修复标记
            result["fixed"] = True
            result["fix_count"] = len(issues)
            result["fix_round"] = fix_round

            self._log_success(result, len(issues))
            return result

        except Exception as e:
            log.error(f"MainRouteFixerAgent 处理失败: {e}")
            raise RuntimeError(f"主线框架修复失败: {e}") from e

    def _log_success(self, result: Dict[str, Any], issue_count: int) -> None:
        """记录成功日志"""
        log.info(f"主线框架修复完成")
        log.info(f"  结构ID: {result.get('structure_id')}")
        log.info(f"  章节数: {len(result.get('chapters', []))}")
        log.info(f"  分支数: {len(result.get('branches', []))}")
        log.info(f"  结局数: {len(result.get('endings', []))}")
        if issue_count > 0:
            log.info(f"  修复问题: {issue_count}个")

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """验证输出"""
        # 检查必需字段
        for field in self.required_fields:
            if field not in output:
                return f"缺少必需字段: {field}"

        # 检查state
        state = output.get("state")
        if not isinstance(state, dict):
            return "state必须是对象"

        # 检查branches
        branches = output.get("branches")
        if branches is not None and not isinstance(branches, list):
            return "branches必须是数组"

        # 检查endings
        endings = output.get("endings")
        if endings is not None and not isinstance(endings, list):
            return "endings必须是数组"

        # 检查chapters
        chapters = output.get("chapters")
        if not isinstance(chapters, list) or not chapters:
            return "chapters必须是非空数组"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        return {
            "structure_id": f"main_route_fixer_fallback_{uuid.uuid4().hex[:8]}",
            "state": {},
            "branches": [],
            "endings": [],
            "chapters": [],
            "fallback": True
        }
