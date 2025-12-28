"""
Project Analyzer - Phase 1 Agent

TODO: 專案分析功能待實現
"""
from typing import Optional, Dict, Any

from config import config
from agents.base import BaseAgent


class ProjectAnalyzer(BaseAgent):
    """
    專案分析師（待實作）
    
    預計功能：
    - CodeReader: 讀取代碼結構
    - ImageReader: 描述圖片內容
    - Analyzer: 分析專案特性
    """
    
    def __init__(self, model: Optional[str] = None):
        super().__init__(
            name="ProjectAnalyzer",
            model=model or config.models.project_analyzer
        )
    
    def execute(self, project_path: str, **kwargs) -> Dict[str, Any]:
        """分析專案（未實現）"""
        raise NotImplementedError("Phase 1: ProjectAnalyzer 尚未實現")

