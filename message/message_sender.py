from typing import Optional
from ncatbot.utils import status
from ncatbot.core.event import MessageArray

class MessageSender:
    @staticmethod
    async def send_message_to_source(source: str, 
                                     text: Optional[str] = None, 
                                     at: Optional[str] = None, 
                                     reply: Optional[str] = None, 
                                     image: Optional[str] = None, 
                                     rtf: Optional[MessageArray] = None
                                     ):
        """通过source发送消息到指定位置"""
        if source.startswith("G"):
            await status.global_api.post_group_msg(source[1:], text, at=at, reply=reply, image=image, rtf=rtf)
        elif source.startswith("P"):
            await status.global_api.post_private_msg(source[1:], text, reply=reply, image=image, rtf=rtf)
        else:
            raise ValueError("source不合法")
        
