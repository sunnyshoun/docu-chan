"""
Base Agent - 所有 Agent 共用的基礎類別

使用 Ollama Python SDK 進行 LLM 呼叫。
支援同步與非同步兩種模式。
"""
import json
import re
import logging
from abc import ABC
from typing import Any, Optional

from ollama import ChatResponse

from .client import get_client, get_async_client
from .prompts import format_prompt, get_prompt_params


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
        name: str,
        model: str,
        think: bool = False
    ):
        """
        初始化 Agent
        
        Args:
            name: Agent 名稱（用於日誌）
            model: 使用的模型名稱
            think: 是否啟用 thinking 模式
        """
        self.name = name
        self.model = model
        self.think = think
        self.messages: list[dict[str, Any]] = []
        self.logger = logging.getLogger(f"agent.{name}")
    
    # ==================== Chat ====================
    
    def chat(
        self,
        prompt_name: str,
        variables: dict[str, Any],
        images: Optional[list[str]] = None,
        tools: Optional[list[dict]] = None,
        format: Optional[str | dict] = None,
        keep_history: bool = True
    ):
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
            "temperature": params.get("temperature", 0.7),
            "num_predict": params.get("max_tokens", 4096),
        }
        
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": all_messages,
            "options": options,
            "stream": False,
        }
        
        if self.think:
            kwargs["think"] = True
        if tools:
            kwargs["tools"] = tools
        if format:
            kwargs["format"] = format
        
        # 呼叫 Ollama
        response = get_client().chat(**kwargs)
        
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
        }
        
        if self.think:
            kwargs["think"] = True
        if tools:
            kwargs["tools"] = tools
        if format:
            kwargs["format"] = format
        
        response = get_client().chat(stream=False, **kwargs)
        
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
    ):
        """
        非同步呼叫 LLM（使用 prompt template）
        
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
            "temperature": params.get("temperature", 0.7),
            "num_predict": params.get("max_tokens", 4096),
        }
        
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": all_messages,
            "options": options,
            "stream": False,
        }
        
        if self.think:
            kwargs["think"] = True
        if tools:
            kwargs["tools"] = tools
        if format:
            kwargs["format"] = format
        
        # 非同步呼叫 Ollama
        response = await get_async_client().chat(**kwargs)
        
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
    
    async def chat_raw_async(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict]] = None,
        format: Optional[str | dict] = None,
        keep_history: bool = False
    ):
        """
        非同步直接傳入 messages 呼叫（不使用 prompt template）
        
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
        
        if self.think:
            kwargs["think"] = True
        if tools:
            kwargs["tools"] = tools
        if format:
            kwargs["format"] = format
        
        response = await get_async_client().chat(**kwargs)
        
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
        
        Args:
            text: 可能包含 JSON 的文字
        
        Returns:
            dict: 解析後的 JSON 物件
            
        Raises:
            json.JSONDecodeError: 如果解析失敗
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
    
    def log(self, message: str) -> None:
        """記錄日誌訊息"""
        self.logger.info(f"[{self.name}] {message}")
        print(f"[{self.name}] {message}")

