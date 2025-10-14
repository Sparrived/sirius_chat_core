from ncatbot.utils import get_log
from ncatbot.plugin_system import EventBus
from pathlib import Path

from ..base_system import BaseSystem, SystemConfig

class WillingnessConfig(SystemConfig):
    threshold: float = 70.0  # 触发聊天的阈值

    def __init__(self, work_path: Path) -> None:
        super().__init__(work_path, ["threshold"])

class WillingnessSystem(BaseSystem[WillingnessConfig]):
    log = get_log("SiriusChatCore-WillingnessSystem")
    def __init__(self, event_bus: EventBus, work_path: Path):
        super().__init__(event_bus, work_path, WillingnessConfig(work_path))
        self.willingness_level: float = 0

    def increase_willingness(self, amount: float):
        self.willingness_level += amount
        self.willingness_level = min(self.willingness_level, 100)  # Cap at 100

    def decrease_willingness(self, amount: float):
        self.willingness_level -= amount
        self.willingness_level = max(self.willingness_level, 0)  # Floor at 0


