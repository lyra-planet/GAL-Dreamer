"""
主时间线管理器 - 精简版
只记录已发生的历史
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from models.runtime.timeline import StoryTimeline, MAIN_TIMELINE_ID
from utils.logger import log


class TimelineManager:
    """主时间线管理器"""

    def __init__(self, save_dir: str = "runtime_data"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.save_dir / "main_timeline.json"
        self._timeline: Optional[StoryTimeline] = None

    def load_or_create(self) -> StoryTimeline:
        """加载或创建"""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._timeline = StoryTimeline(**data)
                log.info(f"加载时间线: {len(self._timeline.history)}个历史")
                return self._timeline
            except:
                pass

        self._timeline = StoryTimeline()
        self._save()
        return self._timeline

    def load_world_history(self, path: str) -> StoryTimeline:
        """加载世界历史（只执行一次，加载背景故事）"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 确保时间线已加载
        if not self._timeline:
            self._timeline = StoryTimeline()

        # 如果已有历史，不重复加载
        if self._timeline.history:
            log.info("历史已存在，跳过加载")
            return self._timeline

        # 尝试从不同位置获取时间线数据
        # 可能是独立的timeline文件，或者嵌套在其他结构中
        timeline_data = data.get("timeline") or data.get("steps", {}).get("timeline") or data

        if not timeline_data or isinstance(timeline_data, str):
            return self.get_timeline()

        self._timeline = StoryTimeline.from_worldbuilding(timeline_data)
        self._save()
        log.info(f"加载世界历史: {len(self._timeline.history)} 个事件")
        return self._timeline

    def get_timeline(self) -> StoryTimeline:
        """获取时间线"""
        if not self._timeline:
            return self.load_or_create()
        return self._timeline

    # ========== 导演接口 ==========

    def get_position(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.get_timeline().get_position()

    def add_history(
        self,
        name: str,
        desc: str,
        time: str = "",
        type: str = "story",
        characters: List[Dict[str, str]] = None
    ) -> str:
        """追加历史事件

        Args:
            name: 事件名称
            desc: 事件描述
            time: 时间描述
            type: 事件类型
            characters: 角色快照列表，格式：[{"character_id": "xxx", "state": "xxx"}]
        """
        event_id = self._timeline.add_history(name, desc, time=time, type=type, characters=characters)
        self._save()
        log.info(f"追加历史: [{event_id}] {name}")
        return event_id

    # ========== 查询 ==========

    def get_recent_history(self, count: int = 10) -> List[Dict]:
        """获取最近的历史"""
        events = self._timeline.get_recent(count)
        return [
            {
                "id": e.id,
                "time": e.time,
                "name": e.name,
                "desc": e.desc,
                "type": e.type,
                "characters": [
                    {
                        "character_id": c.character_id,
                        "name": c.name,
                        "state": c.state,
                        "driver_event": c.driver_event
                    }
                    for c in e.characters
                ]
            }
            for e in events
        ]

    def get_all_history(self) -> List[Dict]:
        """获取所有历史"""
        return [
            {
                "id": e.id,
                "time": e.time,
                "name": e.name,
                "desc": e.desc,
                "type": e.type,
                "characters": [
                    {
                        "character_id": c.character_id,
                        "name": c.name,
                        "state": c.state,
                        "driver_event": c.driver_event
                    }
                    for c in e.characters
                ]
            }
            for e in self._timeline.history
        ]

    # ========== 保存 ==========

    def _save(self):
        """保存"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            data = self._timeline.model_dump(exclude={'counter'})
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save(self) -> bool:
        """保存"""
        self._save()
        return True

    def reload(self) -> Optional[StoryTimeline]:
        """重新加载"""
        return self.load_or_create()
