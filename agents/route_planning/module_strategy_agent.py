"""
Module Strategy Agent
四模块策略规划 Agent - 将故事分为起承转合四个模块，分别规划策略
"""
import uuid
from typing import Dict, Any, List

from pydantic import BaseModel, Field

from agents.base_agent import BaseAgent
from prompts.route_planning.module_strategy_prompt import (
    MODULE_STRATEGY_SYSTEM_PROMPT,
    MODULE_STRATEGY_PROMPT
)
from utils.logger import log


class ModuleStrategy(BaseModel):
    """四模块策略"""
    strategy_id: str = Field(..., description="策略ID")
    source_outline: str = Field(..., description="来源大纲ID")
    total_chapters: int = Field(..., description="总章节数")
    modules: List[Dict[str, Any]] = Field(..., description="四模块策略列表")


class ModuleStrategyAgent(BaseAgent):
    """
    四模块策略规划Agent

    按照起承转合结构，将故事分为四个模块，分别规划策略
    """
    name = "ModuleStrategyAgent"
    system_prompt = MODULE_STRATEGY_SYSTEM_PROMPT
    human_prompt_template = MODULE_STRATEGY_PROMPT
    required_fields = ["strategy_id", "total_chapters", "modules"]
    output_model = ModuleStrategy

    # 四模块定义
    MODULE_TYPES = {
        "起": "introduction",
        "承": "development",
        "转": "twist",
        "合": "resolution"
    }

    def process(
        self,
        story_outline_data: Dict[str, Any],
        user_idea: str = "",
        total_chapters: int = 27,
        route_strategy_text: str = ""
    ) -> ModuleStrategy:
        """
        处理四模块策略规划

        Args:
            story_outline_data: 故事大纲数据
            user_idea: 用户创意
            total_chapters: 总章节数
            route_strategy_text: 整体路线战略意见
        """
        if not story_outline_data:
            raise ValueError("story_outline_data不能为空")

        steps = story_outline_data.get("steps", {})
        if not steps:
            raise ValueError("story_outline_data中缺少steps数据")

        if not user_idea:
            user_idea = story_outline_data.get("input", {}).get("user_idea", "")

        log.info(f"规划四模块策略（总章节数：{total_chapters}）...")

        # 构建故事数据
        import json
        relevant_data = {
            "premise": steps.get("premise", {}),
            "cast_arc": steps.get("cast_arc", {}),
            "conflict_map": steps.get("conflict_engine", {}).get("map", {})
        }
        steps_json = json.dumps(relevant_data, ensure_ascii=False, separators=(',', ':'))

        # 如果没有提供路线战略，使用空字符串
        if not route_strategy_text:
            route_strategy_text = "（暂无整体路线战略意见，请自行规划）"

        try:
            result = self.run(
                user_idea=user_idea,
                steps_data=steps_json,
                route_strategy_text=route_strategy_text,
                total_chapters=total_chapters
            )

            if "strategy_id" not in result:
                result["strategy_id"] = f"module_strategy_{uuid.uuid4().hex[:8]}"

            if "source_outline" not in result:
                result["source_outline"] = steps.get("conflict_engine", {}).get("map", {}).get("conflict_map_id", "")

            if "total_chapters" not in result:
                result["total_chapters"] = total_chapters

            strategy = ModuleStrategy(**result)
            self._log_success(strategy)
            return strategy

        except Exception as e:
            log.error(f"ModuleStrategyAgent 失败: {e}")
            raise RuntimeError(f"四模块策略规划失败: {e}") from e

    def _log_success(self, strategy: ModuleStrategy) -> None:
        """记录成功日志"""
        log.info("四模块策略生成成功:")
        log.info(f"  策略ID: {strategy.strategy_id}")
        log.info(f"  来源大纲: {strategy.source_outline}")
        log.info(f"  总章节数: {strategy.total_chapters}")
        log.info(f"  模块数: {len(strategy.modules)}")

        for module in strategy.modules:
            module_name = module.get("module_name", "未知")
            chapter_range = module.get("chapter_range", {})
            log.info(f"    - {module_name}: 第{chapter_range.get('start', '?')}章到第{chapter_range.get('end', '?')}章")

    def validate_output(self, output: Dict[str, Any]) -> bool | str:
        """验证输出"""
        modules = output.get("modules")
        if not isinstance(modules, list) or len(modules) != 4:
            return "modules必须是包含4个元素的数组"

        module_names = {"起", "承", "转", "合"}
        for i, module in enumerate(modules):
            if not isinstance(module, dict):
                return f"模块{i}必须是对象"

            module_name = module.get("module_name")
            if module_name not in module_names:
                return f"模块{i}的module_name必须是起/承/转/合之一"

        return True

    def get_module_plan(self, strategy: ModuleStrategy, module_name: str) -> Dict[str, Any]:
        """获取指定模块的策略"""
        for module in strategy.modules:
            if module.get("module_name") == module_name:
                return module
        raise ValueError(f"未找到模块: {module_name}")
