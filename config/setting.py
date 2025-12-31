import dotenv

GLOBAL_API_URL = dotenv.get_key(".env", "API_URL") or "http://localhost:11434"
GLOBAL_API_KEY = dotenv.get_key(".env", "API_KEY") or ""
PROMPT_ROOT = "prompts/"

class AgentConfig:
    model: str
    api_url: str = None
    api_key: str = None
    thinking: bool = None
    temperature: float = None
    num_ctx: int = None
    
    def __init__(
        self,
        model: str,
        api_url: str = None, 
        api_key: str = None, 
        thinking: bool = False, 
        temperature: float = 0.7, 
        num_ctx: int = 1024
    ):
        
        self.model = model
        self.api_url = api_url or GLOBAL_API_URL
        self.api_key = api_key or GLOBAL_API_KEY
        self.thinking = thinking
        self.temperature = temperature
        self.num_ctx = num_ctx
        

AGENT_CONFIGS = {
    "CodeAnalyzer":AgentConfig(
        model="qwen2.5-coder:3b",
        api_url=dotenv.get_key(".env", "CUSTOM_API_URL") or "http://localhost:11434",
        api_key=None,
        temperature=0.3,
        num_ctx=4096
    ),
    "ProjectAnalyzer":AgentConfig(
        model="ministral-3:8b",
        api_url=dotenv.get_key(".env", "CUSTOM_API_URL") or "http://localhost:11434",
        api_key=None,
        temperature=0.7,
        num_ctx=4096
    )
}