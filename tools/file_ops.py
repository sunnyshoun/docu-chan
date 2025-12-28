"""
File Operations Tools - 檔案讀寫相關的 tools

這些 tools 提供給 AI Agent 使用，讓它能夠讀取專案檔案並回報分析結果。
"""
import chardet
from pathlib import Path
from typing import Optional

from .registry import tool


# 全域狀態：用於儲存分析結果
_project_root: Optional[Path] = None
_reports: dict[str, dict] = {}


def set_project_root(path: str) -> None:
    """設定專案根目錄"""
    global _project_root
    _project_root = Path(path).resolve()


def get_project_root() -> Optional[Path]:
    """取得專案根目錄"""
    return _project_root


def get_reports() -> dict[str, dict]:
    """取得所有分析報告"""
    return _reports.copy()


def clear_reports() -> None:
    """清除分析報告"""
    global _reports
    _reports = {}


@tool
def read_file(file_path: str, n: int = -1) -> str:
    """
    Read the content of a file.
    
    Args:
        file_path: Path of the file to read (relative to project root or absolute).
        n: Number of lines to read. Set to -1 to read entire file, or positive number for first n lines.
    
    Returns:
        The file content as string, or error message if file cannot be read.
    """
    try:
        # 解析路徑
        path = Path(file_path)
        if not path.is_absolute() and _project_root:
            path = _project_root / file_path
        
        if not path.exists():
            return f"error: file not found: {file_path}"
        
        # 讀取檔案
        raw_data = path.read_bytes()
        
        # 嘗試 UTF-8
        try:
            text = raw_data.decode('utf-8')
        except UnicodeDecodeError:
            # 偵測編碼
            result = chardet.detect(raw_data)
            detected_encoding = result.get('encoding')
            confidence = result.get('confidence', 0)
            
            if detected_encoding and confidence > 0.7:
                try:
                    text = raw_data.decode(detected_encoding)
                except UnicodeDecodeError:
                    return f"error: unable to decode file with detected encoding {detected_encoding}"
            else:
                return "error: unable to determine file encoding"
        
        # 處理空檔案
        if not text.strip():
            return "(empty file)"
        
        # 處理行數限制
        lines = text.splitlines()
        if n > 0 and len(lines) > n:
            truncated_lines = lines[:n]
            # 處理過長的行
            result_lines = []
            for line in truncated_lines:
                if len(line) > 200:
                    result_lines.append(f"{line[:200]}... (+{len(line) - 200} chars)")
                else:
                    result_lines.append(line)
            return '\n'.join(result_lines) + f"\n\n... (showing {n}/{len(lines)} lines)"
        
        return text
        
    except Exception as e:
        return f"error: {str(e)}"


@tool
def report_summary(path: str, is_important: bool, summary: str) -> str:
    """
    Report the analysis summary of a file. Call this after analyzing each file.
    
    Args:
        path: File path that was analyzed.
        is_important: Whether this file is important for project documentation (True for core logic, entry points, APIs; False for configs, generated files, tests).
        summary: Concise summary of the file's purpose, main logic, key functions/classes, and relationships with other files. Leave empty for unimportant files.
    
    Returns:
        Confirmation message.
    """
    global _reports
    _reports[path] = {
        "is_important": is_important,
        "summary": summary
    }
    return f"Reported: {path}"


@tool
def get_image_description(image_path: str) -> str:
    """
    Get description of an image file. Use this for diagrams, screenshots, UI mockups, etc.
    
    Args:
        image_path: Path of the image file to analyze.
    
    Returns:
        Description of the image content, or instruction to use vision model.
    """
    # 這個 tool 的實際實作需要 VLM，這裡回傳提示
    # 實際使用時會被 PictureAnalyzer 覆蓋
    return f"[Image analysis required for: {image_path}]"
