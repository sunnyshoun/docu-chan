from pathlib import Path
from logging import Logger, getLogger, DEBUG, INFO, WARNING, ERROR, CRITICAL
from typing import Callable
from config.setting import PROMPT_ROOT, AgentConfig, AGENT_CONFIGS
from agents.models import ChatRequest, ChatResponse
from agents.llm_client import chat, async_chat

class BaseAgent:
    agent_config: AgentConfig
    prompt_dir: Path
    logger: Logger
    messages = []
    
    def __init__(self, name: str):
        self.name = name
        self.prompt_dir = Path(PROMPT_ROOT) / name
        self.agent_config = AGENT_CONFIGS[name]
        self.logger = getLogger(name)

    def chat(self, messages: list[dict], tools: list[Callable] = None, format: str = None) -> ChatResponse:
        request = ChatRequest(
            messages=messages,
            model=self.agent_config.model,
            think=self.agent_config.thinking,
            tools=tools,
            num_ctx=self.agent_config.num_ctx,
            temperature=self.agent_config.temperature,
            format=format
        )
        
        return chat(request, 
            api_url=self.agent_config.api_url,
            api_key=self.agent_config.api_key
        )
    
    async def async_chat(self, messages: list[dict], tools: list[Callable] = None, format: str = None) -> ChatResponse:
        request = ChatRequest(
            messages=messages,
            model=self.agent_config.model,
            think=self.agent_config.thinking,
            tools=tools,
            num_ctx=self.agent_config.num_ctx,
            temperature=self.agent_config.temperature,
            format=format
        )
        
        return await async_chat(request, 
            api_url=self.agent_config.api_url,
            api_key=self.agent_config.api_key
        )
        
    def log(self, level: int, message: str):
        LOG_LEVELS = {
            1: DEBUG,
            2: INFO,
            3: WARNING,
            4: ERROR,
            5: CRITICAL
        }
        
        log_level = LOG_LEVELS.get(level, INFO)
        self.logger.log(log_level, f"[Agent {self.name}] {message}")