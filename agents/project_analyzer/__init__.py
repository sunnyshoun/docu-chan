"""
Project Analyzer Module (Phase 1)

負責專案理解：
- CodeReader: 讀取和摘要代碼檔案
- ImageReader: 讀取和描述圖片
- Analyzer: 整合分析專案結構
"""

from .analyzer import ProjectAnalyzer

__all__ = ["ProjectAnalyzer"]
