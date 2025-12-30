"""
Modular Main Route Agent
模块化主线框架规划 Agent - 按起承转合四模块生成主线章节
"""
import uuid
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field

from agents.base_agent import BaseAgent
from prompts.route_planning.modular_main_route_prompt import (
    MODULAR_MAIN_ROUTE_SYSTEM_PROMPT,
    MODULAR_MAIN_ROUTE_PROMPT
)
from utils.logger import log


class ModuleRouteFramework(BaseModel):
    """单个模块的路线框架"""
    module_name: str = Field(..., description="模块名称（起/承/转/合）")
    module_type: str = Field(..., description="模块类型")
    chapter_range: Dict[str, int] = Field(..., description="章节范围")
    chapters: List[Dict[str, Any]] = Field(..., description="章节列表")
    branches: List[Dict[str, Any]] = Field(default_factory=list, description="本模块新增分支")
    endings: List[Dict[str, Any]] = Field(default_factory=list, description="本模块结局（仅合模块）")
    state_transitions: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="状态变化区间")


class ModularMainRouteAgent(BaseAgent):
    """
    模块化主线框架规划Agent

    按照起承转合四模块，分别生成每个模块的主线章节框架
    """
    name = "ModularMainRouteAgent"
    system_prompt = MODULAR_MAIN_ROUTE_SYSTEM_PROMPT
    human_prompt_template = MODULAR_MAIN_ROUTE_PROMPT
    required_fields = ["module_name", "chapter_range", "chapters"]
    output_model = ModuleRouteFramework

    def __init__(self):
        super().__init__()
        self.generated_modules = {}  # 存储已生成的模块

    def process_module(
        self,
        story_outline_data: Dict[str, Any],
        module_name: str,
        module_type: str,
        chapter_start: int,
        chapter_end: int,
        module_strategy: Dict[str, Any],
        global_state: Optional[Dict[str, Any]] = None,
        global_branches: Optional[List[Dict[str, Any]]] = None,
        global_endings: Optional[List[Dict[str, Any]]] = None,
        user_idea: str = "",
        route_strategy_text: str = "",
        main_plot_summary: str = "",
        chapters: List[Dict[str, Any]] = None,
        previous_issues: List[Dict[str, Any]] = None
    ) -> ModuleRouteFramework:
        """
        处理单个模块的框架规划

        Args:
            story_outline_data: 故事大纲数据
            module_name: 模块名称（起/承/转/合）
            module_type: 模块类型（introduction/development/twist/resolution）
            chapter_start: 起始章节
            chapter_end: 结束章节
            module_strategy: 该模块的策略
            global_state: 全局状态框架（从之前的模块继承）
            global_branches: 全局分支列表
            global_endings: 全局结局列表
            user_idea: 用户创意
            route_strategy_text: 整体路线战略意见
            main_plot_summary: 主线一句话概要
            chapters: 章节规划数组
            previous_issues: 之前检查出的问题列表（修复模式）

        Returns:
            该模块的路线框架
        """
        if not story_outline_data:
            raise ValueError("story_outline_data不能为空")

        steps = story_outline_data.get("steps", {})
        if not steps:
            raise ValueError("story_outline_data中缺少steps数据")

        if not user_idea:
            user_idea = story_outline_data.get("input", {}).get("user_idea", "")

        chapter_count = chapter_end - chapter_start + 1
        log.info(f"规划{module_name}模块框架（第{chapter_start}-{chapter_end}章，共{chapter_count}章）...")

        # 构建故事数据（确保传递给LLM）
        story_data_section = ""
        if steps:
            import json
            relevant_data = {
                "premise": steps.get("premise", {}),
                "cast_arc": steps.get("cast_arc", {}),
                "conflict_map": steps.get("conflict_engine", {}).get("map", {})
            }
            story_data_section = "\n【故事大纲数据】\n" + json.dumps(relevant_data, ensure_ascii=False, indent=2)

        # 构建上下文信息
        previous_context = self._build_previous_context(module_name)

        # 构建修改意见
        feedback_section = ""
        if previous_issues:
            feedback_section = self._build_feedback_section(previous_issues)

        # 如果没有提供路线战略，使用空字符串
        if not route_strategy_text:
            route_strategy_text = "（暂无整体路线战略意见）"
        if not chapters:
            chapters = []
        if not main_plot_summary:
            main_plot_summary = ""

        try:
            result = self.run(
                user_idea=user_idea,
                story_data=story_data_section,
                route_strategy_text=route_strategy_text,
                main_plot_summary=main_plot_summary,
                chapters=_format_chapters(chapters) if chapters else "[]",
                module_name=module_name,
                module_type=module_type,
                chapter_start=chapter_start,
                chapter_end=chapter_end,
                chapter_count=chapter_count,
                previous_context=previous_context,
                module_strategy=_format_strategy(module_strategy),
                state_framework=_format_state(global_state) if global_state else "{}",
                global_branches=_format_branches(global_branches) if global_branches else "[]",
                global_endings=_format_endings(global_endings) if global_endings else "[]",
                feedback_section=feedback_section
            )

            # 添加元数据
            result["module_name"] = module_name
            result["module_type"] = module_type
            result["chapter_range"] = {"start": chapter_start, "end": chapter_end}

            framework = ModuleRouteFramework(**result)

            # 保存已生成的模块
            self.generated_modules[module_name] = framework

            self._log_success(framework)
            return framework

        except Exception as e:
            log.error(f"ModularMainRouteAgent 处理{module_name}模块失败: {e}")
            raise RuntimeError(f"{module_name}模块框架规划失败: {e}") from e

    def _build_previous_context(self, module_name: str) -> str:
        """构建前序模块的上下文信息"""
        module_order = ["起", "承", "转", "合"]
        current_index = module_order.index(module_name)

        if current_index == 0:
            return "【前序模块】这是第一个模块（起），没有前序模块的上下文。"

        context_parts = []
        for i in range(current_index):
            prev_module = module_order[i]
            if prev_module in self.generated_modules:
                framework = self.generated_modules[prev_module]
                chapters = framework.chapters
                context_parts.append(f"【{prev_module}模块】")
                context_parts.append(f"  - 章节范围: 第{framework.chapter_range['start']}-{framework.chapter_range['end']}章")
                context_parts.append(f"  - 章节数: {len(chapters)}")

                # 列出章节概要
                for ch in chapters:
                    context_parts.append(f"    {ch.get('id', '')}: {ch.get('summary', '')}")

                # 列出分支
                if framework.branches:
                    context_parts.append(f"  - 分支数: {len(framework.branches)}")
                    for br in framework.branches:
                        context_parts.append(f"    {br.get('id', '')}: {br.get('desc', '')}")

        return "\n".join(context_parts) if context_parts else "【前序模块】无"

    def _build_feedback_section(self, issues: List[Dict[str, Any]]) -> str:
        """构建修复意见部分"""
        feedback = "\n【重要：修复模式】\n"
        feedback += "你正在修复之前版本的路线设计问题。请优先解决以下问题：\n\n"

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_issues = sorted(issues, key=lambda x: severity_order.get(x.get('severity', 'low'), 3))

        for i, issue in enumerate(sorted_issues, 1):
            severity = issue.get('severity', 'unknown')
            category = issue.get('category', 'unknown')
            description = issue.get('description', '')
            suggestion = issue.get('fix_suggestion', '')
            location = issue.get('location', '')

            feedback += f"\n{i}. [{severity.upper()}] {category}\n"
            if location:
                feedback += f"   位置: {location}\n"
            feedback += f"   问题: {description}\n"
            if suggestion:
                feedback += f"   建议: {suggestion}\n"

        return feedback

    def _log_success(self, framework: ModuleRouteFramework) -> None:
        """记录成功日志"""
        chapters = framework.chapters
        log.info(f"{framework.module_name}模块框架生成成功:")
        log.info(f"  模块类型: {framework.module_type}")
        log.info(f"  章节范围: 第{framework.chapter_range['start']}-{framework.chapter_range['end']}章")
        log.info(f"  章节数: {len(chapters)}章")

        # 统计选择点
        choice_count = sum(len(ch.get('choices', [])) for ch in chapters)
        log.info(f"  选择点数量: {choice_count}个")

        # 统计分支和结局
        if framework.branches:
            log.info(f"  新增分支数: {len(framework.branches)}个")
        if framework.endings:
            log.info(f"  新增结局数: {len(framework.endings)}个")

    def validate_output(self, output: Dict[str, Any]) -> bool | str:
        """验证输出"""
        chapters = output.get("chapters")
        if not isinstance(chapters, list) or not chapters:
            return "chapters必须是非空数组"

        branches = output.get("branches")
        if branches is not None and not isinstance(branches, list):
            return "branches必须是数组"

        endings = output.get("endings")
        if endings is not None and not isinstance(endings, list):
            return "endings必须是数组"

        return True

    def get_all_chapters(self) -> List[Dict[str, Any]]:
        """获取所有已生成的章节"""
        all_chapters = []
        for module_name in ["起", "承", "转", "合"]:
            if module_name in self.generated_modules:
                framework = self.generated_modules[module_name]
                all_chapters.extend(framework.chapters)
        return all_chapters

    def get_all_branches(self) -> List[Dict[str, Any]]:
        """获取所有已生成的分支"""
        all_branches = []
        for module_name in ["起", "承", "转", "合"]:
            if module_name in self.generated_modules:
                framework = self.generated_modules[module_name]
                all_branches.extend(framework.branches)
        return all_branches

    def get_all_endings(self) -> List[Dict[str, Any]]:
        """获取所有已生成的结局"""
        all_endings = []
        for module_name in ["起", "承", "转", "合"]:
            if module_name in self.generated_modules:
                framework = self.generated_modules[module_name]
                all_endings.extend(framework.endings)
        return all_endings

    def clear(self):
        """清除已生成的模块数据"""
        self.generated_modules.clear()


def _format_strategy(strategy: Dict[str, Any]) -> str:
    """格式化策略信息"""
    import json
    return json.dumps(strategy, ensure_ascii=False, indent=2)


def _format_state(state: Dict[str, Any]) -> str:
    """格式化状态框架"""
    import json
    return json.dumps(state, ensure_ascii=False, indent=2)


def _format_branches(branches: List[Dict[str, Any]]) -> str:
    """格式化分支列表"""
    import json
    # 只输出简要信息
    summary = []
    for br in branches:
        summary.append({
            "id": br.get("id"),
            "target": br.get("target"),
            "desc": br.get("desc"),
            "return": br.get("return")
        })
    return json.dumps(summary, ensure_ascii=False, indent=2)


def _format_endings(endings: List[Dict[str, Any]]) -> str:
    """格式化结局列表"""
    import json
    # 只输出简要信息
    summary = []
    for ed in endings:
        summary.append({
            "id": ed.get("id"),
            "target": ed.get("target"),
            "desc": ed.get("desc"),
            "type": ed.get("type")
        })
    return json.dumps(summary, ensure_ascii=False, indent=2)


def _format_chapters(chapters: List[Dict[str, Any]]) -> str:
    """格式化章节规划列表"""
    import json
    return json.dumps(chapters, ensure_ascii=False, indent=2)
