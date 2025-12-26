"""Agent Context - 共用的 LLM 和 Prompt 資源"""
import os
import json
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LLMResponse:
    """LLM 回應"""
    content: str
    model: str
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0


class AgentContext:
    """
    Agent 共用的上下文，包含 LLM 呼叫和 Prompt 載入功能
    
    統一管理 API 連線和 Prompt 載入，避免重複傳遞
    """
    
    _instance: Optional["AgentContext"] = None
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        prompts_dir: Optional[str] = None,
        timeout: int = 120
    ):
        self.api_key = api_key or os.getenv("API_KEY")
        self.base_url = (base_url or os.getenv("API_BASE_URL", "")).rstrip("/")
        self.timeout = timeout
        
        if not self.api_key:
            raise ValueError("API_KEY is required")
        if not self.base_url:
            raise ValueError("API_BASE_URL is required")
        
        # Prompt 目錄
        if prompts_dir is None:
            project_root = Path(__file__).resolve().parent.parent
            prompts_dir = project_root / "prompts"
        self.prompts_dir = Path(prompts_dir)
        self._prompt_cache: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def get_instance(cls) -> "AgentContext":
        """取得單例實例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def initialize(cls, api_key: str, base_url: str, **kwargs) -> "AgentContext":
        """初始化並設定單例"""
        cls._instance = cls(api_key=api_key, base_url=base_url, **kwargs)
        return cls._instance
    
    # ==================== LLM 相關 ====================
    
    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        thinking: bool = False,
        **kwargs
    ) -> LLMResponse:
        """發送 LLM 請求"""
        # 處理多模態訊息
        processed_messages = self._process_messages(messages)
        
        payload = {
            "model": model,
            "messages": processed_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        # thinking 僅 GPT 模型支援
        if thinking and "gemma" not in model.lower():
            payload["think"] = True
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json=payload,
                timeout=self.timeout
            )
            if not response.ok:
                print(f"[LLM Error] {response.status_code}: {response.text}")
            response.raise_for_status()
            
            data = response.json()
            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                model=model,
                total_tokens=data.get("eval_count", 0) + data.get("prompt_eval_count", 0),
                prompt_tokens=data.get("prompt_eval_count", 0),
                completion_tokens=data.get("eval_count", 0)
            )
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"LLM API failed: {e}")
    
    def _process_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """處理多模態訊息為 Ollama 格式"""
        processed = []
        for msg in messages:
            if isinstance(msg.get("content"), list):
                text_parts = []
                images = []
                for item in msg["content"]:
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif item.get("type") == "image_url":
                        url = item.get("image_url", {}).get("url", "")
                        if url.startswith("data:"):
                            images.append(url.split(",", 1)[-1])
                processed_msg = {"role": msg["role"], "content": "\n".join(text_parts)}
                if images:
                    processed_msg["images"] = images
                processed.append(processed_msg)
            else:
                processed.append(msg)
        return processed
    
    # ==================== Prompt 相關 ====================
    
    def load_prompt(self, name: str) -> Dict[str, Any]:
        """載入 prompt 配置"""
        if name in self._prompt_cache:
            return self._prompt_cache[name]
        
        path = self.prompts_dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Prompt not found: {path}")
        
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        
        self._prompt_cache[name] = data
        return data
    
    def format_prompt(self, name: str, variables: Dict[str, Any]) -> tuple[Optional[str], str]:
        """格式化 prompt，回傳 (system_prompt, user_prompt)"""
        data = self.load_prompt(name)
        
        system = data.get("system_prompt", "")
        user = data.get("user_prompt_template", "")
        
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, indent=2)
            user = user.replace(placeholder, str(value))
        
        return (system if system else None, user)
    
    def get_prompt_params(self, name: str) -> Dict[str, Any]:
        """取得 prompt 參數設定"""
        data = self.load_prompt(name)
        return data.get("parameters", {})
