"""
Project Analyzer - Data Classes

定義專案分析相關的資料結構
"""
from typing import List, Optional, Set
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class FileInfo:
    """檔案資訊"""
    path: str  # 相對路徑
    abs_path: Path  # 絕對路徑
    is_text: bool
    extension: str
    size: int = 0


@dataclass
class FileAnalysisResult:
    """單一檔案分析結果"""
    file_path: str
    is_important: bool
    summary: str
    dependencies: List[str] = field(default_factory=list)
    key_elements: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ProjectContext:
    """專案上下文"""
    root_dir: Path
    files: List[FileInfo]
    file_tree_str: str
    gitignore_patterns: Set[str]
    entry_points: List[str] = field(default_factory=list)
    project_type: Optional[str] = None
