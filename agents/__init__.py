"""
Agents module for Doc Generator

三階段架構：
- Phase 1: project_analyzer - 專案分析
- Phase 2: doc_planner - 規劃（DocPlanner）
- Phase 3: doc_generator - 內容生成（DocWriter + ChartLoop）
"""

from .base import BaseAgent

# Phase 1: 專案分析
from .project_analyzer import ProjectAnalyzer, CoAProjectAnalyzer, create_coa_analyzer

# Phase 2: 規劃
from .doc_planner import (
    DocPlanner, PlannerOutput, DocTodo, ChartTodo
)

# Phase 3: 內容生成
from .doc_generator import ChartLoop, DiagramDesigner, MermaidCoder, CodeExecutor, DocWriter

__all__ = [
    # Base
    "BaseAgent",
    # Phase 1: 專案分析
    "ProjectAnalyzer",
    "CoAProjectAnalyzer",
    "create_coa_analyzer",
    # Phase 2: 規劃
    "DocPlanner", "PlannerOutput", "DocTodo", "ChartTodo",
    # Phase 3: 內容生成
    "DocWriter", "ChartLoop",
    "DiagramDesigner", "MermaidCoder", "CodeExecutor",
]
