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


def format_prompt(name: str, variables: dict[str, Any]) -> tuple[Optional[str], str]:
    """
    格式化 prompt
    
    Args:
        name: Prompt 名稱
        variables: 要替換的變數字典
    
    Returns:
        tuple[str | None, str]: (system_prompt, user_prompt)
            system_prompt 如果不存在則為 None
    """
    data = load_prompt(name)
    
    system = data.get("system_prompt", "")
    user = data.get("user_prompt_template", "")
    
    for key, value in variables.items():
        placeholder = "{" + key + "}"
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
