"""
Tools module - 提供給 AI Agent 使用的工具函式

Usage:
    from tools import get_tools, execute, get_tool_definitions
    
    # 取得指定 tools 的定義（給 API 用）
    definitions = get_tools("read_file", "report_summary")
    
    # 執行 tool
    result = execute("read_file", file_path="main.py", n=50)
"""

from .registry import (
    tool,
    get_tools,
    get_tool_definitions,
    execute,
    list_tools
)

# 匯入 tools 以觸發註冊
from . import file_ops

__all__ = [
    "tool",
    "get_tools",
    "get_tool_definitions", 
    "execute",
    "list_tools"
]
