import json
from typing import Optional, override, Callable

from .base_model import BaseModel
from .filter_model import FilterModel
from ..api_platforms import ModelPlatform
from ..prompts import PromptManager
from ..message import ChatRequest, MessageChainBuilder, MessageChain

class ChatModel(BaseModel):
    def __init__(self, model_name: str, platform: ModelPlatform, bot_info):
        self._init_tools = False
        self._chat_temp: list[dict] = []
        self._bot_info = bot_info
        system_prompt = PromptManager.get_chat_prompt(bot_info)

        BaseModel.__init__(self, system_prompt, model_name, platform, temperature=0.7, top_p= 0.9, max_tokens=2048)

    def init_tools(self, tools: dict[Callable, str]):
        if self._init_tools:
            raise ValueError("工具已经初始化")
        for k,v in tools.items():
            self.add_tool(k, v)
        self._system_prompt += PromptManager.get_chat_tools_prompt(self._tools)
        self._init_tools = True

    @override
    def create_initial_message_chain(self, user_message: Optional[str] = None, img_base64: Optional[str] = None) -> MessageChain:
        """创建初始消息链，如果传入其他参数则下一条信息应为助手消息，传入消息作为用户消息"""
        self._system_prompt = PromptManager.get_chat_prompt(self._bot_info)
        mcb = MessageChainBuilder()
        mcb.create_new_message_chain(self._system_prompt)
        if user_message or img_base64:
            mcb.add_user_message(user_message, img_base64)
        return mcb.build()

    @override
    def _process_data(self, model_output: dict) -> dict:
        try:
            content = json.loads(model_output["choices"][0]["message"]["content"])
            if isinstance(content, dict):
                return content
            raise ValueError("无效的响应格式")
        except Exception as e:
            raise ValueError(f"处理数据失败: {e}")

    def process_func(self, chat_request: ChatRequest, filter: Optional[FilterModel]) -> tuple[dict, dict, str, str]:
        processed_data = self.get_process_data(chat_request)
        validation_data = {}
        emotion = processed_data["emotion"] if processed_data["emotion"] in ["喜悦", "愤怒", "悲伤", "厌恶", "平静", "尴尬", "失望", "渴望", "疑惑"] else "平静"
        daily = processed_data["diary"] if "diary" in processed_data else ""
        if filter:
            cr = ChatRequest(filter.create_initial_message_chain(str(processed_data)))
            validation_data = filter.get_process_data(cr)
        return processed_data, validation_data, emotion, daily
        

