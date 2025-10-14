import json
from typing import Optional, override
from .base_model import BaseModel

from ..errors import ExecuteError
from ..api_platforms import ModelPlatform
from ..prompts import PromptManager

class FilterModel(BaseModel):
    def __init__(self, model_name: str, platform: ModelPlatform):
        system_prompt = PromptManager.get_filter_prompt()
        super().__init__(system_prompt, model_name, platform, temperature=0.1, max_tokens=2048, enable_thinking=True, thinking_budget=512)

        

    @override
    def _process_data(self, model_output : dict) -> dict:
        reply_msg = model_output["choices"][0]["message"]["content"].replace("```json", "").replace("```", "")
        try:
            reply_json = json.loads(reply_msg)
            if isinstance(reply_json, list):
                reply_json = {"verified": reply_json}
            if isinstance(reply_json, dict) and "verified" in reply_json:
                return reply_json
            raise ValueError("无效的响应格式")
        except Exception as e:
            raise ExecuteError(f"过滤模型返回内容解析失败: {reply_msg}，错误信息: {e}")
