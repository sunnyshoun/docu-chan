"""
Doc Planner - Phase 2 Agent

TODO: 文檔規劃功能待實作
"""
from typing import Dict, Any, Optional

from agents.base import BaseAgent, AgentResult


class DocPlanner(BaseAgent):
    """
    文檔規劃器（待實作）
    
    預計功能：
    - 基於專案分析規劃文檔結構
    - 決定需要的圖表類型
    """
    
    def __init__(self, model: Optional[str] = None):
        super().__init__(name="DocPlanner", model=model)
    
    def execute(self, project_analysis: Dict[str, Any], **kwargs) -> AgentResult:
        """規劃文檔結構（待實作）"""
        raise NotImplementedError("Phase 2: DocPlanner 尚未實作")
