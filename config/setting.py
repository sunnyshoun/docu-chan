import dotenv

GLOBAL_API_URL = dotenv.get_key(".env", "GLOBAL_API_URL") or "http://localhost:11434"
GLOBAL_API_KEY = dotenv.get_key(".env", "GLOBAL_API_KEY") or ""
PROMPT_ROOT = "prompts/"
LOG_ROOT = "logs/"

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
        num_ctx: int = 4096
    ):
        
        self.model = model
        self.api_url = api_url or GLOBAL_API_URL
        self.api_key = api_key or GLOBAL_API_KEY
        self.thinking = thinking
        self.temperature = temperature
        self.num_ctx = num_ctx
        

AGENT_CONFIGS = {
    "CodeAnalyzer":AgentConfig(
        # model="qwen2.5-coder:7b",
        model="gemma3:12b",
        api_url=dotenv.get_key(".env", "CUSTOM_API_URL") or GLOBAL_API_URL,
    ),
    "ImageAnalyzer":AgentConfig(
        model="ministral-3:8b",
        api_url=dotenv.get_key(".env", "CUSTOM_API_URL") or GLOBAL_API_URL,
    ),
    "ProjectAnalyzer":AgentConfig(
        model="ministral-3:8b",
        api_url=dotenv.get_key(".env", "CUSTOM_API_URL") or GLOBAL_API_URL,
    ),
    "Summarize":AgentConfig(
        model="ministral-3:8b",
        api_url=dotenv.get_key(".env", "CUSTOM_API_URL") or GLOBAL_API_URL,
        api_key=None,
        temperature=0.1,
        num_ctx=32000
    ),
}