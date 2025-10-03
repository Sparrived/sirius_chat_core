from typing import Callable
from typing import Any, Optional

from .errors import ExecuteError

from ..api_platforms import ModelPlatform
from ..message import MessageChain, MessageChainBuilder, ChatRequest
from ..function_calls import FunctionBuilder

class BaseModel:
    def __init__(self, 
                 system_prompt: str, 
                 model_name: str,
                 platform : ModelPlatform,
                 temperature: float = 0.7,
                 top_p: float = 1.0,
                 top_k: int = 50,
                 max_tokens: int = 1024,
                 frequency_penalty: float = 0.0,
                 presence_penalty: float = 0.0,
                 enable_streaming: bool = False,
                 enable_thinking: bool = False,
                 thinking_budget: int = 512,
                 stop: list[str] = [],
                 n: int = 1,
                 response_format: str = "json_object"
                 ):
        self._system_prompt = system_prompt
        self._temperature = temperature
        self._top_p = top_p
        self._top_k = top_k
        self._max_tokens = max_tokens
        self._model_name = model_name
        self._frequency_penalty = frequency_penalty
        self._presence_penalty = presence_penalty
        self._enable_streaming = enable_streaming
        self._enable_thinking = enable_thinking
        self._thinking_budget = thinking_budget
        self._stop = stop
        self._n = n
        self._response_format = response_format
        self._platform = platform

    def create_initial_message_chain(self, user_message: Optional[str] = None, img_base64: Optional[str] = None) -> MessageChain:
        """创建初始消息链，如果传入其他参数则下一条信息应为助手消息，传入消息作为用户消息"""
        mcb = MessageChainBuilder()
        mcb.create_new_message_chain(self._system_prompt)
        if user_message or img_base64:
            mcb.add_user_message(user_message, img_base64)
        return mcb.build()

    def add_tool(self, func: Callable, desc: str = ""):
        try:
            if not hasattr(self, "_tools"):
                self._tools = []
            self._tools.append({"type": "function", "function": FunctionBuilder(function=func, description=desc).build_function_json()})
        except Exception as e:
            raise ValueError(f"构建工具失败: {e}")
    
    def _response(self, chat_request: ChatRequest) -> dict:
        """发送请求并返回响应结果，得到全部响应结果的内容"""
        payload = self._build_payload(chat_request.message_chain.to_list())
        return self._platform.response(payload, self._extra_body, chat_request)
    
    def _process_data(self, model_output: dict) -> dict:
        """处理响应结果，提取有用信息，需要子类实现"""
        raise NotImplementedError()

    def get_process_data(self, chat_request: ChatRequest) -> dict:
        """获取处理后的数据"""
        try:
            model_output = self._response(chat_request)
            return self._process_data(model_output)
        except Exception as e:
            raise ExecuteError(f"获取处理后的数据失败: {e}")
        
    def _build_payload(self, messages: list[dict]) -> dict:
        if not hasattr(self, "_extra_body"):
            self._extra_body = self._build_extra_body()
        payload = {
            "model": self._model_name,
            "messages": messages,
            "max_tokens": self._max_tokens,
            "stop": self._stop,
            "temperature": self._temperature,
            "top_p": self._top_p,
            "frequency_penalty": self._frequency_penalty,
            "presence_penalty": self._presence_penalty,
            "n": self._n,
            "response_format": {"type": self._response_format},
        }
        if hasattr(self, "_tools"):
            payload["tools"] = self._tools
        return payload

    def _build_extra_body(self) -> dict[str, Any]:
        if self._platform.custom_extra_body:
            return self._platform.custom_extra_body(self)
        return {
            "thinking": self._enable_thinking,
            "thinking_budget": self._thinking_budget
        }