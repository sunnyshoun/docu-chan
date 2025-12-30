from pathlib import Path
from config.setting import PROMPT_ROOT, AgentConfig, AGENT_CONFIGS
from agents.models import ChatRequest
from agents.llm_client import chat, async_chat

class BaseAgent:
    agent_config: AgentConfig
    prompt_dir: Path
    messages = []
    
    def __init__(self, name: str):
        self.name = name
        self.prompt_dir = Path(PROMPT_ROOT) / name
        self.agent_config = AGENT_CONFIGS[name]

    def chat(self, messages: list[dict], tools: list[callable] = None, format: str = None) -> str:
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
    
    async def async_chat(self, messages: list[dict], tools: list[callable] = None, format: str = None) -> str:
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