"""
Agent Configuration - 每個 Agent 獨立配置

每個 Agent 可配置：
- model: 使用的 LLM 模型
- api_url: API 端點 (可選，預設使用全域)
- api_key: API 密鑰 (可選，預設使用全域)
- use_tools: 是否啟用 tool calling
- thinking: 是否啟用 thinking 模式
"""
import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class AgentConfig:
    """單一 Agent 配置"""
    model: str
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    use_tools: bool = False
    thinking: bool = False
    temperature: float = 0.7
    max_tokens: int = 4096
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "api_url": self.api_url,
            "api_key": self.api_key,
            "use_tools": self.use_tools,
            "thinking": self.thinking,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        return cls(
            model=data.get("model", "gpt-oss:20b"),
            api_url=data.get("api_url"),
            api_key=data.get("api_key"),
            use_tools=data.get("use_tools", False),
            thinking=data.get("thinking", False),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 4096)
        )


# Agent 名稱常數
class AgentName:
    """Agent 名稱定義"""
    # Phase 1 - Analyzer
    FILE_WORKER = "file_worker"
    IMAGE_WORKER = "image_worker"
    ANALYSIS_MANAGER = "analysis_manager"
    
    # Phase 2 - Planner
    DOC_PLANNER = "doc_planner"
    
    # Phase 3 - Generator
    DIAGRAM_DESIGNER = "diagram_designer"
    MERMAID_CODER = "mermaid_coder"
    VISUAL_INSPECTOR = "visual_inspector"
    QUESTION_GENERATOR = "question_generator"
    TECH_WRITER = "tech_writer"


# 預設配置
DEFAULT_AGENT_CONFIGS: Dict[str, AgentConfig] = {
    # Phase 1 - Analyzer
    AgentName.FILE_WORKER: AgentConfig(
        model="gpt-oss:20b",
        use_tools=True,
        thinking=False
    ),
    AgentName.IMAGE_WORKER: AgentConfig(
        model="gemma3:4b",
        use_tools=False,
        thinking=False
    ),
    AgentName.ANALYSIS_MANAGER: AgentConfig(
        model="gpt-oss:120b",
        use_tools=False,
        thinking=True
    ),
    
    # Phase 2 - Planner
    AgentName.DOC_PLANNER: AgentConfig(
        model="gpt-oss:20b",
        use_tools=False,
        thinking=False
    ),
    
    # Phase 3 - Generator
    AgentName.DIAGRAM_DESIGNER: AgentConfig(
        model="gpt-oss:20b",
        use_tools=True,
        thinking=True
    ),
    AgentName.MERMAID_CODER: AgentConfig(
        model="gpt-oss:20b",
        use_tools=False,
        thinking=True
    ),
    AgentName.VISUAL_INSPECTOR: AgentConfig(
        model="gemma3:4b",
        use_tools=False,
        thinking=False
    ),
    AgentName.QUESTION_GENERATOR: AgentConfig(
        model="gpt-oss:20b",
        use_tools=False,
        thinking=False
    ),
    AgentName.TECH_WRITER: AgentConfig(
        model="gpt-oss:20b",
        use_tools=True,
        thinking=False
    ),
}


class AgentConfigManager:
    """
    Agent 配置管理器
    
    讀取順序（後者覆蓋前者）:
    1. DEFAULT_AGENT_CONFIGS (程式碼預設)
    2. config/agents.json (專案配置檔)
    3. 環境變數 AGENT_{NAME}_MODEL 等
    """
    
    _instance: Optional["AgentConfigManager"] = None
    _configs: Dict[str, AgentConfig] = {}
    
    def __init__(self, config_file: Optional[Path] = None):
        self._config_file = config_file
        self._load_configs()
    
    def _load_configs(self):
        """載入配置"""
        # 1. 從預設值開始
        self._configs = {k: AgentConfig(**v.to_dict()) for k, v in DEFAULT_AGENT_CONFIGS.items()}
        
        # 2. 從配置檔載入
        if self._config_file and self._config_file.exists():
            self._load_from_file(self._config_file)
        else:
            # 嘗試預設路徑
            default_path = Path(__file__).parent / "agents.json"
            if default_path.exists():
                self._load_from_file(default_path)
        
        # 3. 從環境變數載入
        self._load_from_env()
    
    def _load_from_file(self, path: Path):
        """從 JSON 檔載入配置"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for name, config_data in data.items():
                if name in self._configs:
                    # 合併配置（保留未指定的預設值）
                    current = self._configs[name].to_dict()
                    current.update(config_data)
                    self._configs[name] = AgentConfig.from_dict(current)
                else:
                    self._configs[name] = AgentConfig.from_dict(config_data)
        except Exception as e:
            print(f"Warning: Failed to load agent config from {path}: {e}")
    
    def _load_from_env(self):
        """從環境變數載入配置"""
        for name in self._configs:
            env_prefix = f"AGENT_{name.upper()}_"
            
            # MODEL
            model_env = os.getenv(f"{env_prefix}MODEL")
            if model_env:
                self._configs[name].model = model_env
            
            # API_URL
            api_url_env = os.getenv(f"{env_prefix}API_URL")
            if api_url_env:
                self._configs[name].api_url = api_url_env
            
            # API_KEY
            api_key_env = os.getenv(f"{env_prefix}API_KEY")
            if api_key_env:
                self._configs[name].api_key = api_key_env
            
            # THINKING
            thinking_env = os.getenv(f"{env_prefix}THINKING")
            if thinking_env:
                self._configs[name].thinking = thinking_env.lower() in ("true", "1", "yes")
            
            # USE_TOOLS
            tools_env = os.getenv(f"{env_prefix}USE_TOOLS")
            if tools_env:
                self._configs[name].use_tools = tools_env.lower() in ("true", "1", "yes")
    
    def get(self, agent_name: str) -> AgentConfig:
        """取得 Agent 配置"""
        if agent_name not in self._configs:
            # 回傳預設配置
            return AgentConfig(model="gpt-oss:20b")
        return self._configs[agent_name]
    
    def set(self, agent_name: str, config: AgentConfig):
        """設定 Agent 配置"""
        self._configs[agent_name] = config
    
    def save(self, path: Optional[Path] = None):
        """儲存配置到檔案"""
        save_path = path or self._config_file or Path(__file__).parent / "agents.json"
        data = {name: config.to_dict() for name, config in self._configs.items()}
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def get_instance(cls, config_file: Optional[Path] = None) -> "AgentConfigManager":
        """取得單例實例"""
        if cls._instance is None:
            cls._instance = cls(config_file)
        return cls._instance
    
    @classmethod
    def reset(cls):
        """重置實例"""
        cls._instance = None


# 便利函數
def get_agent_config(agent_name: str) -> AgentConfig:
    """取得 Agent 配置的便利函數"""
    return AgentConfigManager.get_instance().get(agent_name)


def load_agent_configs(config_file: Optional[Path] = None) -> AgentConfigManager:
    """載入 Agent 配置"""
    AgentConfigManager.reset()
    return AgentConfigManager.get_instance(config_file)
