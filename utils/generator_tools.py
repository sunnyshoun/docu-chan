"""
Generator Tools - 提供給 Designer 和 Writer 使用的工具函數

讓 Generator 能夠自主讀取檔案、分析結構，補充 Planner 給的指引不足的資訊。
"""
import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .file_utils import read_file, list_files


# ============================================================
# Tool Definitions (用於 function calling)
# ============================================================

GENERATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_source_file",
            "description": "讀取專案中的原始碼檔案。使用此工具來獲取繪製圖表或撰寫文檔所需的具體程式碼資訊。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要讀取的檔案路徑（相對於專案根目錄）"
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "起始行號（可選，從 1 開始）"
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "結束行號（可選）"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_class_info",
            "description": "獲取檔案中指定類別的詳細資訊，包括方法、屬性、繼承關係。用於繪製類別圖或撰寫 API 文檔。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "檔案路徑"
                    },
                    "class_name": {
                        "type": "string",
                        "description": "要查詢的類別名稱（可選，不提供則列出所有類別）"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_function_info",
            "description": "獲取檔案中指定函數的詳細資訊，包括參數、回傳值、docstring。用於撰寫 API 文檔或理解流程。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "檔案路徑"
                    },
                    "function_name": {
                        "type": "string",
                        "description": "要查詢的函數名稱（可選，不提供則列出所有函數）"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_references",
            "description": "在專案中搜尋指定符號（類別、函數、變數）的使用位置。用於理解元件之間的關係。",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol_name": {
                        "type": "string",
                        "description": "要搜尋的符號名稱"
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "檔案過濾模式（如 '*.py'）"
                    }
                },
                "required": ["symbol_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_module_overview",
            "description": "獲取模組（目錄）的整體概覽，列出所有檔案及其主要類別/函數。用於理解模組結構。",
            "parameters": {
                "type": "object",
                "properties": {
                    "module_path": {
                        "type": "string",
                        "description": "模組目錄路徑"
                    }
                },
                "required": ["module_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_call_flow",
            "description": "分析從指定函數開始的呼叫流程。用於繪製序列圖或流程圖。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "檔案路徑"
                    },
                    "function_name": {
                        "type": "string",
                        "description": "起始函數名稱"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "最大追蹤深度（預設 3）"
                    }
                },
                "required": ["file_path", "function_name"]
            }
        }
    }
]


# ============================================================
# Tool 實作函數
# ============================================================

# 全域專案路徑（在執行時設定）
_project_path: Optional[Path] = None


def set_project_path(path: str):
    """設定專案根目錄路徑"""
    global _project_path
    _project_path = Path(path).resolve()


def get_project_path() -> Path:
    """取得專案根目錄路徑"""
    if _project_path is None:
        raise ValueError("Project path not set. Call set_project_path() first.")
    return _project_path


def _resolve_path(file_path: str) -> Path:
    """解析檔案路徑（支援相對路徑和絕對路徑）"""
    path = Path(file_path)
    if path.is_absolute():
        return path
    return get_project_path() / file_path


def read_source_file(
    file_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None
) -> Dict[str, Any]:
    """
    讀取原始碼檔案
    
    Args:
        file_path: 檔案路徑
        start_line: 起始行號（從 1 開始）
        end_line: 結束行號
        
    Returns:
        dict: 包含 success, content, line_count, language
    """
    try:
        full_path = _resolve_path(file_path)
        
        if not full_path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        content = read_file(full_path)
        lines = content.split('\n')
        total_lines = len(lines)
        
        # 處理行號範圍
        if start_line is not None or end_line is not None:
            start = (start_line or 1) - 1
            end = end_line or total_lines
            lines = lines[start:end]
            content = '\n'.join(lines)
        
        # 偵測語言
        ext = full_path.suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.md': 'markdown',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
        }
        language = language_map.get(ext, 'text')
        
        return {
            "success": True,
            "content": content,
            "line_count": len(lines),
            "total_lines": total_lines,
            "language": language,
            "file_path": str(full_path)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_class_info(
    file_path: str,
    class_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    獲取類別資訊
    
    Args:
        file_path: 檔案路徑
        class_name: 類別名稱（可選）
        
    Returns:
        dict: 類別資訊
    """
    try:
        full_path = _resolve_path(file_path)
        
        if not full_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        if full_path.suffix != '.py':
            return {"success": False, "error": "Only Python files are supported"}
        
        content = read_file(full_path)
        tree = ast.parse(content)
        
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if class_name and node.name != class_name:
                    continue
                
                class_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "docstring": ast.get_docstring(node),
                    "bases": [_get_name(base) for base in node.bases],
                    "methods": [],
                    "attributes": []
                }
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            "name": item.name,
                            "line": item.lineno,
                            "args": [arg.arg for arg in item.args.args if arg.arg != 'self'],
                            "docstring": ast.get_docstring(item),
                            "decorators": [_get_name(d) for d in item.decorator_list]
                        }
                        class_info["methods"].append(method_info)
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                class_info["attributes"].append({
                                    "name": target.id,
                                    "line": item.lineno
                                })
                
                classes.append(class_info)
        
        return {
            "success": True,
            "classes": classes,
            "file_path": str(full_path)
        }
        
    except SyntaxError as e:
        return {"success": False, "error": f"Syntax error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_function_info(
    file_path: str,
    function_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    獲取函數資訊
    
    Args:
        file_path: 檔案路徑
        function_name: 函數名稱（可選）
        
    Returns:
        dict: 函數資訊
    """
    try:
        full_path = _resolve_path(file_path)
        
        if not full_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        if full_path.suffix != '.py':
            return {"success": False, "error": "Only Python files are supported"}
        
        content = read_file(full_path)
        tree = ast.parse(content)
        
        functions = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                if function_name and node.name != function_name:
                    continue
                
                # 解析參數
                args_info = []
                for arg in node.args.args:
                    arg_info = {"name": arg.arg}
                    if arg.annotation:
                        arg_info["type"] = _get_annotation(arg.annotation)
                    args_info.append(arg_info)
                
                # 解析回傳值
                returns = None
                if node.returns:
                    returns = _get_annotation(node.returns)
                
                func_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "docstring": ast.get_docstring(node),
                    "args": args_info,
                    "returns": returns,
                    "decorators": [_get_name(d) for d in node.decorator_list],
                    "is_async": isinstance(node, ast.AsyncFunctionDef)
                }
                functions.append(func_info)
        
        return {
            "success": True,
            "functions": functions,
            "file_path": str(full_path)
        }
        
    except SyntaxError as e:
        return {"success": False, "error": f"Syntax error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def find_references(
    symbol_name: str,
    file_pattern: str = "*.py"
) -> Dict[str, Any]:
    """
    搜尋符號的使用位置
    
    Args:
        symbol_name: 符號名稱
        file_pattern: 檔案過濾模式
        
    Returns:
        dict: 搜尋結果
    """
    try:
        project_path = get_project_path()
        references = []
        
        # 列出所有匹配的檔案
        files = list_files(project_path, pattern=file_pattern, recursive=True)
        
        for file_path in files:
            try:
                content = read_file(file_path)
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    if symbol_name in line:
                        references.append({
                            "file": str(file_path.relative_to(project_path)),
                            "line": i,
                            "content": line.strip()
                        })
            except Exception:
                continue
        
        return {
            "success": True,
            "symbol": symbol_name,
            "references": references[:50],  # 限制結果數量
            "total_count": len(references)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_module_overview(module_path: str) -> Dict[str, Any]:
    """
    獲取模組概覽
    
    Args:
        module_path: 模組目錄路徑
        
    Returns:
        dict: 模組概覽
    """
    try:
        full_path = _resolve_path(module_path)
        
        if not full_path.exists():
            return {"success": False, "error": f"Path not found: {module_path}"}
        
        if not full_path.is_dir():
            return {"success": False, "error": f"Not a directory: {module_path}"}
        
        files_info = []
        
        for py_file in full_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            file_info = {
                "file": py_file.name,
                "classes": [],
                "functions": []
            }
            
            try:
                content = read_file(py_file)
                tree = ast.parse(content)
                
                for node in ast.iter_child_nodes(tree):
                    if isinstance(node, ast.ClassDef):
                        file_info["classes"].append(node.name)
                    elif isinstance(node, ast.FunctionDef):
                        if not node.name.startswith("_"):
                            file_info["functions"].append(node.name)
                
            except Exception:
                file_info["error"] = "Parse error"
            
            files_info.append(file_info)
        
        # 子目錄
        subdirs = [d.name for d in full_path.iterdir() 
                   if d.is_dir() and not d.name.startswith((".", "_"))]
        
        return {
            "success": True,
            "module_path": str(full_path),
            "files": files_info,
            "subdirectories": subdirs
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def analyze_call_flow(
    file_path: str,
    function_name: str,
    max_depth: int = 3
) -> Dict[str, Any]:
    """
    分析呼叫流程
    
    Args:
        file_path: 檔案路徑
        function_name: 函數名稱
        max_depth: 最大深度
        
    Returns:
        dict: 呼叫流程資訊
    """
    try:
        full_path = _resolve_path(file_path)
        
        if not full_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        content = read_file(full_path)
        tree = ast.parse(content)
        
        # 找到目標函數
        target_func = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == function_name:
                    target_func = node
                    break
        
        if not target_func:
            return {"success": False, "error": f"Function not found: {function_name}"}
        
        # 分析呼叫
        calls = _extract_calls(target_func, max_depth)
        
        return {
            "success": True,
            "function": function_name,
            "file": str(full_path),
            "calls": calls
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def _extract_calls(node: ast.AST, depth: int) -> List[Dict[str, Any]]:
    """遞迴提取函數呼叫"""
    if depth <= 0:
        return []
    
    calls = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            call_info = {
                "name": _get_call_name(child),
                "line": getattr(child, 'lineno', 0),
                "args_count": len(child.args)
            }
            calls.append(call_info)
    
    return calls


def _get_call_name(node: ast.Call) -> str:
    """取得呼叫名稱"""
    if isinstance(node.func, ast.Name):
        return node.func.id
    elif isinstance(node.func, ast.Attribute):
        if isinstance(node.func.value, ast.Name):
            return f"{node.func.value.id}.{node.func.attr}"
        return node.func.attr
    return "unknown"


def _get_name(node: ast.AST) -> str:
    """取得 AST 節點名稱"""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return f"{_get_name(node.value)}.{node.attr}"
    elif isinstance(node, ast.Call):
        return _get_name(node.func)
    return str(node)


def _get_annotation(node: ast.AST) -> str:
    """取得型別註解字串"""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Constant):
        return str(node.value)
    elif isinstance(node, ast.Subscript):
        base = _get_annotation(node.value)
        if isinstance(node.slice, ast.Tuple):
            args = ", ".join(_get_annotation(e) for e in node.slice.elts)
        else:
            args = _get_annotation(node.slice)
        return f"{base}[{args}]"
    elif isinstance(node, ast.Attribute):
        return f"{_get_annotation(node.value)}.{node.attr}"
    return "Any"


# ============================================================
# Tool 執行器
# ============================================================

TOOL_FUNCTIONS = {
    "read_source_file": read_source_file,
    "get_class_info": get_class_info,
    "get_function_info": get_function_info,
    "find_references": find_references,
    "get_module_overview": get_module_overview,
    "analyze_call_flow": analyze_call_flow,
}


def execute_generator_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    執行 Generator 工具
    
    Args:
        tool_name: 工具名稱
        arguments: 工具參數
        
    Returns:
        dict: 執行結果
    """
    if tool_name not in TOOL_FUNCTIONS:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }
    
    try:
        return TOOL_FUNCTIONS[tool_name](**arguments)
    except TypeError as e:
        return {
            "success": False,
            "error": f"Invalid arguments: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
