import json
import time
from typing import Optional, override, Callable

from .base_model import BaseModel
from .filter_model import FilterModel
from ..api_platforms import ModelPlatform
from ..prompts import PromptManager
from ..ego import BotBaseInfo
from ..message import ChatRequest


class ChatModel(BaseModel):
    def __init__(self, model_name: str, platform: ModelPlatform, bot_info: BotBaseInfo):
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
    def _process_data(self, model_output: dict) -> dict:
        try:
            content = json.loads(model_output["choices"][0]["message"]["content"])
            if isinstance(content, dict):
                return content
            raise ValueError("无效的响应格式")
        except Exception as e:
            raise ValueError(f"处理数据失败: {e}")

    def process_func(self, chat_request: ChatRequest, filter: Optional[FilterModel]) -> tuple[dict, dict, str]:
        processed_data = self.get_process_data(chat_request)
        validation_data = {}
        emotion = processed_data["emotion"] if processed_data["emotion"] in ["喜悦", "愤怒", "悲伤", "厌恶", "平静", "尴尬", "失望", "渴望", "疑惑"] else "平静"
        if filter:
            cr = ChatRequest(filter.create_initial_message_chain(str(processed_data)))
            validation_data = filter.get_process_data(cr)
        return processed_data, validation_data, emotion
    
    def generate_reply_func(self, processed_data, validation_data = None):
        if validation_data:
            for original_content, verification_result in zip(processed_data["content"], validation_data["verified"]):
                can_output = verification_result.get("can_output", False)
                reason = verification_result.get("reason", "")
                if not can_output:
                    yield f"!!过滤!!({reason})", original_content
                else:
                    yield original_content, ""
                time.sleep(len(original_content) / 5)  # 模拟打字延迟
        else:
            for reply_msg in processed_data.get("content", []):
                yield reply_msg, ""
                time.sleep(len(reply_msg) / 5)  # 模拟打字延迟
        

