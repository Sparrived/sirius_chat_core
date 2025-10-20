from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Iterable
from .message_unit import MessageUnit

MessageDict = Dict[str, Any]

@dataclass(slots=True)
class MessageChain:
    """消息链
    约束:
        - 列表非空
        - 第一个消息必须为 system
        - 每个元素必须包含 role 与 content
    """
    _messages: List[MessageDict] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        if not self._messages:
            raise ValueError("消息链不能为空，且必须为列表")
        if not isinstance(self._messages, list):
            raise ValueError("_messages 必须为 list")
        if not all(isinstance(m, dict) and "role" in m and "content" in m for m in self._messages):
            raise ValueError("消息链中的每个消息必须是包含'role'和'content'字段的字典")
        if self._messages[0].get("role") != "system":
            raise ValueError("消息链的第一条消息必须是系统消息，role 必须为 'system'")

    # 基础访问 -------------------------------------------------------
    def to_list(self) -> List[MessageDict]:
        # 返回浅拷贝避免外部直接修改内部结构
        return list(self._messages)

    def __iter__(self) -> Iterable[MessageDict]:
        return iter(self._messages)

    def __getitem__(self, index: int) -> MessageDict:
        return self._messages[index]

    def __len__(self) -> int:
        return len(self._messages)

    def last_role(self) -> Optional[str]:
        return self._messages[-1]["role"] if self._messages else None

    def append(self, msg: MessageDict) -> None:
        self._messages.append(msg)


@dataclass(slots=True)
class MessageChainBuilder:
    """消息链构建器（可链式调用）"""
    _messages: List[MessageDict] = field(default_factory=list, repr=False)

    # 构建 -----------------------------------------------------------
    @classmethod
    def from_message_chain(cls, message_chain: MessageChain) -> "MessageChainBuilder":
        """从已有的 MessageChain 创建构建器实例"""
        return cls(message_chain.to_list())

    def create_new_message_chain(self, system_prompt: str) -> "MessageChainBuilder":
        """创建新的消息链，必须首先调用此方法"""
        if self._messages:
            raise ValueError("已经存在消息，不能再次创建 system 消息")
        self._messages.append({"role": "system", "content": system_prompt})
        return self

    # 添加消息 -------------------------------------------------------
    def _ensure_not_consecutive(self, role: str) -> None:
        if len(self._messages) > 1 and self._messages[-1]["role"] == role:
            raise ValueError(f"{role} 消息不能连续发送")

    def add_user_message(self, content: Optional[str], img_base64: Optional[str] = None) -> "MessageChainBuilder":
        if not self._messages:
            raise ValueError("请先创建 system 消息")
        self._ensure_not_consecutive("user")
        if img_base64:
            payload: List[Dict[str, Any]] = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_base64}",
                        "detail": "low",
                    },
                }
            ]
            if content:
                payload.append({"type": "text", "text": content})
            self._messages.append({"role": "user", "content": payload})
        elif content:
            self._messages.append({"role": "user", "content": content})
        else:
            raise ValueError("必须提供 content 或 img_base64 其中之一")
        return self

    def add_user_message_by_units(self, message_units: List[MessageUnit]) -> "MessageChainBuilder":
        if not self._messages:
            raise ValueError("请先创建 system 消息")
        self._ensure_not_consecutive("user")
        if message_units:
            content = "\n".join(str(unit) for unit in message_units)
            self._messages.append({"role": "user", "content": content})
        else:
            raise ValueError("message_units 不能为空")
        return self
    
    def add_message_by_units(self, message_units: List[MessageUnit]) -> "MessageChainBuilder":
        if not self._messages:
            raise ValueError("请先创建 system 消息")
        last_unit: Optional[MessageUnit] = None
        for unit in message_units:
            if unit.is_self:
                self.add_assistant_message(str(unit))
            else:
                self.add_user_message(str(unit))
        return self

    def add_assistant_message(self, content: str) -> "MessageChainBuilder":
        if not self._messages:
            raise ValueError("请先创建 system 消息")
        self._ensure_not_consecutive("assistant")
        self._messages.append({"role": "assistant", "content": content})
        return self
    
    def append_system_message(self, content: str) -> "MessageChainBuilder":
        self._messages[0]["content"] += f"\n{content}"
        return self

    # 维护 -----------------------------------------------------------
    def clear(self) -> "MessageChainBuilder":
        self._messages.clear()
        return self

    # 输出 -----------------------------------------------------------
    def build(self) -> MessageChain:
        if not self._messages:
            raise ValueError("消息链为空，请先添加消息")
        chain = MessageChain(self._messages.copy())
        self.clear()
        return chain
