"""
Conflict & Emotion Agent
冲突与情绪引擎 Agent
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from prompts.conflict_emotion_prompt import (
    CONFLICT_EMOTION_SYSTEM_PROMPT,
    CONFLICT_EMOTION_HUMAN_PROMPT
)
from models.plot import ConflictDesign
from utils.logger import log


class ConflictEmotionAgent(BaseAgent):
    """冲突与情绪引擎Agent - 设计剧情冲突和情绪曲线"""

    def __init__(self):
        """初始化Conflict & Emotion Agent"""
        super().__init__(
            name="ConflictEmotionAgent",
            system_prompt=CONFLICT_EMOTION_SYSTEM_PROMPT,
            human_prompt_template=CONFLICT_EMOTION_HUMAN_PROMPT
        )

    def _get_required_fields(self) -> List[str]:
        """返回必填字段列表"""
        return ["conflicts", "emotional_curves"]

    def process(self, route_plots: Dict[str, Any], character_states: Dict[str, Any]) -> ConflictDesign:
        """
        处理冲突和情绪设计

        Args:
            route_plots: 线路剧情
            character_states: 角色状态和关系

        Returns:
            ConflictDesign: 冲突设计
        """
        log.info("设计冲突和情绪曲线")

        # 运行Agent (带自动验证和修复)
        result = self.run(
            route_plots=route_plots,
            character_states=character_states
        )

        # 转换为ConflictDesign对象
        conflict_design = ConflictDesign(**result)

        log.info(f"冲突设计成功:")
        log.info(f"  冲突节点数量: {len(conflict_design.conflicts)}")
        log.info(f"  情绪曲线数量: {len(conflict_design.emotional_curves)}")

        return conflict_design

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

        # 检查冲突节点是列表
        conflicts = output.get("conflicts")
        if not isinstance(conflicts, list):
            return "conflicts必须是数组类型"

        # 检查每个冲突节点的必需字段
        for i, conflict in enumerate(conflicts):
            if not isinstance(conflict, dict):
                return f"conflicts[{i}]必须是字典类型"
            required_conflict_fields = ["node_id", "conflict_type", "emotional_intensity", "description", "resolution_method"]
            for field in required_conflict_fields:
                if field not in conflict:
                    return f"conflicts[{i}]缺少必填字段: {field}"

        return True


if __name__ == "__main__":
    # 测试Conflict & Emotion Agent
    agent = ConflictEmotionAgent()

    test_routes = {
        "routes": [
            {"route_id": "A", "route_name": "A线", "conflict_focus": "信任"},
            {"route_id": "B", "route_name": "B线", "conflict_focus": "成长"}
        ]
    }

    test_characters = {
        "protagonist": {"name": "主角", "core_flaw": "逃避"},
        "heroines": [
            {"name": "A", "secret": "隐瞒真相"},
            {"name": "B", "secret": "过去创伤"}
        ]
    }

    try:
        design = agent.process(
            route_plots=test_routes,
            character_states=test_characters
        )
        print("\n" + "="*50)
        print("Conflict & Emotion Agent 测试成功!")
        print("="*50)
        for conflict in design.conflicts[:3]:
            print(f"{conflict.conflict_type}: {conflict.description[:50]}...")
        print("="*50)
    except Exception as e:
        print(f"测试失败: {e}")
