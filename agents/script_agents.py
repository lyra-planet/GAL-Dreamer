"""
文本生成相关 Agents
包含: OpeningSceneAgent, CommonRouteAgent, RouteSceneAgent, EndingSceneAgent

所有 Script Agents 现在继承自 BaseAgent，获得4轮重试机制
"""
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from utils.logger import log
from models.script import Scene, RouteScript, GameScript


class BaseScriptAgent(BaseAgent):
    """脚本生成Agent基类 - 继承自 BaseAgent

    提供4轮JSON验证重试机制
    """

    def __init__(self, name: str, system_prompt: str, human_prompt_template: str):
        super().__init__(
            name=name,
            system_prompt=system_prompt,
            human_prompt_template=human_prompt_template,
            use_structured_output=True  # 启用结构化输出
        )

    def _get_required_fields(self) -> List[str]:
        """子类应重写此方法返回其必填字段"""
        return []


class OpeningSceneAgent(BaseScriptAgent):
    """开场场景生成Agent"""

    def __init__(self):
        from prompts.script_prompts import OPENING_SYSTEM_PROMPT, OPENING_HUMAN_PROMPT
        super().__init__(
            name="OpeningSceneAgent",
            system_prompt=OPENING_SYSTEM_PROMPT,
            human_prompt_template=OPENING_HUMAN_PROMPT
        )

    def _get_required_fields(self) -> List[str]:
        return ["scene_id", "route_id", "scene_type", "location", "time",
                "characters_present", "scene_description", "script_text"]

    def generate(self, story_info: Dict[str, Any]) -> Scene:
        """生成开场场景"""
        protagonist = story_info.get("protagonist", {})
        world = story_info.get("world", {})

        kwargs = {
            "title": story_info.get("title", "无标题"),
            "genre": story_info.get("genre", "未知"),
            "tone": story_info.get("tone", "普通"),
            "protagonist_name": protagonist.get("name", "主角"),
            "protagonist_personality": ", ".join(protagonist.get("personality", [])),
            "protagonist_background": protagonist.get("background", ""),
            "era": world.get("era", "现代"),
            "location": world.get("location", "未知"),
            "core_setting": world.get("description", "")
        }

        result = self.run(**kwargs)
        return Scene(**result)


class CommonRouteAgent(BaseScriptAgent):
    """共通线场景生成Agent"""

    def __init__(self):
        from prompts.script_prompts import COMMON_ROUTE_SYSTEM_PROMPT, COMMON_ROUTE_HUMAN_PROMPT
        super().__init__(
            name="CommonRouteAgent",
            system_prompt=COMMON_ROUTE_SYSTEM_PROMPT,
            human_prompt_template=COMMON_ROUTE_HUMAN_PROMPT
        )

    def _get_required_fields(self) -> List[str]:
        return ["scenes"]

    def generate(self, story_info: Dict[str, Any], scene_count: int = 3) -> List[Scene]:
        """生成共通线场景"""
        heroines = story_info.get("heroines", [])
        route_design = story_info.get("route_design", {})

        # 构建女主摘要
        heroines_summary = []
        for h in heroines:
            heroines_summary.append(
                f"- {h.get('name', '')}: {', '.join(h.get('personality', []))}, {h.get('first_impression', '')}"
            )

        kwargs = {
            "story_summary": story_info.get("macro_plot", {}).get("story_arc", ""),
            "heroines_summary": "\n".join(heroines_summary),
            "common_route_length": route_design.get("common_route_length", "中等"),
            "branching_strategy": route_design.get("branching_strategy", "基于关键选择"),
            "scene_count": scene_count
        }

        result = self.run(**kwargs)

        # 返回scenes列表
        scenes = []
        for s in result.get("scenes", []):
            scenes.append(Scene(**s))
        return scenes


class RouteSceneAgent(BaseScriptAgent):
    """线路场景生成Agent"""

    def __init__(self):
        from prompts.script_prompts import ROUTE_SCENE_SYSTEM_PROMPT, ROUTE_SCENE_HUMAN_PROMPT
        super().__init__(
            name="RouteSceneAgent",
            system_prompt=ROUTE_SCENE_SYSTEM_PROMPT,
            human_prompt_template=ROUTE_SCENE_HUMAN_PROMPT
        )

    def _get_required_fields(self) -> List[str]:
        return ["scenes"]

    def generate(self, route_info: Dict[str, Any], scene_count: int = 4) -> List[Scene]:
        """生成线路专属场景"""
        heroine = route_info.get("heroine", {})
        route = route_info.get("route", {})

        kwargs = {
            "route_id": route.get("route_id", ""),
            "route_name": route.get("route_name", ""),
            "heroine_name": heroine.get("name", ""),
            "heroine_personality": ", ".join(heroine.get("personality", [])),
            "heroine_background": heroine.get("background", ""),
            "route_summary": route.get("route_summary", ""),
            "conflict_focus": route.get("conflict_focus", ""),
            "branch_point": route.get("branch_point", ""),
            "ending_types": ", ".join(route.get("ending_types", [])),
            "scene_count": scene_count
        }

        result = self.run(**kwargs)

        scenes = []
        for s in result.get("scenes", []):
            scenes.append(Scene(**s))
        return scenes


class EndingSceneAgent(BaseScriptAgent):
    """结局场景生成Agent"""

    def __init__(self):
        from prompts.script_prompts import ENDING_SYSTEM_PROMPT, ENDING_HUMAN_PROMPT
        super().__init__(
            name="EndingSceneAgent",
            system_prompt=ENDING_SYSTEM_PROMPT,
            human_prompt_template=ENDING_HUMAN_PROMPT
        )

    def _get_required_fields(self) -> List[str]:
        return ["scene_id", "route_id", "scene_type", "location", "time",
                "characters_present", "scene_description", "script_text"]

    def generate(self, route_info: Dict[str, Any], ending_type: str = "Happy End") -> Scene:
        """生成结局场景"""
        heroine = route_info.get("heroine", {})
        route = route_info.get("route", {})

        kwargs = {
            "route_id": route.get("route_id", ""),
            "route_name": route.get("route_name", ""),
            "heroine_name": heroine.get("name", ""),
            "ending_type": ending_type,
            "climax_aftermath": route.get("climax_aftermath", "经历高潮后，主角面临最终选择")
        }

        result = self.run(**kwargs)
        return Scene(**result)


class ScriptOrchestrator:
    """脚本生成编排器 - 统筹各脚本Agent

    使用继承自 BaseAgent 的 Script Agents，
    获得4轮JSON验证重试机制
    """

    def __init__(self):
        self.opening_agent = OpeningSceneAgent()
        self.common_agent = CommonRouteAgent()
        self.route_agent = RouteSceneAgent()
        self.ending_agent = EndingSceneAgent()
        log.info("ScriptOrchestrator 初始化完成 (所有Agent具备4轮重试机制)")

    def generate_full_script(
        self,
        story_data: Dict[str, Any],
        common_scene_count: int = 3,
        route_scene_count: int = 4,
        progress_callback=None
    ) -> GameScript:
        """生成完整游戏脚本"""

        log.info("=" * 60)
        log.info("开始生成完整游戏脚本")
        log.info("=" * 60)

        # 准备基础信息
        game_script = GameScript(
            story_title=story_data.get("title", "GAL-Dreamer Story"),
            genre=story_data.get("genre", "恋爱"),
            tone=story_data.get("tone", "温馨")
        )

        # 1. 生成开场场景 (带4轮重试)
        log.info("📜 生成开场场景...")
        if progress_callback:
            progress_callback("生成开场场景...")
        opening_scene = self.opening_agent.generate(story_data)
        game_script.common_route_scenes.append(opening_scene)
        log.success(f"开场场景完成: {opening_scene.scene_id}")

        # 2. 生成共通线场景 (带4轮重试)
        log.info("📜 生成共通线场景...")
        if progress_callback:
            progress_callback("生成共通线场景...")
        common_scenes = self.common_agent.generate(story_data, scene_count=common_scene_count)
        game_script.common_route_scenes.extend(common_scenes)
        log.success(f"共通线场景完成: {len(common_scenes)}个场景")

        # 3. 为每条线路生成专属场景 (每个场景带4轮重试)
        routes = story_data.get("routes", [])
        for route in routes:
            route_id = route.get("route_id", "")
            route_name = route.get("route_name", "")

            log.info(f"📜 生成线路 {route_name} 的专属场景...")
            if progress_callback:
                progress_callback(f"生成 {route_name} 线路场景...")

            # 确保 heroine 是字典
            heroine = route.get("heroine", {})
            if not isinstance(heroine, dict):
                log.warning(f"线路 {route_name} 的 heroine 不是字典，使用空字典")
                heroine = {}

            route_info = {
                "heroine": heroine,
                "route": route
            }

            # 生成线路场景 (带4轮重试)
            route_scenes = self.route_agent.generate(route_info, scene_count=route_scene_count)

            # 生成结局 (带4轮重试)
            ending_types = route.get("ending_types", ["Happy End"])
            for ending_type in ending_types[:1]:  # 暂时只生成第一种结局
                log.info(f"  生成 {ending_type} 结局...")
                ending_scene = self.ending_agent.generate(route_info, ending_type)
                route_scenes.append(ending_scene)

            # 创建线路脚本
            route_script = RouteScript(
                route_id=route_id,
                route_name=route_name,
                heroine_name=heroine.get("name", "未知女主"),
                scenes=route_scenes
            )
            game_script.route_scripts.append(route_script)

            log.success(f"线路 {route_name} 完成: {len(route_scenes)}个场景")

        # 4. 生成完整文本
        log.info("📜 整合完整脚本文本...")
        game_script.full_text = game_script.get_full_script_text()

        log.success("=" * 60)
        log.success(f"脚本生成完成！总计 {game_script.get_scene_count()} 个场景")
        log.success(f"文本长度: {len(game_script.full_text)} 字符")
        log.success("=" * 60)

        return game_script
