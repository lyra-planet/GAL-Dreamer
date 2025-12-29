"""
Worldbuilding Agent
世界观构建 Agent - 构建故事世界背景和规则
"""
from typing import Dict, Any, List, Optional, Union

from agents.base_agent import BaseAgent
from prompts.worldbuilding.worldbuilding_prompt import (
    WORLDBUILDING_SYSTEM_PROMPT,
    WORLDBUILDING_HUMAN_PROMPT
)
from models.worldbuilding.world import WorldSetting
from utils.logger import log


class WorldbuildingAgent(BaseAgent):
    """
    世界观构建Agent

    功能:
    - 根据故事约束构建世界观
    - 定义时代背景、地点、类型
    - 设定世界规则
    - 确定核心冲突来源
    """

    # 类属性配置
    name = "WorldbuildingAgent"
    system_prompt = WORLDBUILDING_SYSTEM_PROMPT
    human_prompt_template = WORLDBUILDING_HUMAN_PROMPT
    required_fields = ["era", "location", "type", "rules", "core_conflict_source", "description"]
    output_model = WorldSetting  # 用于完整 Pydantic 验证

    def process(
        self,
        story_constraints: Dict[str, Any],
        genre: str,
        themes: List[str],
        user_idea: str = "",
        validate: bool = True
    ) -> WorldSetting:
        """
        处理世界观构建

        Args:
            story_constraints: 故事约束条件
            genre: 题材
            themes: 主题列表
            user_idea: 用户原始创意
            validate: 是否验证输出(默认True)

        Returns:
            WorldSetting: 世界观设定

        Raises:
            ValueError: 必需参数为空时
            RuntimeError: 处理失败时
        """
        # 参数验证
        if not genre or not genre.strip():
            raise ValueError("genre不能为空")
        if not themes:
            raise ValueError("themes不能为空")

        themes_str = ", ".join(themes) if isinstance(themes, list) else themes
        log.info(f"构建世界观 - 题材: {genre}, 主题: {themes_str}")

        try:
            result = self.run(
                story_constraints=story_constraints,
                genre=genre,
                themes=themes_str,
                user_idea=user_idea
            )

            # 设置默认的 setting_id
            if "setting_id" not in result:
                import uuid
                result["setting_id"] = f"world_{uuid.uuid4().hex[:8]}"

            world_setting = WorldSetting(**result)
            self._log_success(world_setting)
            return world_setting

        except Exception as e:
            log.error(f"WorldbuildingAgent 处理失败: {e}")
            raise RuntimeError(f"世界观构建失败: {e}") from e

    def _log_success(self, world_setting: WorldSetting) -> None:
        """记录成功日志"""
        log.info("世界观构建成功:")
        log.info(f"  时代: {world_setting.era}")
        log.info(f"  地点: {world_setting.location}")
        log.info(f"  类型: {world_setting.type}")
        log.info(f"  核心冲突: {self._truncate(world_setting.core_conflict_source, 50)}...")
        log.info(f"  规则数量: {len(world_setting.rules)}")

    def _truncate(self, text: str, max_length: int) -> str:
        """截断文本"""
        return text[:max_length] if len(text) > max_length else text

    def validate_output(self, output: Dict[str, Any]) -> Union[bool, str]:
        """
        验证输出是否有效

        Args:
            output: Agent输出

        Returns:
            True: 验证通过
            str: 验证失败的错误信息
        """
        # 检查era
        era = output.get("era")
        if not era or not isinstance(era, str) or not era.strip():
            return "era必须是非空字符串"

        # 检查location
        location = output.get("location")
        if not location or not isinstance(location, str) or not location.strip():
            return "location必须是非空字符串"

        # 检查type
        world_type = output.get("type")
        if not world_type or not isinstance(world_type, str) or not world_type.strip():
            return "type必须是非空字符串"

        # 检查rules
        rules = output.get("rules")
        if not isinstance(rules, list):
            return "rules必须是数组类型"
        if len(rules) == 0:
            return "rules不能为空，至少需要1条规则"
        if not all(isinstance(r, dict) for r in rules):
            return "rules中的所有元素必须是对象"

        # 检查每条规则的结构
        for i, rule in enumerate(rules):
            if not isinstance(rule, dict):
                return f"rules[{i}]必须是对象"
            if "rule_id" not in rule or not rule["rule_id"]:
                return f"rules[{i}]缺少rule_id字段"
            if "description" not in rule or not rule["description"]:
                return f"rules[{i}]缺少description字段"

        # 检查core_conflict_source
        conflict = output.get("core_conflict_source")
        if not conflict or not isinstance(conflict, str) or not conflict.strip():
            return "core_conflict_source必须是非空字符串"

        # 检查description
        description = output.get("description")
        if not description or not isinstance(description, str) or not description.strip():
            return "description必须是非空字符串"

        # 检查special_elements(可选)
        special_elements = output.get("special_elements")
        if special_elements is not None:
            if not isinstance(special_elements, list):
                return "special_elements必须是数组类型"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        import uuid
        return {
            "setting_id": f"world_fallback_{uuid.uuid4().hex[:8]}",
            "era": "现代",
            "location": "普通城市",
            "type": "现实",
            "rules": [
                {
                    "rule_id": "default_1",
                    "description": "世界遵循基本的物理法则",
                    "is_breakable": False
                }
            ],
            "core_conflict_source": "待定",
            "description": "默认世界观设定",
            "special_elements": [],
            "fallback": True
        }


if __name__ == "__main__":
    # 测试Worldbuilding Agent
    agent = WorldbuildingAgent()

    test_constraints = {
        "genre": "恋爱",
        "themes": ["青春", "成长"],
        "tone": "温馨",
        "must_have": ["多女主", "多结局"],
        "forbidden": ["超自然"]
    }

    try:
        world = agent.process(
            story_constraints=test_constraints,
            genre="恋爱",
            themes=["青春", "成长"]
        )
        print("\n" + "=" * 50)
        print("Worldbuilding Agent 测试成功!")
        print("=" * 50)
        print(f"ID: {world.setting_id}")
        print(f"时代: {world.era}")
        print(f"地点: {world.location}")
        print(f"类型: {world.type}")
        print(f"核心冲突: {world.core_conflict_source}")
        print(f"规则数量: {len(world.rules)}")
        print("=" * 50)
    except Exception as e:
        print(f"测试失败: {e}")
