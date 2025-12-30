"""
角色管理器
管理游戏中的所有角色，支持从story_outline.json批量创建，也支持半路创建单个角色
每个角色单独保存为JSON文件，支持实时更新
"""
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime

from models.runtime.character import (
    RuntimeCharacter,
    HeroineCharacter,
    ProtagonistCharacter,
    MoodType,
    AffectionStage,
    CharacterGoal,
    CharacterItem,
    RelationshipState
)
from utils.logger import log


class CharacterManager:
    """角色管理器"""

    def __init__(self, save_dir: str = "runtime_data/characters"):
        """
        初始化角色管理器

        Args:
            save_dir: 角色保存目录
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

        # 内存中的角色缓存 {character_id: RuntimeCharacter}
        self._characters: Dict[str, RuntimeCharacter] = {}

        # 主角ID
        self._protagonist_id: Optional[str] = None

        log.info(f"CharacterManager 初始化完成，保存目录: {self.save_dir}")

    # ========== 批量加载/创建 ==========

    def load_from_outline(self, outline_path: str) -> Dict[str, RuntimeCharacter]:
        """
        从story_outline.json加载所有角色

        Args:
            outline_path: story_outline.json文件路径

        Returns:
            创建的角色字典 {character_id: RuntimeCharacter}
        """
        with open(outline_path, 'r', encoding='utf-8') as f:
            outline = json.load(f)

        cast_arc = outline.get("steps", {}).get("cast_arc", {})
        source_outline_id = outline.get("steps", {}).get("premise", {}).get("premise_id", "")

        loaded = {}

        # 加载主角
        protagonist = cast_arc.get("protagonist")
        if protagonist:
            char = self._create_character_from_outline(
                protagonist, "protagonist", source_outline_id
            )
            loaded[char.character_id] = char
            self._protagonist_id = char.character_id
            log.info(f"加载主角: {char.character_name}")

        # 加载女主
        for heroine in cast_arc.get("heroines", []):
            char = self._create_character_from_outline(
                heroine, "heroine", source_outline_id
            )
            loaded[char.character_id] = char
            log.info(f"加载女主: {char.character_name}")

        # 加载配角
        for supporting in cast_arc.get("supporting_cast", []):
            char = self._create_character_from_outline(
                supporting, "supporting", source_outline_id
            )
            loaded[char.character_id] = char
            log.info(f"加载配角: {char.character_name}")

        # 加载反派
        for antagonist in cast_arc.get("antagonists", []):
            char = self._create_character_from_outline(
                antagonist, "antagonist", source_outline_id
            )
            loaded[char.character_id] = char
            log.info(f"加载反派: {char.character_name}")

        # 添加到缓存并保存
        for char in loaded.values():
            self._characters[char.character_id] = char
            self._save_character(char)

        log.info(f"从 outline 加载了 {len(loaded)} 个角色")
        return loaded

    def _create_character_from_outline(
        self,
        outline_char: Dict[str, Any],
        expected_role: str,
        source_outline_id: str
    ) -> RuntimeCharacter:
        """从outline角色数据创建RuntimeCharacter"""
        char_id = outline_char.get("character_id", "")
        role_type = outline_char.get("role_type", "minor")

        # 根据角色类型创建不同的模型
        if role_type == "heroine":
            char = HeroineCharacter.from_outline_character(outline_char, source_outline_id)
            # 设置女主特有属性
            char.route_type = "sweet"  # 可以从outline读取
            char.route_hook = f"与{char.character_name}的恋爱之旅"
        elif role_type == "protagonist":
            char = ProtagonistCharacter.from_outline_character(outline_char, source_outline_id)
        else:
            char = RuntimeCharacter.from_outline_character(outline_char, source_outline_id)

        return char

    # ========== 单个角色创建 ==========

    def create_character(
        self,
        character_id: Optional[str] = None,
        name: str = "",
        role_type: Literal["heroine", "supporting", "antagonist", "minor"] = "minor",
        **kwargs
    ) -> RuntimeCharacter:
        """
        创建一个新角色（半路创建）

        Args:
            character_id: 角色ID（不提供则自动生成）
            name: 角色名称
            role_type: 角色类型
            **kwargs: 其他属性

        Returns:
            创建的角色
        """
        if character_id is None:
            character_id = f"char_{uuid.uuid4().hex[:8]}"

        # 根据角色类型创建对应模型
        if role_type == "heroine":
            char = HeroineCharacter(
                character_id=character_id,
                character_name=name,
                role_type=role_type,
                **kwargs
            )
        elif role_type == "protagonist":
            char = ProtagonistCharacter(
                character_id=character_id,
                character_name=name,
                role_type=role_type,
                **kwargs
            )
        else:
            char = RuntimeCharacter(
                character_id=character_id,
                character_name=name,
                role_type=role_type,
                **kwargs
            )

        self._characters[character_id] = char
        self._save_character(char)

        log.info(f"创建新角色: {name} ({character_id})")
        return char

    # ========== 角色查询 ==========

    def get_character(self, character_id: str) -> Optional[RuntimeCharacter]:
        """
        获取角色

        Args:
            character_id: 角色ID

        Returns:
            角色对象，不存在返回None
        """
        # 先从缓存查找
        if character_id in self._characters:
            return self._characters[character_id]

        # 从文件加载
        char = self._load_character(character_id)
        if char:
            self._characters[character_id] = char

        return char

    def get_protagonist(self) -> Optional[RuntimeCharacter]:
        """获取主角"""
        if self._protagonist_id:
            return self.get_character(self._protagonist_id)

        # 尝试从角色中查找
        for char in self.get_all_characters().values():
            if char.role_type == "protagonist":
                self._protagonist_id = char.character_id
                return char

        return None

    def get_heroines(self) -> List[RuntimeCharacter]:
        """获取所有女主"""
        return [
            char for char in self.get_all_characters().values()
            if char.role_type == "heroine"
        ]

    def get_supporting_cast(self) -> List[RuntimeCharacter]:
        """获取所有配角"""
        return [
            char for char in self.get_all_characters().values()
            if char.role_type == "supporting"
        ]

    def get_antagonists(self) -> List[RuntimeCharacter]:
        """获取所有反派"""
        return [
            char for char in self.get_all_characters().values()
            if char.role_type == "antagonist"
        ]

    def get_all_characters(self) -> Dict[str, RuntimeCharacter]:
        """获取所有角色（从文件加载）"""
        # 如果缓存为空，扫描目录加载
        if not self._characters:
            self._load_all_characters()

        return self._characters

    def get_active_characters(self) -> List[RuntimeCharacter]:
        """获取活跃的角色"""
        return [
            char for char in self.get_all_characters().values()
            if char.is_active
        ]

    # ========== 角色更新 ==========

    def update_character(self, character_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新角色属性

        Args:
            character_id: 角色ID
            updates: 要更新的属性字典

        Returns:
            是否成功
        """
        char = self.get_character(character_id)
        if not char:
            log.warning(f"角色不存在: {character_id}")
            return False

        # 更新属性
        for key, value in updates.items():
            if hasattr(char, key):
                setattr(char, key, value)

        # 保存
        self._save_character(char)
        return True

    def update_mood(
        self,
        character_id: str,
        mood: MoodType | str,
        reason: str = "",
        intensity: int = 5
    ) -> bool:
        """更新角色心情"""
        char = self.get_character(character_id)
        if not char:
            return False

        if isinstance(mood, str):
            mood = MoodType(mood)

        char.update_mood(mood, reason, intensity)
        self._save_character(char)
        return True

    def update_affection(self, character_id: str, delta: int) -> tuple[bool, int, str]:
        """
        更新角色好感度

        Returns:
            (是否成功, 变化量, 新阶段)
        """
        char = self.get_character(character_id)
        if not char:
            return (False, 0, "")

        delta, new_stage = char.update_affection(delta)
        self._save_character(char)

        # 触发成长节点检查
        self._check_affection_milestones(char)

        return (True, delta, new_stage.value)

    def _check_affection_milestones(self, char: RuntimeCharacter):
        """检查好感度里程碑"""
        # 可以在这里定义特定好感度值触发的行为
        if char.affection_value >= 80 and char.affection_value - delta >= 0:  # type: ignore
            log.info(f"[{char.character_name}] 好感度达到深爱阶段!")
        elif char.affection_value >= 60:
            log.info(f"[{char.character_name}] 好感度达到亲密阶段!")
        elif char.affection_value >= 40:
            log.info(f"[{char.character_name}] 好感度达到朋友阶段!")

    def add_item(
        self,
        character_id: str,
        item_id: str,
        name: str,
        description: str = "",
        item_type: Literal["key_item", "weapon", "accessory", "consumable", "special", "gift"] = "key_item",
        **kwargs
    ) -> bool:
        """给角色添加物品"""
        char = self.get_character(character_id)
        if not char:
            return False

        item = CharacterItem(
            item_id=item_id,
            name=name,
            description=description,
            item_type=item_type,
            **kwargs
        )

        success = char.add_item(item)
        if success:
            self._save_character(char)
            log.info(f"[{char.character_name}] 获得物品: {name}")

        return success

    def remove_item(self, character_id: str, item_id: str) -> bool:
        """移除角色物品"""
        char = self.get_character(character_id)
        if not char:
            return False

        success = char.remove_item(item_id)
        if success:
            self._save_character(char)

        return success

    def add_goal(
        self,
        character_id: str,
        description: str,
        goal_type: Literal["short_term", "medium_term", "long_term", "ultimate"] = "medium_term",
        priority: int = 5,
        **kwargs
    ) -> bool:
        """给角色添加目标"""
        char = self.get_character(character_id)
        if not char:
            return False

        goal = CharacterGoal(
            goal_id=f"goal_{character_id}_{uuid.uuid4().hex[:6]}",
            goal_type=goal_type,
            description=description,
            priority=priority,
            **kwargs
        )

        success = char.add_goal(goal)
        if success:
            self._save_character(char)
            log.info(f"[{char.character_name}] 新目标: {description}")

        return success

    def add_memory(
        self,
        character_id: str,
        description: str,
        memory_type: Literal["event", "conversation", "observation", "emotion", "flashback"] = "event",
        importance: Literal["minor", "major", "critical", "life_changing"] = "minor",
        related_characters: List[str] | None = None
    ) -> bool:
        """给角色添加记忆"""
        char = self.get_character(character_id)
        if not char:
            return False

        from models.runtime.character import CharacterMemory

        memory = CharacterMemory(
            memory_id=f"memory_{character_id}_{uuid.uuid4().hex[:6]}",
            memory_type=memory_type,
            description=description,
            importance=importance,
            related_characters=related_characters or []
        )

        char.add_memory(memory)
        self._save_character(char)
        return True

    def trigger_growth_node(self, character_id: str, node: str) -> bool:
        """触发角色成长节点"""
        char = self.get_character(character_id)
        if not char:
            return False

        success = char.trigger_growth_node(node)
        if success:
            self._save_character(char)
            log.info(f"[{char.character_name}] 触发成长节点: {node}")

        return success

    def reveal_secret(self, character_id: str) -> bool:
        """揭露角色秘密"""
        char = self.get_character(character_id)
        if not char:
            return False

        success = char.reveal_secret()
        if success:
            self._save_character(char)
            log.info(f"[{char.character_name}] 秘密已揭露!")

        return success

    def set_relationship(
        self,
        character_id: str,
        target_id: str,
        relationship_type: Literal["love_interest", "ally", "rival", "enemy", "mentor", "family", "friend", "stranger", "complex", "subordinate"],
        affection: int = 50,
        trust: int = 50
    ) -> bool:
        """设置角色间的关系"""
        char = self.get_character(character_id)
        if not char:
            return False

        target_char = self.get_character(target_id)
        target_name = target_char.character_name if target_char else "Unknown"

        relationship = RelationshipState(
            target_character_id=target_id,
            target_character_name=target_name,
            relationship_type=relationship_type,
            affection_level=affection,
            trust_level=trust
        )

        char.set_relationship(relationship)
        self._save_character(char)
        return True

    # ========== 角色状态控制 ==========

    def deactivate_character(self, character_id: str) -> bool:
        """停用角色（不再出现在游戏中）"""
        return self.update_character(character_id, {"is_active": False})

    def activate_character(self, character_id: str) -> bool:
        """激活角色"""
        return self.update_character(character_id, {"is_active": True})

    # ========== 文件存储 ==========

    def _save_character(self, char: RuntimeCharacter) -> bool:
        """保存角色到文件"""
        try:
            file_path = self.save_dir / f"{char.character_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(char.model_dump(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            log.error(f"保存角色失败 {char.character_id}: {e}")
            return False

    def _load_character(self, character_id: str) -> Optional[RuntimeCharacter]:
        """从文件加载角色"""
        file_path = self.save_dir / f"{character_id}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 根据角色类型创建对应模型
            role_type = data.get("role_type", "minor")
            if role_type == "heroine":
                char = HeroineCharacter(**data)
            elif role_type == "protagonist":
                char = ProtagonistCharacter(**data)
            else:
                char = RuntimeCharacter(**data)

            return char
        except Exception as e:
            log.error(f"加载角色失败 {character_id}: {e}")
            return None

    def _load_all_characters(self):
        """加载目录中的所有角色"""
        for file_path in self.save_dir.glob("*.json"):
            # 跳过非角色文件
            if file_path.name in ["main_timeline.json", "story_direction.json"]:
                continue

            character_id = file_path.stem
            char = self._load_character(character_id)
            if char:
                self._characters[character_id] = char

                # 记录主角ID
                if char.role_type == "protagonist":
                    self._protagonist_id = character_id

        log.info(f"从文件加载了 {len(self._characters)} 个角色")

    def save_all(self):
        """保存所有角色"""
        for char in self._characters.values():
            self._save_character(char)
        log.info(f"保存了 {len(self._characters)} 个角色")

    # ========== 查询功能 ==========

    def get_characters_by_mood(self, mood: MoodType | str) -> List[RuntimeCharacter]:
        """获取指定心情的角色"""
        if isinstance(mood, str):
            mood = MoodType(mood)

        return [
            char for char in self.get_all_characters().values()
            if char.current_state.current_mood == mood
        ]

    def get_characters_at_location(self, location: str) -> List[RuntimeCharacter]:
        """获取在指定位置的角色"""
        return [
            char for char in self.get_all_characters().values()
            if char.current_state.current_location == location
        ]

    def get_characters_by_flag(self, flag_name: str, flag_value: bool = True) -> List[RuntimeCharacter]:
        """获取具有指定Flag的角色"""
        return [
            char for char in self.get_all_characters().values()
            if char.get_flag(flag_name) == flag_value
        ]

    def get_characters_with_item(self, item_id: str) -> List[RuntimeCharacter]:
        """获取拥有指定物品的角色"""
        return [
            char for char in self.get_all_characters().values()
            if char.has_item(item_id)
        ]

    def get_affection_ranking(self) -> List[tuple[str, str, int]]:
        """
        获取好感度排名

        Returns:
            [(character_id, character_name, affection_value), ...]
        """
        characters = [
            (char.character_id, char.character_name, char.affection_value)
            for char in self.get_all_characters().values()
            if char.role_type in ["heroine", "supporting"]
        ]

        # 按好感度降序排序
        return sorted(characters, key=lambda x: x[2], reverse=True)

    # ========== 批量操作 ==========

    def update_all_moods(
        self,
        mood: MoodType | str,
        reason: str = "",
        exclude: List[str] | None = None
    ):
        """更新所有角色心情"""
        exclude = exclude or []
        for char in self.get_all_characters().values():
            if char.character_id not in exclude:
                self.update_mood(char.character_id, mood, reason)

    def time_passage_effects(self, hours: int = 1):
        """
        时间流逝效果

        Args:
            hours: 经过的小时数
        """
        for char in self.get_all_characters().values():
            # 精力恢复
            char.current_state.energy_level = min(100, char.current_state.energy_level + hours * 5)

            # 压力自然下降
            char.current_state.stress_level = max(0, char.current_state.stress_level - hours * 2)

            self._save_character(char)

        log.info(f"时间流逝: {hours}小时，已更新所有角色状态")
