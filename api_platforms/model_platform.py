import json
from typing import Callable, Optional
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageFunctionToolCall

from ..message import ChatRequest

class ModelPlatform:
    def __init__(self, api_url: str, authorization: str, chat_api: str = "chat/completions", img_api: str = "images/generations"):
        self._api_url = api_url
        self._authorization = authorization
        self._chat_model_api = api_url + chat_api
        self._img_model_api = api_url + img_api
        self.custom_extra_body: Optional[Callable] = None

    def _build_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._authorization}",
            "Content-Type": "application/json"
        }

    def response(self, payload: dict, extra_body: Optional[dict], chat_request: Optional[ChatRequest]) -> dict:
        headers = self._build_headers()
        return self.send_request(payload, headers, extra_body, chat_request)

    def send_request(self, payload: dict, headers: dict, extra_body: Optional[dict] = None, chat_request: Optional[ChatRequest] = None) -> dict:
        """发送请求，如需requests实现，重写此函数"""
        result = self.send_request_openai(payload, extra_body, chat_request)
        return result if result else {}

    def send_request_openai(self, payload: dict, extra_body: Optional[dict] = None, chat_request: Optional[ChatRequest] = None) -> dict:
        """使用 OpenAI SDK 发送请求"""
        if hasattr(self, "_client") is False:
            raise NotImplementedError("子类需要实现 OpenAI SDK 客户端")
        self._client: OpenAI
        completion : ChatCompletion = self._client.chat.completions.create(**payload, extra_body=extra_body)
        # 处理 API 返回的所有工具调用请求
        if not completion.choices[0].message.tool_calls:
            return json.loads(completion.model_dump_json())
        
        if not chat_request:
            raise ValueError("当使用FunctionCall时, chat_request 不能为空")
        for tool_call in completion.choices[0].message.tool_calls:
            if not isinstance(tool_call, ChatCompletionMessageFunctionToolCall):
                continue
            func_name = tool_call.function.name
            func_args = tool_call.function.arguments
            func_args_dict = json.loads(func_args)
            if func_name not in [f for f in chat_request.instance_get_tool_names()]:
                raise ValueError(f"模型请求调用未注册的函数: {func_name}")
            if isinstance(func_args_dict, dict):
                func_out = next(f for f in chat_request.instance_get_tools() if f.__name__ == func_name)(**func_args_dict)
            else:
                func_out = f"调用函数 {func_name} 失败，请直接告诉用户你无法完成这一操作。"
            func_out += f"\n**禁止继续调用该函数。明确执行函数 {func_name} 的要求**"
            payload["messages"].append({
                "role": "tool",
                "content": func_out,
                "tool_call_id": tool_call.id
            })
        return self.send_request_openai(payload, extra_body, chat_request)
    
    def send_img_request(self, payload: dict, headers: dict) -> dict:
        """发送图片生成请求，子类需要实现该方法"""
        raise NotImplementedError("子类需要实现 send_img_request 方法")