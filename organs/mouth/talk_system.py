import time
from typing import Optional, Dict
from pathlib import Path
from queue import Queue
import threading
from ncatbot.utils import get_log
from ncatbot.plugin_system import EventBus
from dataclasses import dataclass

from ..base_system import BaseSystem, SystemConfig
from ...message import ChatRequest, MessageSender, MessageUnit
from ...models import ChatModel, FilterModel

class TalkConfig(SystemConfig):
    def __init__(self, work_path: Path) -> None:
        super().__init__(work_path, [])

class TalkSystem(BaseSystem[TalkConfig]):
    log = get_log("SiriusChatCore-TalkSystem")
    def __init__(self, event_bus: EventBus, work_path: Path, chat_model: ChatModel, filter: Optional[FilterModel] = None):
        super().__init__(event_bus, work_path, TalkConfig(work_path))
        self._chat_model = chat_model
        self._filter = filter
        # 监控线程：定期清理长时间空闲的来源
        self._monitor_thread = threading.Thread(name="mouth_monitor_thread", target=self._monitor_loop, daemon=True)
        self._talk_processors = []
        self._chat_requests : Dict[str, "_ChatChannelState"] = {}
        self._lock = threading.Lock()
        self._monitor_thread.start()

    def add_talk(self, source: str, current_message: MessageUnit):
        # TODO: 构造MessageChain
        chat_request = ChatRequest(
            message_chain=self._chat_model.create_initial_message_chain(str(current_message)),
            source=source,
            current_message=current_message,
            timestamp=int(time.time()),
            at_bot=self._chat_model._bot_info.is_mentioned(str(current_message))
        )
        with self._lock:
            if source not in self._chat_requests:
                self._chat_requests[source] = _ChatChannelState(Queue(), int(time.time()))
                t = threading.Thread(name=f"mouth_in_{source}", target=self._talk_processor, args=(source,), daemon=True)
                t.start()
                self._talk_processors.append(t)
            self._chat_requests[source].queue.put(chat_request)


    def _talk_processor(self, source: str):
        while True:
            chat_request = self._chat_requests[source].queue.get()
            with self._lock:
                self._chat_requests[source].last_active = int(time.time())
            if not chat_request and not isinstance(chat_request, ChatRequest):
                continue
            try:
                p_data, v_data, emotion = self._chat_model.process_func(chat_request, self._filter)
                if v_data:
                    for original_content, verification_result in zip(p_data["content"], v_data["verified"]):
                        can_output = verification_result.get("can_output", False)
                        reason = verification_result.get("reason", "")
                        if not can_output:
                            self.log.info(f"过滤发送给 {source} 的消息: {original_content} 原因: {reason}")
                            MessageSender.send_message_to_source_sync(source, f"该消息已被过滤。")
                        else:
                            self.log.info(f"向 {source} 发送消息: {original_content}")
                            MessageSender.send_message_to_source_sync(source, original_content)
                        time.sleep(len(original_content) / 5)  # 模拟打字延迟
                else:
                    for reply_msg in p_data.get("content", []):
                        self.log.info(f"向 {source} 发送消息: {reply_msg}")
                        MessageSender.send_message_to_source_sync(source, reply_msg)
                        time.sleep(len(reply_msg) / 5)  # 模拟打字延迟
                
            except Exception as e:
                self.log.error(f"在处理 {source} 的回复时出现了错误: {e}")


    def _monitor_loop(self):
        self.log.debug("对话监控线程已启动。")
        while True:
            time.sleep(10)
            with self._lock:
                to_remove = []
                for source, state in self._chat_requests.items():
                    if state.queue.empty() and time.time() - state.last_active > 300:  # 300秒未活跃则关闭
                        to_remove.append(source)
                for source in to_remove:
                    self.log.info(f"关闭 {source} 的对话处理线程。")
                    del self._chat_requests[source]

@dataclass(slots=True)
class _ChatChannelState:
    """单个来源的对话通道状态。

    queue: 消息请求队列
    last_active: 上次活跃时间戳（秒）
    """
    queue: Queue
    last_active: int