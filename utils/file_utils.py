"""
File utility functions for Doc Generator

基本檔案操作工具函數。
"""
from pathlib import Path
from typing import List, Optional, Union


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    確保目錄存在，若不存在則建立
    
    Args:
        path: 目錄路徑
        
    Returns:
        Path: 目錄路徑物件
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_file(path: Union[str, Path], encoding: str = "utf-8") -> str:
    """
    讀取檔案內容
    
    Args:
        path: 檔案路徑
        encoding: 編碼
        
    Returns:
        str: 檔案內容
    """
    with open(path, "r", encoding=encoding) as f:
        return f.read()


def write_file(
    path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    ensure_parent: bool = True
) -> Path:
    """
    寫入檔案內容
    
    Args:
        path: 檔案路徑
        content: 寫入內容
        encoding: 編碼
        ensure_parent: 是否確保父目錄存在
        
    Returns:
        Path: 檔案路徑物件
    """
    path = Path(path)
    
    if ensure_parent:
        ensure_dir(path.parent)
    
    with open(path, "w", encoding=encoding) as f:
        f.write(content)
    
    return path


def list_files(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False
) -> List[Path]:
    """
    列出目錄中的檔案
    
    Args:
        directory: 目錄路徑
        pattern: 檔案模式（如 "*.py"）
        recursive: 是否遞迴搜尋
        
    Returns:
        List[Path]: 檔案路徑列表
    """
    directory = Path(directory)
    
    if not directory.exists():
        return []
    
    if recursive:
        return list(directory.rglob(pattern))
    else:
        return list(directory.glob(pattern))


def get_file_extension(path: Union[str, Path]) -> str:
    """
    取得檔案副檔名
    
    Args:
        path: 檔案路徑
        
    Returns:
        str: 副檔名（不含點）
    """
    return Path(path).suffix.lstrip(".")


def get_relative_path(path: Union[str, Path], base: Union[str, Path]) -> Path:
    """
    取得相對路徑
    
    Args:
        path: 檔案路徑
        base: 基礎路徑
        
    Returns:
        Path: 相對路徑
    """
    return Path(path).relative_to(Path(base))
