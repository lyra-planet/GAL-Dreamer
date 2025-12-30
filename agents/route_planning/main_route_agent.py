"""
Main Route Agent
主线框架规划 Agent - 根据策略文本生成主线章节
"""
import uuid
from typing import Dict, Any, List

from agents.base_agent import BaseAgent
from prompts.route_planning.main_route_prompt import (
    MAIN_ROUTE_SYSTEM_PROMPT,
    MAIN_ROUTE_PROMPT
)
from pydantic import BaseModel, Field
from utils.logger import log


class MainRouteFramework(BaseModel):
    """主线框架"""
    structure_id: str = Field(..., description="结构ID")
    source_outline: str = Field(..., description="来源ID")
    total_estimated_chapters: int = Field(..., description="预计总章节数")
    common_ratio: float = Field(..., description="共通线占比")
    state: Dict[str, Any] = Field(..., description="状态框架（好感度）")
    branches: List[Dict[str, Any]] = Field(default_factory=list, description="分支框架列表")
    endings: List[Dict[str, Any]] = Field(default_factory=list, description="结局分支框架列表")
    chapters: List[Dict[str, Any]] = Field(..., description="章节列表")


class MainRouteAgent(BaseAgent):
    """
    主线框架规划Agent

    根据路线战略文本，生成主线（共通线）的详细章节框架
    """
    name = "MainRouteAgent"
    system_prompt = MAIN_ROUTE_SYSTEM_PROMPT
    human_prompt_template = MAIN_ROUTE_PROMPT
    required_fields = ["structure_id", "state", "branches", "endings", "chapters"]
    output_model = MainRouteFramework

    def process(
        self,
        story_outline_data: Dict[str, Any],
        strategy_text: str,
        user_idea: str = "",
        previous_issues: List[Dict[str, Any]] = None
    ) -> MainRouteFramework:
        """
        处理主线框架规划

        Args:
            story_outline_data: 故事大纲数据
            strategy_text: 路线战略文本
            user_idea: 用户创意
            previous_issues: 之前检查出的问题列表（可选），用于改进生成
        """
        if not story_outline_data:
            raise ValueError("story_outline_data不能为空")

        steps = story_outline_data.get("steps", {})
        if not steps:
            raise ValueError("story_outline_data中缺少steps数据")

        if not user_idea:
            user_idea = story_outline_data.get("input", {}).get("user_idea", "")

        log.info("规划共通线（主线）框架...")

        # 构建修改意见部分
        feedback_section = ""
        steps_json = ""

        if previous_issues:
            # 修复模式：优先传递修改意见，不传递完整故事数据
            log.info(f"修复模式：根据{len(previous_issues)}个问题重新生成")
            feedback_section = "\n【重要：修复模式】\n"
            feedback_section += "你正在修复之前版本的路线设计问题。请优先解决以下问题：\n\n"

            # 按严重程度排序
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            sorted_issues = sorted(previous_issues, key=lambda x: severity_order.get(x.get('severity', 'low'), 3))

            for i, issue in enumerate(sorted_issues, 1):
                severity = issue.get('severity', 'unknown')
                category = issue.get('category', 'unknown')
                description = issue.get('description', '')
                suggestion = issue.get('fix_suggestion', '')
                location = issue.get('location', '')

                feedback_section += f"\n{i}. [{severity.upper()}] {category}\n"
                if location:
                    feedback_section += f"   位置: {location}\n"
                feedback_section += f"   问题: {description}\n"
                if suggestion:
                    feedback_section += f"   建议: {suggestion}\n"

            feedback_section += "\n请严格按照路线战略文本生成新的主线框架，同时确保上述问题得到解决。"
            steps_data_section = ""  # 修复模式不传递故事数据
        else:
            # 正常生成模式：传递故事数据
            import json
            relevant_data = {
                "premise": steps.get("premise", {}),
                "cast_arc": steps.get("cast_arc", {}),
                "conflict_map": steps.get("conflict_engine", {}).get("map", {})
            }
            steps_json = json.dumps(relevant_data, ensure_ascii=False, separators=(',', ':'))
            steps_data_section = f"【故事数据】\n{steps_json}\n"
            feedback_section = ""

        try:
            result = self.run(
                user_idea=user_idea,
                steps_data_section=steps_data_section,
                strategy_text=strategy_text,
                feedback_section=feedback_section
            )

            if "structure_id" not in result:
                result["structure_id"] = f"main_route_{uuid.uuid4().hex[:8]}"

            if "source_outline" not in result:
                result["source_outline"] = steps.get("conflict_engine", {}).get("map", {}).get("conflict_map_id", "")

            framework = MainRouteFramework(**result)
            self._log_success(framework)
            return framework

        except Exception as e:
            log.error(f"MainRouteAgent 失败: {e}")
            raise RuntimeError(f"主线框架规划失败: {e}") from e

    def _log_success(self, framework: MainRouteFramework) -> None:
        chapters = framework.chapters
        log.info("共通线（主线）框架生成成功:")
        log.info(f"  结构ID: {framework.structure_id}")
        log.info(f"  预计总章节: {framework.total_estimated_chapters}章")
        log.info(f"  共通线占比: {framework.common_ratio*100:.0f}%")
        log.info(f"  章节数: {len(chapters)}章")

        # 统计选择点
        choice_count = sum(len(ch.get('choices', [])) for ch in chapters)
        log.info(f"  选择点数量: {choice_count}个")

    def validate_output(self, output: Dict[str, Any]) -> bool | str:
        state = output.get("state")
        if not isinstance(state, dict):
            return "state必须是对象"
        branches = output.get("branches")
        if not isinstance(branches, list):
            return "branches必须是数组"
        endings = output.get("endings")
        if not isinstance(endings, list):
            return "endings必须是数组"
        chapters = output.get("chapters")
        if not isinstance(chapters, list):
            return "chapters必须是数组"
        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        return {
            "structure_id": f"main_route_fallback_{uuid.uuid4().hex[:8]}",
            "source_outline": "fallback",
            "total_estimated_chapters": 20,
            "common_ratio": 0.7,
            "state": {
                "heroine_001": {"initial": 0, "min": 0, "max": 100, "description": "女主1好感度"}
            },
            "branches": [],
            "endings": [],
            "chapters": [
                {"id": "common_ch1", "summary": "故事开始", "scene": "", "choices": []}
            ],
            "fallback": True
        }
