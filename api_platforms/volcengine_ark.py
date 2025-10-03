from typing import TYPE_CHECKING
from .model_platform import ModelPlatform
from openai import OpenAI

if TYPE_CHECKING:
    from ..models import BaseModel

class VolcengineArk(ModelPlatform):
    def __init__(self, authorization: str):
        super().__init__(api_url="https://ark.cn-beijing.volces.com/api/v3/", authorization=authorization)
        self._client = OpenAI(api_key=authorization, base_url="https://ark.cn-beijing.volces.com/api/v3")
        self.custom_extra_body = self._build_extra_body

    def _build_extra_body(self, model : "BaseModel"):
        return {"thinking": {"type": "enabled" if model._enable_thinking else "disabled"}}
    
