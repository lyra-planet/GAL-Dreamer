"""
Key Element Agent
关键元素Agent - 设计世界观中的关键道具、地点、组织等
"""
from typing import Dict, Any, List, Optional, Union
import uuid

from agents.base_agent import BaseAgent
from prompts.worldbuilding.key_element_prompt import (
    KEY_ELEMENT_SYSTEM_PROMPT,
    KEY_ELEMENT_HUMAN_PROMPT
)
from models.worldbuilding.key_element import KeyElements
from utils.logger import log


class KeyElementAgent(BaseAgent):
    """
    关键元素Agent

    功能:
    - 设计关键道具(特殊物品)
    - 设计关键地点(重要场所)
    - 设计组织/势力
    - 设计专有名词
    """

    # 类属性配置
    name = "KeyElementAgent"
    system_prompt = KEY_ELEMENT_SYSTEM_PROMPT
    human_prompt_template = KEY_ELEMENT_HUMAN_PROMPT
    required_fields = ["items", "locations", "organizations", "terms"]
    output_model = KeyElements

    # 重要性级别
    IMPORTANCE_LEVELS = ["minor", "major", "critical"]
    # 影响力范围
    INFLUENCE_LEVELS = ["local", "regional", "national", "global"]

    def process(
        self,
        story_constraints: Dict[str, Any],
        world_setting: Dict[str, Any],
        user_idea: str = "",
        validate: bool = True
    ) -> KeyElements:
        """
        处理关键元素生成

        Args:
            story_constraints: 故事约束条件
            world_setting: 世界观设定
            user_idea: 用户原始创意
            validate: 是否验证输出(默认True)

        Returns:
            KeyElements: 关键元素集合

        Raises:
            ValueError: 必需参数为空时
            RuntimeError: 处理失败时
        """
        # 参数验证
        if not story_constraints:
            raise ValueError("story_constraints不能为空")
        if not world_setting:
            raise ValueError("world_setting不能为空")

        log.info("生成关键元素...")

        try:
            result = self.run(
                genre=story_constraints.get("genre", ""),
                themes=", ".join(story_constraints.get("themes", [])),
                tone=story_constraints.get("tone", ""),
                must_have=", ".join(story_constraints.get("must_have", [])),
                era=world_setting.get("era", ""),
                location=world_setting.get("location", ""),
                world_type=world_setting.get("type", ""),
                core_conflict=world_setting.get("core_conflict_source", ""),
                world_description=world_setting.get("description", ""),
                user_idea=user_idea
            )

            # 设置默认的 elements_id
            if "elements_id" not in result:
                result["elements_id"] = f"elements_{uuid.uuid4().hex[:8]}"

            key_elements = KeyElements(**result)
            self._log_success(key_elements)
            return key_elements

        except Exception as e:
            log.error(f"KeyElementAgent 处理失败: {e}")
            raise RuntimeError(f"关键元素生成失败: {e}") from e

    def _log_success(self, key_elements: KeyElements) -> None:
        """记录成功日志"""
        summary = key_elements.get_summary()
        log.info("关键元素生成成功:")
        log.info(f"  道具: {summary['items_count']}个")
        log.info(f"  地点: {summary['locations_count']}个")
        log.info(f"  组织: {summary['organizations_count']}个")
        log.info(f"  术语: {summary['terms_count']}个")

        # 记录重要道具
        for item in key_elements.items:
            if item.importance == "critical":
                log.info(f"  [关键道具] {item.name}: {self._truncate(item.description, 30)}...")

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
        # 验证items
        items = output.get("items")
        if not isinstance(items, list):
            return "items必须是数组类型"
        if len(items) == 0:
            return "items不能为空"

        for i, item in enumerate(items):
            if not isinstance(item, dict):
                return f"items[{i}]必须是对象"
            if not item.get("item_id"):
                return f"items[{i}]缺少item_id"
            if not item.get("name"):
                return f"items[{i}]缺少name"
            if not item.get("description"):
                return f"items[{i}]缺少description"
            if not item.get("origin"):
                return f"items[{i}]缺少origin"

            importance = item.get("importance", "major")
            if importance not in self.IMPORTANCE_LEVELS:
                return f"items[{i}]的importance必须是: {', '.join(self.IMPORTANCE_LEVELS)}"

            abilities = item.get("abilities")
            if abilities is not None and not isinstance(abilities, list):
                return f"items[{i}]的abilities必须是数组类型"

        # 验证locations
        locations = output.get("locations")
        if not isinstance(locations, list):
            return "locations必须是数组类型"
        if len(locations) == 0:
            return "locations不能为空"

        for i, loc in enumerate(locations):
            if not isinstance(loc, dict):
                return f"locations[{i}]必须是对象"
            if not loc.get("location_id"):
                return f"locations[{i}]缺少location_id"
            if not loc.get("name"):
                return f"locations[{i}]缺少name"
            if not loc.get("description"):
                return f"locations[{i}]缺少description"
            if not loc.get("atmosphere"):
                return f"locations[{i}]缺少atmosphere"
            if not loc.get("story_role"):
                return f"locations[{i}]缺少story_role"

        # 验证organizations (可选但如果有必须符合格式)
        organizations = output.get("organizations")
        if organizations is not None:
            if not isinstance(organizations, list):
                return "organizations必须是数组类型"
            for i, org in enumerate(organizations):
                if not isinstance(org, dict):
                    return f"organizations[{i}]必须是对象"
                if not org.get("org_id"):
                    return f"organizations[{i}]缺少org_id"
                if not org.get("name"):
                    return f"organizations[{i}]缺少name"
                if not org.get("description"):
                    return f"organizations[{i}]缺少description"
                if not org.get("purpose"):
                    return f"organizations[{i}]缺少purpose"

                influence = org.get("influence", "local")
                if influence not in self.INFLUENCE_LEVELS:
                    return f"organizations[{i}]的influence必须是: {', '.join(self.INFLUENCE_LEVELS)}"

        # 验证terms
        terms = output.get("terms")
        if terms is not None:
            if not isinstance(terms, list):
                return "terms必须是数组类型"
            for i, term in enumerate(terms):
                if not isinstance(term, dict):
                    return f"terms[{i}]必须是对象"
                if not term.get("term"):
                    return f"terms[{i}]缺少term"
                if not term.get("definition"):
                    return f"terms[{i}]缺少definition"
                if not term.get("context"):
                    return f"terms[{i}]缺少context"

        return True

    def _get_fallback_response(self) -> Dict[str, Any]:
        """获取降级响应"""
        return {
            "elements_id": f"elements_fallback_{uuid.uuid4().hex[:8]}",
            "items": [
                {
                    "item_id": "item_default_1",
                    "name": "神秘物品",
                    "description": "一个具有神秘力量的物品",
                    "origin": "来源不明",
                    "importance": "major",
                    "abilities": []
                }
            ],
            "locations": [
                {
                    "location_id": "loc_default_1",
                    "name": "主要场所",
                    "description": "故事的主要发生地",
                    "atmosphere": "普通",
                    "story_role": "主要活动场所"
                }
            ],
            "organizations": [],
            "terms": [],
            "fallback": True
        }


if __name__ == "__main__":
    # 测试KeyElementAgent
    agent = KeyElementAgent()

    test_constraints = {
        "genre": "恋爱",
        "themes": ["青春", "成长"],
        "tone": "温馨",
        "must_have": ["校园", "社团"]
    }

    test_world = {
        "era": "现代",
        "location": "私立高中",
        "type": "现实",
        "core_conflict_source": "主角需要在梦想与现实间做出选择",
        "description": "一个普通的高中校园故事"
    }

    try:
        elements = agent.process(
            story_constraints=test_constraints,
            world_setting=test_world
        )
        print("\n" + "=" * 50)
        print("KeyElementAgent 测试成功!")
        print("=" * 50)
        print(f"ID: {elements.elements_id}")
        print(f"道具: {len(elements.items)}个")
        print(f"地点: {len(elements.locations)}个")
        print(f"组织: {len(elements.organizations)}个")
        print(f"术语: {len(elements.terms)}个")
        print("=" * 50)
    except Exception as e:
        print(f"测试失败: {e}")
