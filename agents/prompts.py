"""
Prompt 載入與格式化

提供純函式來載入與格式化 prompt 模板。
"""
import json
from pathlib import Path
from typing import Any, Optional


_cache: dict[str, dict[str, Any]] = {}
_prompts_dir: Path = Path(__file__).parent.parent / "prompts"


def load_prompt(name: str) -> dict[str, Any]:
    """
    載入 prompt 配置
    
    Args:
        name: Prompt 名稱（對應 prompts/ 目錄下的路徑，不含 .json）
              例如：'doc_generator/designer_tpa'
    
    Returns:
        dict: Prompt 配置內容
        
    Raises:
        FileNotFoundError: 如果 prompt 檔案不存在
    """
    if name in _cache:
        return _cache[name]
    
    path = _prompts_dir / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    
    _cache[name] = data
    return data


def _flatten_variables(variables: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """
    展平嵌套的變數字典，支持 {key[subkey]} 語法
    
    Args:
        variables: 原始變數字典
        prefix: 前綴（用於遞迴）
    
    Returns:
        dict: 展平的變數字典，包含：
              - 原始鍵: 原始值
              - key[subkey]: 嵌套值
    """
    result = {}
    
    for key, value in variables.items():
        full_key = f"{prefix}[{key}]" if prefix else key
        
        if isinstance(value, dict):
            # 加入原始值（會被 JSON 序列化）
            result[full_key] = value
            # 遞迴展平嵌套鍵
            for sub_key, sub_value in value.items():
                nested_key = f"{full_key}[{sub_key}]"
                if isinstance(sub_value, (dict, list)):
                    result[nested_key] = json.dumps(sub_value, ensure_ascii=False, indent=2)
                else:
                    result[nested_key] = str(sub_value) if sub_value is not None else ""
        elif isinstance(value, list):
            result[full_key] = json.dumps(value, ensure_ascii=False, indent=2)
        else:
            result[full_key] = str(value) if value is not None else ""
    
    return result


def format_prompt(name: str, variables: dict[str, Any]) -> tuple[Optional[str], str]:
    """
    格式化 prompt
    
    支持嵌套變數語法：{key[subkey]}
    例如：variables = {"section": {"title": "Hello"}}
         可替換 {section[title]} 為 "Hello"
    
    Args:
        name: Prompt 名稱
        variables: 要替換的變數字典（支持嵌套）
    
    Returns:
        tuple[str | None, str]: (system_prompt, user_prompt)
            system_prompt 如果不存在則為 None
    """
    data = load_prompt(name)
    
    system = data.get("system_prompt", "")
    user = data.get("user_prompt_template", "")
    
    # 展平變數以支持嵌套語法
    flat_vars = _flatten_variables(variables)
    
    # 先替換嵌套鍵（較長的優先，避免部分匹配）
    for key in sorted(flat_vars.keys(), key=len, reverse=True):
        placeholder = "{" + key + "}"
        value = flat_vars[key]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, indent=2)
        user = user.replace(placeholder, str(value))
    
    return (system if system else None, user)


def get_prompt_params(name: str) -> dict[str, Any]:
    """
    取得 prompt 參數設定
    
    Args:
        name: Prompt 名稱
    
    Returns:
        dict: 參數設定（temperature, max_tokens 等）
    """
    data = load_prompt(name)
    return data.get("parameters", {})


def clear_cache() -> None:
    """清除 prompt 快取"""
    global _cache
    _cache = {}
