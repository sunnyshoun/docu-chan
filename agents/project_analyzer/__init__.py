"""
Project Analyzer Module (Phase 1) - CoA 架構

使用 Chain of Agents 架構進行專案分析：
- CoAProjectAnalyzer: 主要分析器（Worker + Manager）
- FileAnalyzerWorker: 平行處理各檔案
- ImageWorker: 圖片分析 Worker
- AnalysisManager: 整合所有 Worker 結果

特點：
- 自動處理 .gitignore 排除規則
- Worker 帶 timeout 防止卡住
- Async 平行處理提升速度
- LLM 自主決定是否讀取檔案
"""

# Data models
from .models import FileInfo, FileAnalysisResult, ProjectContext

# Scanner utilities
from .scanner import GitIgnoreParser, FileScanner

# Worker agents
from .file_worker import FileAnalyzerWorker, WORKER_TIMEOUT
from .image_worker import ImageWorker

# Manager agent
from .manager import AnalysisManager

# Main analyzer
from .coa_analyzer import CoAProjectAnalyzer, create_coa_analyzer

# 主要 export（統一使用 CoA 版本）
ProjectAnalyzer = CoAProjectAnalyzer
create_analyzer = create_coa_analyzer

__all__ = [
    # Models
    "FileInfo",
    "FileAnalysisResult",
    "ProjectContext",
    # Scanner
    "GitIgnoreParser",
    "FileScanner",
    # Agents
    "FileAnalyzerWorker",
    "ImageWorker",
    "AnalysisManager",
    "CoAProjectAnalyzer",
    # Factory
    "create_coa_analyzer",
    # Aliases
    "ProjectAnalyzer",
    "create_analyzer",
    # Constants
    "WORKER_TIMEOUT",
]


