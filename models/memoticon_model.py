import json
from typing import override


from .base_model import BaseModel
from ..api_platforms import ModelPlatform
from ..prompts import PromptManager
from ..message import ChatRequest

class MemoticonModel(BaseModel):
    """表情包判别模型"""
    def __init__(self, model_name: str, platform: ModelPlatform):
        system_prompt = PromptManager.get_memoticon_prompt()
        super().__init__(system_prompt, model_name, platform, temperature=0, max_tokens=1024, enable_thinking=True, thinking_budget=512)

    @override
    def _process_data(self, model_output: dict) -> dict:
        reply_msg = model_output["choices"][0]["message"]["content"].replace("```json", "").replace("```", "")
        try:
            reply_json = json.loads(reply_msg)
            if isinstance(reply_json, dict) and "is_meme" in reply_json and "meme_type" in reply_json and "desp" in reply_json:
                return reply_json
            raise ValueError(f"表情包判别模型返回内容不完整")
        except Exception as e:
            raise ValueError(f"表情包判别模型返回内容解析失败: {reply_msg}，错误信息: {e}")
    
    @override
    def _build_payload(self, messages: list[dict]) -> dict:
        self._extra_body = self._build_extra_body()
        return {
            "model": self._model_name,
            "messages": messages,
            "max_tokens": self._max_tokens,
            "stop": self._stop,
            "temperature": self._temperature,
            "top_p": self._top_p,
            "frequency_penalty": self._frequency_penalty,
            "presence_penalty": self._presence_penalty,
            "n": self._n,
        }

    def judge_meme(self, img_base64: str) -> dict:
        msg_chain = self.create_initial_message_chain("判别这张图片", img_base64)
        cr = ChatRequest(message_chain=msg_chain)
        return self.get_process_data(cr)