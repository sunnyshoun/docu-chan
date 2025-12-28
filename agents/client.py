"""
Ollama Client 管理

從環境變數讀取配置並建立共用的 Ollama Client。
"""
import os
from typing import Optional

from ollama import Client


_client: Optional[Client] = None


def get_client() -> Client:
    """
    取得共用的 Ollama Client（單例模式）
    
    從環境變數讀取：
    - API_BASE_URL: API 端點
    - API_KEY: API 密鑰（用於 Authorization header）
    
    Returns:
        Client: Ollama Client 實例
    """
    global _client
    if _client is None:
        host = os.getenv("API_BASE_URL", "http://localhost:11434")
        api_key = os.getenv("API_KEY", "")
        
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        _client = Client(host=host, headers=headers)
    return _client


def reset_client() -> None:
    """重設 Client（用於測試或重新配置）"""
    global _client
    _client = None
