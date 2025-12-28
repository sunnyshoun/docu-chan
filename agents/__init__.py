"""
Agents module for Doc Generator

包含四個主要模組：
- project_analyzer: 專案分析（Phase 1）
- doc_planner: 文檔規劃（Phase 2）
- doc_generator: 內容生成（Phase 3）
- packer: 打包發布（Phase 4）
"""

from .base import BaseAgent

# Project Analyzer
from .project_analyzer import ProjectAnalyzer

# Doc Planner
from .doc_planner import DocPlanner

# Doc Generator
from .doc_generator import DocWriter, ChartLoop

# Packer
from .packer import Packer

__all__ = [
    # Base
    "BaseAgent",
    # Phase 1: Understanding
    "ProjectAnalyzer",
    # Phase 2: Planning
    "DocPlanner",
    # Phase 3: Generation
    "DocWriter",
    "ChartLoop",
    # Phase 4: Packaging
    "Packer",
]

