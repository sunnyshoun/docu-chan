"""
Base Agent - 所有 Agent 共用的基礎類別

使用 Ollama Python SDK 進行 LLM 呼叫。
"""
import json
import re
from abc import ABC
from typing import Any, Optional

from ollama import Client, AsyncClient, ChatResponse

from config.agents import AgentConfig, get_agent_config
from .prompts import format_prompt, get_prompt_params
from utils.logger import get_logger


class BaseAgent(ABC):
    """
    Agent 基礎類別
    
    功能：
    - LLM 呼叫（chat, chat_raw）
    - 對話歷史管理（messages）
    - Thinking 模式支援
    - Tool calling 支援
    - JSON 解析工具
    """
    
    def __init__(
        self,
        agent_name: str,
        config: Optional[AgentConfig] = None,
        display_name: Optional[str] = None
    ):
        """
        初始化 Agent
        
        Args:
            agent_name: Agent 配置名稱 (對應 agents.json 中的 key)
            config: 直接傳入配置 (優先於 agent_name 讀取)
            display_name: 顯示名稱 (用於日誌，預設使用 agent_name)
        """
        self.agent_name = agent_name
        self.display_name = display_name or agent_name
        
        # 載入配置
        if config:
            self.config = config
        else:
            self.config = get_agent_config(agent_name)
        
        self.messages: list[dict[str, Any]] = []
        self._logger = None
        self._client: Optional[Client] = None
        self._async_client: Optional[AsyncClient] = None
    
    @property
    def model(self) -> str:
        return self.config.model
    
    @property
    def logger(self):
        """取得 logger（延遲初始化）"""
        if self._logger is None:
            self._logger = get_logger()
        return self._logger
    
    def _get_client(self) -> Client:
        """取得 Ollama Client"""
        if self._client is None:
            import os
            host = self.config.api_url or os.getenv("API_BASE_URL", "http://localhost:11434")
            api_key = self.config.api_key or os.getenv("API_KEY", "")
            
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            self._client = Client(host=host, headers=headers)
        return self._client
    
    def _get_async_client(self) -> AsyncClient:
        """取得 Ollama AsyncClient"""
        if self._async_client is None:
            import os
            host = self.config.api_url or os.getenv("API_BASE_URL", "http://localhost:11434")
            api_key = self.config.api_key or os.getenv("API_KEY", "")
            
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            self._async_client = AsyncClient(host=host, headers=headers)
        return self._async_client
    
    # ==================== Chat ====================
    
    def chat(
        self,
        prompt_name: str,
        variables: dict[str, Any],
        images: Optional[list[str]] = None,
        tools: Optional[list[dict]] = None,
        format: Optional[str | dict] = None,
        keep_history: bool = True
    ) -> ChatResponse:
        """
        呼叫 LLM（使用 prompt template）
        
        Args:
            prompt_name: Prompt 名稱（對應 prompts/ 目錄下的 JSON）
            variables: Prompt 變數
            images: Base64 圖片列表（用於多模態模型）
            tools: Tool definitions（用於 function calling）
            format: 輸出格式（"json" 或 JSON schema）
            keep_history: 是否保留 messages 歷史
        
        Returns:
            ChatResponse: Ollama 回應物件
        """
        system, user = format_prompt(prompt_name, variables)
        params = get_prompt_params(prompt_name)
        
        # 建立新訊息
        new_messages: list[dict[str, Any]] = []
        if system:
            new_messages.append({"role": "system", "content": system})
        
        user_msg: dict[str, Any] = {"role": "user", "content": user}
        if images:
            user_msg["images"] = images
        new_messages.append(user_msg)
        
        # 合併歷史訊息
        all_messages = self.messages + new_messages
        
        # 建立呼叫參數
        options = {
            "temperature": params.get("temperature", self.config.temperature),
            "num_predict": params.get("max_tokens", self.config.max_tokens),
        }
        
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": all_messages,
            "options": options,
            "stream": False,
        }
        
        if self.config.thinking:
            kwargs["think"] = True
        if tools and self.config.use_tools:
            kwargs["tools"] = tools
        if format:
            kwargs["format"] = format
        
        # 呼叫 Ollama
        response = self._get_client().chat(**kwargs)
        
        # 保存歷史
        if keep_history:
            self.messages.extend(new_messages)
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": response.message.content or ""
            }
            if response.message.tool_calls:
                assistant_msg["tool_calls"] = response.message.tool_calls
            self.messages.append(assistant_msg)
        
        return response
    
    def chat_raw(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict]] = None,
        format: Optional[str | dict] = None,
        keep_history: bool = False
    ) -> ChatResponse:
        """
        直接傳入 messages 呼叫（不使用 prompt template）
        
        Args:
            messages: 訊息列表
            tools: Tool definitions
            format: 輸出格式
            keep_history: 是否保存到歷史
        
        Returns:
            ChatResponse: Ollama 回應物件
        """
        all_messages = self.messages + messages
        
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": all_messages,
            "stream": False,
        }
        
        if self.config.thinking:
            kwargs["think"] = True
        if tools and self.config.use_tools:
            kwargs["tools"] = tools
        if format:
            kwargs["format"] = format
        
        response = self._get_client().chat(**kwargs)
        
        if keep_history:
            self.messages.extend(messages)
            keys_to_keep = ["role", "content", "tool_calls"]
            assistant_msg = response.message.model_dump()
            self.messages.append({key: assistant_msg[key] for key in keys_to_keep if key in assistant_msg})
        
        return response
    
    def add_tool_result(self, tool_name: str, result: str) -> None:
        """
        加入 tool 執行結果到歷史
        
        Args:
            tool_name: Tool 名稱
            result: 執行結果
        """
        self.messages.append({
            "role": "tool",
            "content": result,
            "tool_name": tool_name
        })
    
    # ==================== Async Chat ====================
    
    async def chat_async(
        self,
        prompt_name: str,
        variables: dict[str, Any],
        images: Optional[list[str]] = None,
        tools: Optional[list[dict]] = None,
        format: Optional[str | dict] = None,
        keep_history: bool = True
    ) -> ChatResponse:
        """
        非同步呼叫 LLM（使用 prompt template）
        """
        system, user = format_prompt(prompt_name, variables)
        params = get_prompt_params(prompt_name)
        
        new_messages: list[dict[str, Any]] = []
        if system:
            new_messages.append({"role": "system", "content": system})
        
        user_msg: dict[str, Any] = {"role": "user", "content": user}
        if images:
            user_msg["images"] = images
        new_messages.append(user_msg)
        
        all_messages = self.messages + new_messages
        
        options = {
            "temperature": params.get("temperature", self.config.temperature),
            "num_predict": params.get("max_tokens", self.config.max_tokens),
        }
        
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": all_messages,
            "options": options,
            "stream": False,
        }
        
        if self.config.thinking:
            kwargs["think"] = True
        if tools and self.config.use_tools:
            kwargs["tools"] = tools
        if format:
            kwargs["format"] = format
        
        response = await self._get_async_client().chat(**kwargs)
        
        if keep_history:
            self.messages.extend(new_messages)
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": response.message.content or ""
            }
            if response.message.tool_calls:
                assistant_msg["tool_calls"] = response.message.tool_calls
            self.messages.append(assistant_msg)
        
        return response
    
    async def chat_raw_async(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict]] = None,
        format: Optional[str | dict] = None,
        keep_history: bool = False,
        options: Optional[dict[str, Any]] = None
    ) -> ChatResponse:
        """
        非同步直接傳入 messages 呼叫
        """
        import time
        all_messages = self.messages + messages
        
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": all_messages,
            "stream": False,
        }
        
        if self.config.thinking:
            kwargs["think"] = True
        if tools and self.config.use_tools:
            kwargs["tools"] = tools
        if format:
            kwargs["format"] = format
        if options:
            kwargs["options"] = options
        
        self.logger.debug(f"[{self.display_name}] API 請求開始 - model={self.model}, msg_count={len(all_messages)}")
        start_time = time.time()
        
        try:
            self.logger.debug(f"[{self.display_name}] chat - model: {kwargs["model"]}, think: {kwargs.get("think")}, format: {kwargs.get("format")}")
            response = await self._get_async_client().chat(**kwargs)
            elapsed = time.time() - start_time
            content_len = len(response.message.content) if response.message.content else 0
            self.logger.debug(f"[{self.display_name}] API 回應完成 - {elapsed:.2f}s, content_len={content_len}")
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"[{self.display_name}] API 錯誤 - {elapsed:.2f}s, error={e}")
            raise
        
        if keep_history:
            self.messages.extend(messages)
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": response.message.content or ""
            }
            if response.message.tool_calls:
                assistant_msg["tool_calls"] = response.message.tool_calls
            self.messages.append(assistant_msg)
        
        return response
    
    # ==================== History ====================
    
    def clear_messages(self) -> None:
        """清除對話歷史"""
        self.messages = []
    
    def get_messages(self) -> list[dict[str, Any]]:
        """取得對話歷史副本"""
        return self.messages.copy()
    
    # ==================== Utils ====================
    
    def parse_json(self, text: str) -> dict[str, Any]:
        """
        解析 JSON（支援 code block）
        """
        # 嘗試從 code block 提取
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            text = match.group(1)
        else:
            # 嘗試找到 JSON 物件
            start, end = text.find('{'), text.rfind('}')
            if start != -1 and end != -1:
                text = text[start:end+1]
        
        return json.loads(text)
    
    def log(self, message: str, level: str = "debug") -> None:
        """記錄日誌訊息"""
        full_msg = f"[{self.display_name}] {message}"
        level = level.lower()
        if level == "debug":
            self.logger.debug(full_msg)
        elif level == "info":
            self.logger.info(full_msg)
        elif level == "warning":
            self.logger.warning(full_msg)
        elif level == "error":
            self.logger.error(full_msg)
        else:
            self.logger.debug(full_msg)
    
    def log_progress(self, message: str) -> None:
        """記錄進度訊息"""
        self.logger.progress(f"[{self.display_name}] {message}")

