from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
import re

__all__ = ["MessageUnit"]

_MESSAGE_UNIT_PATTERN = re.compile(
    r"^<message><time:(?P<time>.*?)\/><user:(?P<user_nickname>.*?)\/><user_qqid:(?P<user_id>.*?)\/>(?:<user_card:(?P<user_card>.*?)\/>){0,1}(?P<message>.*)</message>$"
)

@dataclass(slots=True)
class MessageUnit:
    """消息单元

    说明:
        - 采用 dataclass + slots 提升可读性与内存效率。
        - `__str__` 生成的串可由 `from_str` 解析（注意 message / user_card 中含有特殊分隔符时目前未做转义）。
    TODO:
        如将来需要支持包含 `</message>` 或 `/>` 之类符号的正文，可引入转义或改用 JSON。
    """

    user_nickname: str = field(default="")
    user_id: str = field(default="")
    message: str = field(default="")
    time: str = field(default="")
    source: str = field(default="")
    user_card: Optional[str] = field(default=None)
    is_notice: bool = field(default=False)
    is_self: bool = field(default=False)  # 是否为机器人自己发送的消息

    # ------------------------------------------------------------------
    # 序列化 / 反序列化
    # ------------------------------------------------------------------
    def __str__(self) -> str: 
        if self.is_self:
            return f"<time:{self.time}/>{self.message}"
        if self.user_card:
            if self.is_notice:
                return (
                    f"<notice><time:{self.time}/><user:{self.user_nickname}/><user_qqid:{self.user_id}/><user_card:{self.user_card}/>{self.message}</notice>"
                )
            return (
                f"<message><time:{self.time}/><user:{self.user_nickname}/><user_qqid:{self.user_id}/><user_card:{self.user_card}/>{self.message}</message>"
            )
        if self.is_notice:
            return (
                f"<notice><time:{self.time}/><user:{self.user_nickname}/><user_qqid:{self.user_id}/>{self.message}</notice>"
            )
        return (
            f"<message><time:{self.time}/><user:{self.user_nickname}/><user_qqid:{self.user_id}/>{self.message}</message>"
        )

    def to_xml(self) -> str:
        """显式命名的导出方法（与 __str__ 一致）。"""
        return str(self)

    def to_dict(self) -> Dict[str, Any]:
        """转普通 dict（浅拷贝）"""
        return asdict(self)

    @classmethod
    def from_str(cls, message_unit_str: str) -> "MessageUnit":
        """从 __str__ / to_xml 产出的字符串解析

        注意: 当前实现对字段中的分隔符未做转义，确保外部生成的格式可信。
        """
        match = _MESSAGE_UNIT_PATTERN.match(message_unit_str)
        if not match:
            raise ValueError("错误的消息单元格式")
        data = match.groupdict()
        return cls(
            user_nickname=data["user_nickname"],
            user_id=data["user_id"],
            message=data["message"],
            time=data["time"],
            user_card=data.get("user_card"),
        )

    # ------------------------------------------------------------------
    # Hash / 识别
    # ------------------------------------------------------------------
    def __hash__(self) -> int:  # 维持兼容：只用 user_id + time
        return self.get_hash()

    def get_hash(self) -> int:
        return hash((self.user_id, self.time))

    # 可选：定义一个消息唯一 id 属性
    @property
    def uid(self) -> str:
        return f"{self.user_id}:{self.time}"
