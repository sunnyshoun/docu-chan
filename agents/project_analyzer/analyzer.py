"""
Project Analyzer - Phase 1 Agent

TODO: 專案分析功能待實作
"""
from typing import Optional

from agents.base import BaseAgent, AgentResult


class ProjectAnalyzer(BaseAgent):
    """
    專案分析器（待實作）
    
    預計功能：
    - CodeReader: 讀取代碼摘要
    - ImageReader: 描述圖片內容
    - Analyzer: 整合專案分析
    """
    
    def __init__(self, model: Optional[str] = None):
        super().__init__(name="ProjectAnalyzer", model=model)
    
    def execute(self, project_path: str, **kwargs) -> AgentResult:
        """分析專案（待實作）"""
        raise NotImplementedError("Phase 1: ProjectAnalyzer 尚未實作")
