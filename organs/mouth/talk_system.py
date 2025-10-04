from typing import Optional
from pathlib import Path
from queue import Queue
import threading
from ncatbot.utils import get_log
from ncatbot.plugin_system import EventBus

from ..base_system import BaseSystem, SystemConfig
from ...message import ChatRequest
from ...models import ChatModel, FilterModel

class TalkConfig(SystemConfig):
    def __init__(self, work_path: Path) -> None:
        super().__init__(work_path)

class TalkSystem(BaseSystem[TalkConfig]):
    log = get_log("SiriusChatCore-TalkSystem")
    def __init__(self, event_bus: EventBus, work_path: Path, chat_model: ChatModel, filter: Optional[FilterModel] = None):
        super().__init__(event_bus, work_path, TalkConfig(work_path))
        self._chat_model = chat_model
        self._filter = filter
        self._talk_processors = []
        self._chat_requests : dict[str, Queue] = {}
        self._lock = threading.Lock()

    
    def add_chat_request(self, source: str, chat_request: ChatRequest):
        with self._lock:
            if source not in self._chat_requests:
                self._chat_requests[source] = Queue()
                t = threading.Thread(name=f"mouth_in_{source}", target=self._talk_processor, args=(source,), daemon=True)
                t.start()
                self._talk_processors.append(t)
            self._chat_requests[source].put(chat_request)

    def _talk_processor(self, source: str):
        while True:
            chat_request = self._chat_requests[source].get()
            if not chat_request and not isinstance(chat_request, ChatRequest):
                continue
            try:
                # TODO: 回复逻辑
                pass
            except Exception as e:
                self.log.error(f"在处理 {source} 的回复时出现了错误: {e}")