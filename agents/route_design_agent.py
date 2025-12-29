"""
Route Design Agent
多攻略线/分支设计 Agent
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from prompts.route_design_prompt import (
    ROUTE_DESIGN_SYSTEM_PROMPT,
    ROUTE_DESIGN_HUMAN_PROMPT
)
from models.plot import RouteDesign
from utils.logger import log


class RouteDesignAgent(BaseAgent):
    """多线路设计Agent - 设计多条可攻略线路"""

    def __init__(self):
        """初始化Route Design Agent"""
        super().__init__(
            name="RouteDesignAgent",
            system_prompt=ROUTE_DESIGN_SYSTEM_PROMPT,
            human_prompt_template=ROUTE_DESIGN_HUMAN_PROMPT
        )

    def _get_required_fields(self) -> List[str]:
        """返回必填字段列表"""
        return ["routes", "common_route_length", "branching_strategy"]

    def process(self, macro_plot: Dict[str, Any], heroine_list: list) -> RouteDesign:
        """
        处理多线路设计

        Args:
            macro_plot: 大剧情结构
            heroine_list: 可攻略角色列表

        Returns:
            RouteDesign: 多线路设计
        """
        log.info("设计多线路结构")

        # 格式化女主列表
        heroine_str = "\n".join([f"- {h.get('name', h)}: {h.get('personality_type', '')}" if isinstance(h, dict) else f"- {h}" for h in heroine_list])

        # 运行Agent (带自动验证和修复)
        result = self.run(
            macro_plot=macro_plot,
            heroine_list=heroine_str
        )

        # 转换为RouteDesign对象
        route_design = RouteDesign(**result)

        log.info(f"多线路设计成功:")
        log.info(f"  线路数量: {len(route_design.routes)}")
        log.info(f"  共通线长度: {route_design.common_route_length}")
        log.info(f"  分歧策略: {route_design.branching_strategy}")

        return route_design

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

        # 检查线路列表至少2条
        routes = output.get("routes")
        if not isinstance(routes, list):
            return "routes必须是数组类型"
        if len(routes) < 2:
            return f"routes至少需要2条线路，当前只有{len(routes)}条"

        # 检查每条线路的必需字段
        required_route_fields = ["route_id", "route_name", "heroine_id", "branch_point", "conflict_focus", "ending_types", "route_summary"]
        for i, route in enumerate(routes):
            if not isinstance(route, dict):
                return f"routes[{i}]必须是字典类型"
            for field in required_route_fields:
                if field not in route:
                    return f"routes[{i}]缺少必填字段: {field}"

        return True


if __name__ == "__main__":
    # 测试Route Design Agent
    agent = RouteDesignAgent()

    test_plot = {
        "acts": {
            "act1": "日常展示",
            "act2": "矛盾升级",
            "act3": "真相揭露",
            "act4": "分线发展"
        },
        "story_arc": "一个关于成长的故事"
    }

    test_heroines = [
        {"name": "A", "personality_type": "傲娇"},
        {"name": "B", "personality_type": "温柔"}
    ]

    try:
        routes = agent.process(
            macro_plot=test_plot,
            heroine_list=test_heroines
        )
        print("\n" + "="*50)
        print("Route Design Agent 测试成功!")
        print("="*50)
        for route in routes.routes:
            print(f"{route.route_name}: {route.route_summary}")
        print("="*50)
    except Exception as e:
        print(f"测试失败: {e}")
