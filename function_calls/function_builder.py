import inspect
import re
from dataclasses import dataclass, field
from typing import Callable, Any, Dict, List


def _safe_type_name(tp: Any) -> str:
    """获取友好的类型名称（兼容 typing 中的泛型）。"""
    try:
        if hasattr(tp, "__name__"):
            return tp.__name__  # builtin / class
        return str(tp).replace("typing.", "")
    except Exception:
        return "any"


_PYTHON_TO_JSON_SCHEMA = {
    "int": "integer",
    "float": "number",
    "str": "string",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
    "Any": "any",
}


@dataclass(slots=True)
class FunctionBuilder:
    """构建函数工具

    功能:
        - 解析函数签名，收集参数类型/描述/必填列表
        - 生成符合 OpenAI function calling / JSON schema 风格的描述

    参数:
        function: 需要构建的函数对象
        description: 函数总体描述
        enforce_annotations: 是否强制所有非 self 参数必须有类型注解
    """

    function: Callable
    description: str
    enforce_annotations: bool = True

    name: str = field(init=False)
    parameters: Dict[str, Dict[str, Any]] = field(init=False, default_factory=dict)
    required_params: List[str] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        sig = inspect.signature(self.function)
        self.name = self.function.__name__

        params = sig.parameters
        if not params:
            self.parameters = {}
            self.required_params = []
            return

        param_docs = self._get_param_docs(self.function)
        props: Dict[str, Dict[str, Any]] = {}
        required: List[str] = []

        for pname, param in params.items():
            if pname == "self":
                continue

            if param.annotation is inspect.Parameter.empty:
                if self.enforce_annotations:
                    raise ValueError(f"参数 {pname} 必须有类型注解")
                annotation_name = "Any"
            else:
                annotation_name = _safe_type_name(param.annotation)

            json_type = _PYTHON_TO_JSON_SCHEMA.get(annotation_name, "string")

            # 处理可变参数 *args/**kwargs
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                json_type = "array" if param.kind == inspect.Parameter.VAR_POSITIONAL else "object"

            props[pname] = {
                "type": json_type,
                "python_type": annotation_name,
                "description": param_docs.get(pname, ""),
            }

            if param.default is inspect.Parameter.empty and param.kind not in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                required.append(pname)

        self.parameters = props
        self.required_params = required

    # ------------------------------------------------------------------
    # 构建输出
    # ------------------------------------------------------------------
    def build_function_json(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required_params,
            },
        }

    # ------------------------------------------------------------------
    # 文档解析
    # ------------------------------------------------------------------
    @staticmethod
    def _get_param_docs(func: Callable) -> Dict[str, str]:
        """从 docstring 提取参数说明.

        支持两种格式:
            1) 简单行: "param: 描述"
            2) Google/Numpy 风格 Args: 块中的 "name (type): 描述"
        """
        doc = inspect.getdoc(func) or ""
        param_docs: Dict[str, str] = {}

        # 1) 简单 "name: desc" 模式
        for name, desc in re.findall(r"^\s*(\w+):\s*(.+)$", doc, re.MULTILINE):
            param_docs.setdefault(name, desc.strip())

        # 2) Args: 块中的模式
        args_section = re.search(r"Args?:\s*(.+?)(?:\n\S|$)", doc, re.DOTALL)
        if args_section:
            block = args_section.group(1)
            for m in re.finditer(r"^\s*(\w+)\s*\([^)]*\):\s*(.+)$", block, re.MULTILINE):
                name, desc = m.groups()
                param_docs[name] = param_docs.get(name) or desc.strip()

        return param_docs

    # 示例函数（可移除）
    @staticmethod
    def _foo(a: int, b: str):  # pragma: no cover - demo only
        """Demo 函数

        Args:
            a (int): 第一个参数，整数类型
            b (str): 第二个参数，字符串类型
        """
        return a, b
