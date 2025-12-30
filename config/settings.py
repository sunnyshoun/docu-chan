"""Configuration management for Doc Generator"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass
class ChartConfig:
    """Chart Generation 配置"""
    max_iterations: int = 5
    output_format: str = "png"
    render_timeout: int = 30


@dataclass
class Config:
    """
    應用程式主配置
    
    包含：
    - api_key: 全域 API 密鑰
    - api_base_url: 全域 API 端點
    - 路徑配置（prompts, outputs, logs）
    - chart: 圖表生成配置
    
    Agent 模型配置請見 config/agents.py
    """
    api_key: str
    api_base_url: str
    project_root: Path
    prompts_dir: Path
    outputs_dir: Path
    logs_dir: Path
    chart: ChartConfig = field(default_factory=ChartConfig)
    
    @classmethod
    def from_env(cls, env_path: Optional[str] = None) -> "Config":
        """從環境變數載入配置"""
        # 尋找專案根目錄
        project_root = Path(__file__).resolve().parent.parent
        
        # 尋找 .env 檔案
        if env_path is None:
            current = project_root
            while current != current.parent:
                env_file = current / ".env"
                if env_file.exists():
                    env_path = str(env_file)
                    break
                current = current.parent
        
        # 載入 .env
        if env_path and Path(env_path).exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        
        # 驗證必要的環境變數
        api_key = os.getenv("API_KEY")
        if not api_key:
            raise ValueError(
                "API_KEY environment variable is required. "
                "Please set it in .env file or environment."
            )
        
        api_base_url = os.getenv(
            "API_BASE_URL",
            "https://api-gateway.netdb.csie.ncku.edu.tw"
        )
        
        return cls(
            api_key=api_key,
            api_base_url=api_base_url,
            project_root=project_root,
            prompts_dir=project_root / "prompts",
            outputs_dir=project_root / "outputs",
            logs_dir=project_root / "logs"
        )
    
    def __repr__(self) -> str:
        return (
            f"Config(\n"
            f"  api_base_url={self.api_base_url}\n"
            f"  project_root={self.project_root}\n"
            f")"
        )


# 全域配置實例
_config: Optional[Config] = None


def get_config(env_path: Optional[str] = None) -> Config:
    """取得配置實例（單例模式）"""
    global _config
    if _config is None or env_path is not None:
        _config = Config.from_env(env_path)
    return _config


def load_config(env_path: Optional[str] = None) -> Config:
    """Alias for get_config"""
    return get_config(env_path)
