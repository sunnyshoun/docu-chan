"""
Ollama Client 管理

從環境變數讀取配置並建立共用的 Ollama Client。
支援同步與非同步（AsyncClient）兩種模式。
"""
import os
from typing import Optional

from ollama import Client, AsyncClient


_client: Optional[Client] = None
_async_client: Optional[AsyncClient] = None


def _get_connection_config() -> tuple[str, dict[str, str]]:
    """
    取得連線配置
    
    Returns:
        tuple: (host, headers)
    """
    host = os.getenv("API_BASE_URL", "http://localhost:11434")
    api_key = os.getenv("API_KEY", "")
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    return host, headers


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
        host, headers = _get_connection_config()
        _client = Client(host=host, headers=headers)
    return _client


def get_async_client() -> AsyncClient:
    """
    取得共用的 Ollama AsyncClient（單例模式）
    
    用於非同步操作，從環境變數讀取：
    - API_BASE_URL: API 端點
    - API_KEY: API 密鑰（用於 Authorization header）
    
    Returns:
        AsyncClient: Ollama AsyncClient 實例
    """
    global _async_client
    if _async_client is None:
        host, headers = _get_connection_config()
        _async_client = AsyncClient(host=host, headers=headers)
    return _async_client


def reset_client() -> None:
    """重設 Client（用於測試或重新配置）"""
    global _client, _async_client
    _client = None
    _async_client = None
