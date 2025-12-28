"""Configuration management for Doc Generator"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass
class ModelConfig:
    """模型配置（預設值定義於此，不從 .env 讀取）"""
    # Phase 1
    code_reader: str = "gpt-oss:20b"
    image_reader: str = "gemma3:4b"
    project_analyzer: str = "gpt-oss:120b"
    
    # Phase 2
    doc_planner: str = "gpt-oss:120b"
    chart_planner: str = "gpt-oss:120b"  # Chart Planner
    planner_worker: str = "gpt-oss:20b"  # CoA Worker
    
    # Phase 3 - Text
    tech_writer: str = "gpt-oss:20b"
    doc_reviewer: str = "gpt-oss:20b"
    
    # Phase 3 - Chart
    diagram_designer: str = "gpt-oss:20b"
    mermaid_coder: str = "gpt-oss:20b"
    visual_inspector: str = "gemma3:4b"
    
    # Phase 4
    publisher: str = "gemma3:4b"


@dataclass
class ChartConfig:
    """Chart Generation 配置"""
    max_iterations: int = 5
    output_format: str = "png"
    render_timeout: int = 30
    log_dir: Optional[Path] = None      # 日誌/中間產物 (logs/phase3/)
    output_dir: Optional[Path] = None   # 最終輸出 (outputs/)


@dataclass
class Config:
    """應用程式主配置"""
    api_key: str
    api_base_url: str
    project_root: Path
    prompts_dir: Path
    outputs_dir: Path
    logs_dir: Path
    models: ModelConfig = field(default_factory=ModelConfig)
    chart: ChartConfig = field(default_factory=ChartConfig)
    
    @classmethod
    def from_env(cls, env_path: Optional[str] = None) -> "Config":
        """
        從環境變數載入配置
        
        Args:
            env_path: .env 檔案路徑
            
        Returns:
            Config: 配置實例
        """
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
        
        # 路徑配置
        logs_dir = project_root / "logs"
        outputs_dir = project_root / "outputs"
        
        # Chart 配置
        chart = ChartConfig(
            log_dir=logs_dir / "phase3" / "charts",
            output_dir=outputs_dir / "final" / "diagrams"
        )
        
        return cls(
            api_key=api_key,
            api_base_url=api_base_url,
            project_root=project_root,
            prompts_dir=project_root / "prompts",
            outputs_dir=outputs_dir,
            logs_dir=logs_dir,
            chart=chart
        )
    
    def __repr__(self) -> str:
        return (
            f"Config(\n"
            f"  api_base_url={self.api_base_url}\n"
            f"  project_root={self.project_root}\n"
            f"  models=ModelConfig(...)\n"
            f")"
        )


# 全域配置實例
_config: Optional[Config] = None


def get_config(env_path: Optional[str] = None) -> Config:
    """
    取得配置實例（單例模式）
    
    Args:
        env_path: .env 檔案路徑
        
    Returns:
        Config: 配置實例
    """
    global _config
    
    if _config is None or env_path is not None:
        _config = Config.from_env(env_path)
    
    return _config


def load_config(env_path: Optional[str] = None) -> Config:
    """Alias for get_config"""
    return get_config(env_path)
