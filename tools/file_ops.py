"""
File Operations Tools - 檔案讀寫相關的 tools

這些 tools 提供給 AI Agent 使用，讓它能夠讀取專案檔案並回報分析結果。
支援：
- 讀取指定行數範圍
- 檔案內搜尋
- 專案內搜尋
- 自動處理非文字/圖片檔案
"""
import re
import json
import chardet
from pathlib import Path
from typing import Optional, List, Dict

from .registry import tool


# ==================== Constants ====================

# 文字檔案副檔名
TEXT_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.vue', '.svelte',
    '.java', '.kt', '.scala', '.go', '.rs', '.c', '.cpp', '.h', '.hpp',
    '.cs', '.rb', '.php', '.swift', '.m', '.mm',
    '.html', '.css', '.scss', '.sass', '.less',
    '.json', '.yaml', '.yml', '.toml', '.xml', '.ini', '.cfg',
    '.md', '.txt', '.rst', '.tex',
    '.sql', '.graphql', '.prisma',
    '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
    '.env', '.gitignore', '.dockerignore', '.editorconfig',
    '.lock',  # 讓 LLM 自己決定是否要讀
}

# 圖片檔案副檔名
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp', '.ico'}

# 二進制檔案副檔名
BINARY_EXTENSIONS = {
    '.exe', '.dll', '.so', '.dylib', '.bin',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.mp3', '.mp4', '.wav', '.avi', '.mov', '.mkv', '.flv', '.wmv',
    '.mid', '.midi', '.ogg', '.flac', '.aac', '.wma',
    '.whl', '.pyc', '.pyo', '.class', '.o', '.obj',
    '.ttf', '.otf', '.woff', '.woff2', '.eot',
    '.db', '.sqlite', '.sqlite3',
}


# ==================== Global State ====================

_project_root: Optional[Path] = None
_reports: Dict[str, Dict] = {}


def set_project_root(path: str) -> None:
    """設定專案根目錄"""
    global _project_root
    _project_root = Path(path).resolve()


def get_project_root() -> Optional[Path]:
    """取得專案根目錄"""
    return _project_root


def get_reports() -> Dict[str, Dict]:
    """取得所有分析報告"""
    return _reports.copy()


def clear_reports() -> None:
    """清除分析報告"""
    global _reports
    _reports = {}


# ==================== Helper Functions ====================

def _resolve_path(file_path: str) -> Path:
    """解析檔案路徑（相對或絕對）"""
    path = Path(file_path)
    if not path.is_absolute() and _project_root:
        path = _project_root / file_path
    return path


def _get_file_type(path: Path) -> str:
    """判斷檔案類型: 'text', 'image', 'binary'"""
    ext = path.suffix.lower()
    
    if ext in IMAGE_EXTENSIONS:
        return 'image'
    if ext in BINARY_EXTENSIONS:
        return 'binary'
    if ext in TEXT_EXTENSIONS:
        return 'text'
    
    # 未知副檔名，嘗試偵測
    try:
        sample = path.read_bytes()[:8192]
        # 檢查是否有 null bytes（二進制特徵）
        if b'\x00' in sample:
            return 'binary'
        # 嘗試解碼
        sample.decode('utf-8')
        return 'text'
    except:
        return 'binary'


def _read_text_file(path: Path) -> str:
    """讀取文字檔案，處理編碼"""
    raw_data = path.read_bytes()
    
    # 嘗試 UTF-8
    try:
        return raw_data.decode('utf-8')
    except UnicodeDecodeError:
        pass
    
    # 偵測編碼
    result = chardet.detect(raw_data)
    encoding = result.get('encoding')
    confidence = result.get('confidence', 0)
    
    if encoding and confidence > 0.7:
        try:
            return raw_data.decode(encoding)
        except UnicodeDecodeError:
            pass
    
    # 強制解碼（忽略錯誤）
    return raw_data.decode('utf-8', errors='replace')


# ==================== Tools ====================

@tool
def read_file(
    file_path: str,
    start_line: int = 1,
    end_line: int = -1,
    max_line_length: int = 500
) -> str:
    """
    Read the content of a file with optional line range.
    
    Args:
        file_path: Path of the file to read (relative to project root or absolute).
        start_line: Starting line number (1-based, inclusive). Default is 1.
        end_line: Ending line number (1-based, inclusive). Set to -1 to read until end. Default is -1.
        max_line_length: Maximum characters per line before truncation. Default is 500.
    
    Returns:
        The file content as string with line numbers, or error/info message.
    
    Examples:
        - read_file("main.py") -> Read entire file
        - read_file("main.py", 10, 50) -> Read lines 10-50
        - read_file("main.py", 100, -1) -> Read from line 100 to end
    """
    try:
        path = _resolve_path(file_path)
        
        if not path.exists():
            return f"error: file not found: {file_path}"
        
        if not path.is_file():
            return f"error: not a file: {file_path}"
        
        # 檢查檔案類型
        file_type = _get_file_type(path)
        
        if file_type == 'image':
            return (
                f"This is an image file ({path.suffix}). "
                f"Image files are automatically analyzed by the image reader agent."
            )
        
        if file_type == 'binary':
            return (
                f"This file is not a text file ({path.suffix}). "
                f"Cannot open binary files. "
                f"Please determine the file type based on its extension and project structure."
            )
        
        # 讀取文字檔案
        text = _read_text_file(path)
        
        if not text.strip():
            return "(empty file)"
        
        lines = text.splitlines()
        total_lines = len(lines)
        
        # 處理行數範圍
        start_idx = max(0, start_line - 1)  # 轉為 0-based
        end_idx = total_lines if end_line == -1 else min(end_line, total_lines)
        
        if start_idx >= total_lines:
            return f"error: start_line {start_line} exceeds file length ({total_lines} lines)"
        
        selected_lines = lines[start_idx:end_idx]
        
        # 格式化輸出（帶行號）
        result_lines = []
        for i, line in enumerate(selected_lines, start=start_idx + 1):
            if len(line) > max_line_length:
                line = f"{line[:max_line_length]}... (+{len(line) - max_line_length} chars)"
            result_lines.append(f"{i:4d} | {line}")
        
        # 添加範圍資訊
        header = f"[{path.name}] Lines {start_idx + 1}-{end_idx} of {total_lines}\n"
        header += "-" * 60 + "\n"
        
        return header + '\n'.join(result_lines)
        
    except Exception as e:
        return f"error: {str(e)}"


@tool
def search_in_file(
    file_path: str,
    pattern: str,
    context_lines: int = 3,
    max_matches: int = 10,
    case_sensitive: bool = False
) -> str:
    """
    Search for a pattern in a file and return matching lines with context.
    
    Args:
        file_path: Path of the file to search (relative to project root or absolute).
        pattern: Text or regex pattern to search for.
        context_lines: Number of context lines before and after each match. Default is 3.
        max_matches: Maximum number of matches to return. Default is 10.
        case_sensitive: Whether the search is case-sensitive. Default is False.
    
    Returns:
        Matching lines with context and line numbers, or message if no matches.
    
    Examples:
        - search_in_file("main.py", "def main") -> Find function definitions
        - search_in_file("config.json", "api_key", context_lines=1) -> Find config entries
    """
    try:
        path = _resolve_path(file_path)
        
        if not path.exists():
            return f"error: file not found: {file_path}"
        
        # 檢查檔案類型
        file_type = _get_file_type(path)
        if file_type != 'text':
            return f"error: cannot search in {file_type} file: {file_path}"
        
        text = _read_text_file(path)
        lines = text.splitlines()
        
        # 編譯正則表達式
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error:
            # 如果不是有效的正則，當作普通字串搜尋
            regex = re.compile(re.escape(pattern), flags)
        
        # 搜尋匹配
        matches = []
        for i, line in enumerate(lines):
            if regex.search(line):
                matches.append(i)
                if len(matches) >= max_matches:
                    break
        
        if not matches:
            return f"No matches found for '{pattern}' in {file_path}"
        
        # 組合結果（帶上下文）
        results = []
        shown_lines = set()
        
        for match_idx in matches:
            start = max(0, match_idx - context_lines)
            end = min(len(lines), match_idx + context_lines + 1)
            
            # 避免重複顯示
            if match_idx in shown_lines:
                continue
            
            result_lines = []
            for i in range(start, end):
                if i in shown_lines:
                    continue
                shown_lines.add(i)
                
                prefix = ">>> " if i == match_idx else "    "
                result_lines.append(f"{prefix}{i + 1:4d} | {lines[i]}")
            
            if result_lines:
                results.append('\n'.join(result_lines))
        
        header = f"[{path.name}] Found {len(matches)} match(es) for '{pattern}'\n"
        header += "-" * 60 + "\n"
        
        return header + "\n...\n".join(results)
        
    except Exception as e:
        return f"error: {str(e)}"


@tool
def search_in_project(
    pattern: str,
    file_pattern: str = "*",
    max_files: int = 20,
    max_matches_per_file: int = 5,
    case_sensitive: bool = False
) -> str:
    """
    Search for a pattern across all files in the project.
    
    Args:
        pattern: Text or regex pattern to search for.
        file_pattern: Glob pattern to filter files (e.g., "*.py", "*.js"). Default is "*" (all files).
        max_files: Maximum number of files to search. Default is 20.
        max_matches_per_file: Maximum matches to show per file. Default is 5.
        case_sensitive: Whether the search is case-sensitive. Default is False.
    
    Returns:
        Summary of matches across files with file paths and line numbers.
    
    Examples:
        - search_in_project("TODO") -> Find all TODOs
        - search_in_project("import.*torch", "*.py") -> Find PyTorch imports
        - search_in_project("api_key", "*.json") -> Find API keys in configs
    """
    if not _project_root:
        return "error: project root not set"
    
    try:
        # 編譯正則表達式
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error:
            regex = re.compile(re.escape(pattern), flags)
        
        # 收集檔案
        if file_pattern == "*":
            files = [f for f in _project_root.rglob("*") if f.is_file()]
        else:
            files = list(_project_root.rglob(file_pattern))
        
        # 過濾文字檔案
        text_files = [f for f in files if _get_file_type(f) == 'text'][:max_files]
        
        results = []
        total_matches = 0
        
        for file_path in text_files:
            try:
                text = _read_text_file(file_path)
                lines = text.splitlines()
                
                matches = []
                for i, line in enumerate(lines):
                    if regex.search(line):
                        matches.append((i + 1, line.strip()[:100]))
                        if len(matches) >= max_matches_per_file:
                            break
                
                if matches:
                    rel_path = file_path.relative_to(_project_root)
                    file_result = f"\n📄 {rel_path} ({len(matches)} match(es)):\n"
                    for line_num, content in matches:
                        file_result += f"   L{line_num}: {content}\n"
                    results.append(file_result)
                    total_matches += len(matches)
                    
            except Exception:
                continue
        
        if not results:
            return f"No matches found for '{pattern}' in project"
        
        header = f"🔍 Search results for '{pattern}'\n"
        header += f"   Found {total_matches} match(es) in {len(results)} file(s)\n"
        header += "=" * 60
        
        return header + ''.join(results)
        
    except Exception as e:
        return f"error: {str(e)}"


@tool
def list_directory(directory: str = ".", show_hidden: bool = False) -> str:
    """
    List contents of a directory.
    
    Args:
        directory: Directory path to list (relative to project root or absolute). Default is project root.
        show_hidden: Whether to show hidden files (starting with dot). Default is False.
    
    Returns:
        List of files and directories with basic info.
    """
    try:
        path = _resolve_path(directory)
        
        if not path.exists():
            return f"error: directory not found: {directory}"
        
        if not path.is_dir():
            return f"error: not a directory: {directory}"
        
        items = []
        for item in sorted(path.iterdir()):
            if not show_hidden and item.name.startswith('.'):
                continue
            
            if item.is_dir():
                items.append(f"📁 {item.name}/")
            else:
                size = item.stat().st_size
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size // 1024}KB"
                else:
                    size_str = f"{size // (1024 * 1024)}MB"
                items.append(f"📄 {item.name} ({size_str})")
        
        if not items:
            return f"(empty directory: {directory})"
        
        header = f"📂 {directory}\n" + "-" * 40 + "\n"
        return header + '\n'.join(items)
        
    except Exception as e:
        return f"error: {str(e)}"


@tool
def report_summary(path: str, is_important: bool, summary: str) -> str:
    """
    Report the analysis summary of a file. Call this after analyzing each file.
    
    Args:
        path: File path that was analyzed.
        is_important: Whether this file is important for project documentation (True for core logic, entry points, APIs; False for configs, generated files, tests).
        summary: Concise summary of the file's purpose, main logic, key functions/classes, and relationships with other files.
    
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
def report_batch_summary(summaries: str) -> str:
    """
    Report analysis summaries for multiple files at once. Use JSON format.
    
    Args:
        summaries: JSON string containing array of file summaries. Each item should have: path, is_important, summary.
    
    Returns:
        Confirmation message with count of reported files.
    
    Example:
        summaries = '[{"path": "main.py", "is_important": true, "summary": "Entry point"}, ...]'
    """
    global _reports
    
    try:
        data = json.loads(summaries)
        if not isinstance(data, list):
            return "error: summaries must be a JSON array"
        
        count = 0
        for item in data:
            if isinstance(item, dict) and 'path' in item:
                _reports[item['path']] = {
                    "is_important": item.get('is_important', False),
                    "summary": item.get('summary', '')
                }
                count += 1
        
        return f"Reported {count} file(s) successfully"
        
    except json.JSONDecodeError as e:
        return f"error: invalid JSON - {e}"
