from ncatbot.utils import get_log
from ncatbot.plugin_system import EventBus
from pathlib import Path

from ..base_system import BaseSystem, SystemConfig
from ...message import MessageUnit, MessageChain, MessageChainBuilder

class MemoryConfig(SystemConfig):
    short_term_capacity: int = 16  # 短期记忆容量
    diary_capacity: int = 12  # 日记整合容量

    def __init__(self, work_path: Path) -> None:
        super().__init__(work_path, ["short_term_capacity"])

class MemorySystem(BaseSystem[MemoryConfig]):
    log = get_log("SiriusChatCore-MemorySystem")
    def __init__(self, event_bus: EventBus, work_path: Path, summary_model):
        super().__init__(event_bus, work_path, MemoryConfig(work_path))
        self.short_term_memory: list[MessageUnit] = []
        self.diary_category: list[tuple[str, str]] = []
        self.diary: str = ""
        self._summary_model = summary_model

    def add_to_short_term(self, message: MessageUnit):
        if message.is_self or message.is_notice:
            self.short_term_memory.append(message)
        elif self.short_term_memory and self.short_term_memory[-1].user_id == message.user_id:
            self.short_term_memory[-1].message += f"\n{message.message}"  # 合并同一用户的连续消息
            self.short_term_memory[-1].time = message.time  # 更新时间戳
        else:
            self.short_term_memory.append(message)
        if len(self.short_term_memory) > self.config.short_term_capacity:
            self.short_term_memory.pop()
    
    def get_memory(self, init_message_chain: MessageChain) -> MessageChain:
        mcb = MessageChainBuilder.from_message_chain(init_message_chain)
        if self.diary:
            mcb.append_system_message(f"以前发生的事情你写成了日记，这是你的日记内容：\n{self.diary}")
        if self.short_term_memory:
            mcb.add_user_message_by_units(self.short_term_memory)
        return mcb.build()