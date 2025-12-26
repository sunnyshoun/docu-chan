"""Base Agent class for Doc Generator system"""
import json
import re
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from .context import AgentContext, LLMResponse


@dataclass
class AgentResult:
    """Agent 執行結果"""
    success: bool
    data: Any
    raw_response: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data if not hasattr(self.data, 'to_dict') else self.data.to_dict(),
            "error": self.error,
            "metadata": self.metadata
        }


class BaseAgent:
    """Agent 基礎類別"""
    
    def __init__(
        self,
        name: str = "BaseAgent",
        model: Optional[str] = None,
        use_thinking: bool = False,
        context: Optional[AgentContext] = None
    ):
        self.ctx = context or AgentContext.get_instance()
        self.name = name
        self.model = model
        self.use_thinking = use_thinking
        self._history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(f"agent.{name}")
    
    def _call_llm(
        self,
        prompt_name: str,
        variables: Dict[str, Any],
        model: Optional[str] = None,
        images: Optional[List[str]] = None,
        thinking: Optional[bool] = None,
    ) -> LLMResponse:
        """呼叫 LLM"""
        params = self.ctx.get_prompt_params(prompt_name)
        system_prompt, user_prompt = self.ctx.format_prompt(prompt_name, variables)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if images:
            content = [{"type": "text", "text": user_prompt}]
            for img in images:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img}"}
                })
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": user_prompt})
        
        use_think = thinking if thinking is not None else self.use_thinking
        
        return self.ctx.chat(
            messages,
            model=model or self.model,
            temperature=params.get("temperature", 0.7),
            max_tokens=params.get("max_tokens", 4096),
            thinking=use_think
        )
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析 JSON 回應"""
        # 嘗試從 code block 提取
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
        if match:
            json_str = match.group(1)
        else:
            json_str = response.strip()
            start, end = json_str.find('{'), json_str.rfind('}')
            if start != -1 and end != -1:
                json_str = json_str[start:end+1]
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # 修復常見錯誤
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
            json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)
            return json.loads(json_str)
    
    def _log(self, message: str, level: str = "info"):
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(f"[{self.name}] {message}")
        print(f"[{self.name}] [{level.upper()}] {message}")
    
    def _add_to_history(self, action: str, data: Any):
        self._history.append({"action": action, "data": data})
    
    def get_history(self) -> List[Dict[str, Any]]:
        return self._history.copy()
    
    def clear_history(self):
        self._history.clear()
