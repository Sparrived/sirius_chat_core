from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from .message_chain import MessageChain, MessageUnit


@dataclass
class ChatRequest:
    """聊天请求，包含消息链与可选的工具列表

    说明:
        - 采用 dataclass + slots 提升可读性与内存效率。
        - `instance_get_tools` 与 `instance_get_tool_names` 用于获取工具函数列表与名称列表，方便在处理模型响应时调用。
    """
    message_chain: MessageChain = field()
    source: Optional[str] = field(default="")
    current_message: Optional[MessageUnit] = field(default=None, repr=False, compare=False)
    timestamp: Optional[int] = field(default=0)
    at_bot: Optional[bool] = field(default=False)
    tools: Optional[List[Callable]] = field(default=None, repr=False, compare=False)

    def instance_get_tools(self) -> List[Callable]:
        """获取工具函数列表"""
        return self.tools if self.tools else []

    def instance_get_tool_names(self) -> List[str]:
        """获取工具函数名称列表"""
        return [f.__name__ for f in self.instance_get_tools()]