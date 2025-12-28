"""
Tool Registry - 自動從函式產生 tool definitions

利用 Python docstring 和 type hints 自動產生 OpenAI 格式的 tool schema。
"""
import inspect
import re
from typing import Any, Callable, get_type_hints, Optional


# 全域 registry
_registry: dict[str, Callable] = {}


def tool(func: Callable) -> Callable:
    """
    裝飾器：註冊 tool function
    
    Example:
        @tool
        def read_file(file_path: str, n: int = -1) -> str:
            '''Read file content.'''
            ...
    """
    _registry[func.__name__] = func
    return func


def get_tool_definition(func: Callable) -> dict:
    """
    從函式自動產生 OpenAI tool schema
    
    Args:
        func: 要轉換的函式
        
    Returns:
        OpenAI function calling 格式的 dict
    """
    hints = get_type_hints(func) if hasattr(func, '__annotations__') else {}
    sig = inspect.signature(func)
    
    # 解析參數
    properties = {}
    required = []
    
    for name, param in sig.parameters.items():
        if name in ('kwargs', 'args', 'self'):
            continue
            
        prop = {
            "type": _python_type_to_json(hints.get(name, str)),
            "description": _parse_param_doc(func.__doc__, name)
        }
        properties[name] = prop
        
        if param.default is inspect.Parameter.empty:
            required.append(name)
    
    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": _parse_main_doc(func.__doc__),
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }


def get_tools(*names: str) -> list[dict]:
    """
    取得指定 tools 的 definitions（給 API 用）
    
    Args:
        *names: tool 名稱列表
        
    Returns:
        list of tool definitions
        
    Example:
        tools = get_tools("read_file", "report_summary")
    """
    result = []
    for name in names:
        if name not in _registry:
            raise KeyError(f"Tool not found: {name}")
        result.append(get_tool_definition(_registry[name]))
    return result


def get_tool_definitions(category: Optional[str] = None) -> list[dict]:
    """
    取得所有已註冊 tools 的 definitions
    
    Args:
        category: 過濾類別（目前未使用）
        
    Returns:
        list of all tool definitions
    """
    return [get_tool_definition(func) for func in _registry.values()]


def execute(name: str, **kwargs) -> Any:
    """
    執行指定的 tool
    
    Args:
        name: tool 名稱
        **kwargs: tool 參數
        
    Returns:
        tool 執行結果
    """
    if name not in _registry:
        raise KeyError(f"Tool not found: {name}")
    return _registry[name](**kwargs)


def list_tools() -> list[str]:
    """列出所有已註冊的 tool 名稱"""
    return list(_registry.keys())


# ============================================================
# Helper functions
# ============================================================

def _python_type_to_json(python_type) -> str:
    """將 Python 型別轉換為 JSON Schema 型別"""
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null"
    }
    
    # 處理 Optional, Union 等
    origin = getattr(python_type, '__origin__', None)
    if origin is not None:
        # Optional[X] = Union[X, None]
        args = getattr(python_type, '__args__', ())
        if type(None) in args:
            # 取非 None 的型別
            for arg in args:
                if arg is not type(None):
                    return _python_type_to_json(arg)
        return "string"
    
    return type_map.get(python_type, "string")


def _parse_main_doc(docstring: Optional[str]) -> str:
    """從 docstring 解析主要描述（第一段）"""
    if not docstring:
        return ""
    
    lines = docstring.strip().split('\n')
    description_lines = []
    
    for line in lines:
        stripped = line.strip()
        # 遇到 Args:, Returns: 等就停止
        if stripped.lower().startswith(('args:', 'returns:', 'raises:', 'example:')):
            break
        description_lines.append(stripped)
    
    return ' '.join(description_lines).strip()


def _parse_param_doc(docstring: Optional[str], param_name: str) -> str:
    """從 docstring 解析特定參數的描述"""
    if not docstring:
        return ""
    
    # 尋找 Args: 區塊
    in_args = False
    for line in docstring.split('\n'):
        stripped = line.strip()
        
        if stripped.lower().startswith('args:'):
            in_args = True
            continue
        
        if in_args:
            # 遇到其他區塊就結束
            if stripped.lower().startswith(('returns:', 'raises:', 'example:')):
                break
            
            # 解析參數行：param_name: description 或 param_name (type): description
            match = re.match(rf'{param_name}\s*(?:\([^)]*\))?\s*:\s*(.+)', stripped)
            if match:
                return match.group(1).strip()
    
    return ""
