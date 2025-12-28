"""
Planner Tools - 提供給 Agent 使用的工具函數

這些工具函數可用於：
1. 讀取檔案內容
2. 分析檔案依賴關係
3. 識別入口點檔案
4. 解析專案結構
"""
import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .file_utils import read_file, list_files


# ============================================================
# Tool Definitions (用於 function calling)
# ============================================================

PLANNER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file_content",
            "description": "讀取指定檔案的完整內容。用於獲取更詳細的程式碼資訊。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要讀取的檔案路徑"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_file_dependencies",
            "description": "分析指定檔案的 import 依賴關係，回傳該檔案依賴的其他模組列表。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要分析的檔案路徑"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_structure",
            "description": "獲取檔案的結構資訊，包括類別、函數、變數等定義。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要分析的檔案路徑"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_entry_points",
            "description": "在專案中尋找可能的入口點檔案（如 main.py, app.py 等）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "專案根目錄路徑"
                    }
                },
                "required": ["project_path"]
            }
        }
    }
]


# ============================================================
# Tool 實作函數
# ============================================================

def read_file_content(file_path: str, max_lines: int = 500) -> Dict[str, Any]:
    """
    讀取檔案內容
    
    Args:
        file_path: 檔案路徑
        max_lines: 最大讀取行數
        
    Returns:
        dict: 包含 content, line_count, truncated
    """
    try:
        content = read_file(file_path)
        lines = content.split('\n')
        truncated = len(lines) > max_lines
        
        if truncated:
            content = '\n'.join(lines[:max_lines])
            content += f"\n\n... (truncated, total {len(lines)} lines)"
        
        return {
            "success": True,
            "content": content,
            "line_count": len(lines),
            "truncated": truncated
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"File not found: {file_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def analyze_file_dependencies(file_path: str) -> Dict[str, Any]:
    """
    分析 Python 檔案的 import 依賴
    
    Args:
        file_path: 檔案路徑
        
    Returns:
        dict: 包含 imports, from_imports, local_imports, external_imports
    """
    try:
        content = read_file(file_path)
        
        # 使用 AST 解析
        tree = ast.parse(content)
        
        imports: List[str] = []
        from_imports: List[Dict[str, Any]] = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.name for alias in node.names]
                from_imports.append({
                    "module": module,
                    "names": names,
                    "level": node.level  # 相對導入層級
                })
        
        # 區分本地和外部導入
        local_imports = []
        external_imports = []
        
        project_root = Path(file_path).parent
        
        for imp in imports:
            if _is_local_import(imp, project_root):
                local_imports.append(imp)
            else:
                external_imports.append(imp)
        
        for from_imp in from_imports:
            if from_imp["level"] > 0 or _is_local_import(from_imp["module"], project_root):
                local_imports.append(from_imp["module"])
            else:
                external_imports.append(from_imp["module"])
        
        return {
            "success": True,
            "imports": imports,
            "from_imports": from_imports,
            "local_imports": list(set(local_imports)),
            "external_imports": list(set(external_imports))
        }
        
    except SyntaxError as e:
        return {
            "success": False,
            "error": f"Syntax error in file: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_file_structure(file_path: str) -> Dict[str, Any]:
    """
    獲取 Python 檔案的結構資訊
    
    Args:
        file_path: 檔案路徑
        
    Returns:
        dict: 包含 classes, functions, variables
    """
    try:
        content = read_file(file_path)
        tree = ast.parse(content)
        
        classes: List[Dict[str, Any]] = []
        functions: List[Dict[str, Any]] = []
        variables: List[str] = []
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                class_vars = []
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append({
                            "name": item.name,
                            "args": [arg.arg for arg in item.args.args],
                            "decorators": [_get_decorator_name(d) for d in item.decorator_list]
                        })
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                class_vars.append(target.id)
                
                classes.append({
                    "name": node.name,
                    "bases": [_get_base_name(base) for base in node.bases],
                    "methods": methods,
                    "class_variables": class_vars,
                    "decorators": [_get_decorator_name(d) for d in node.decorator_list]
                })
                
            elif isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "decorators": [_get_decorator_name(d) for d in node.decorator_list],
                    "is_async": False
                })
                
            elif isinstance(node, ast.AsyncFunctionDef):
                functions.append({
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "decorators": [_get_decorator_name(d) for d in node.decorator_list],
                    "is_async": True
                })
                
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append(target.id)
        
        return {
            "success": True,
            "classes": classes,
            "functions": functions,
            "variables": variables,
            "file_path": file_path
        }
        
    except SyntaxError as e:
        return {
            "success": False,
            "error": f"Syntax error in file: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def find_entry_points(project_path: str) -> Dict[str, Any]:
    """
    尋找專案的入口點檔案
    
    Args:
        project_path: 專案根目錄
        
    Returns:
        dict: 包含 entry_points 列表
    """
    try:
        project_path = Path(project_path)
        entry_points: List[Dict[str, Any]] = []
        
        # 常見入口點檔案名稱
        entry_patterns = [
            "main.py", "app.py", "run.py", "start.py",
            "__main__.py", "cli.py", "server.py", "wsgi.py",
            "asgi.py", "manage.py"
        ]
        
        # 搜尋入口點
        for pattern in entry_patterns:
            files = list_files(project_path, pattern, recursive=True)
            for f in files:
                # 檢查是否有 if __name__ == "__main__"
                has_main_block = _check_main_block(f)
                entry_points.append({
                    "path": str(f.relative_to(project_path)),
                    "full_path": str(f),
                    "name": f.name,
                    "has_main_block": has_main_block,
                    "priority": _get_entry_priority(f.name, has_main_block)
                })
        
        # 按優先級排序
        entry_points.sort(key=lambda x: x["priority"], reverse=True)
        
        return {
            "success": True,
            "entry_points": entry_points,
            "primary_entry": entry_points[0] if entry_points else None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def build_dependency_graph(
    file_summaries: Dict[str, str],
    project_path: str
) -> Dict[str, Any]:
    """
    建立專案的依賴關係圖
    
    Args:
        file_summaries: 檔案路徑 -> 摘要
        project_path: 專案根目錄
        
    Returns:
        dict: 包含 graph, execution_order, clusters
    """
    try:
        project_path = Path(project_path)
        graph: Dict[str, List[str]] = {}
        reverse_graph: Dict[str, List[str]] = {}
        
        # 分析每個檔案的依賴
        for file_path in file_summaries.keys():
            full_path = project_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
            
            if full_path.suffix == ".py" and full_path.exists():
                deps = analyze_file_dependencies(str(full_path))
                
                if deps["success"]:
                    # 將本地導入轉換為實際檔案路徑
                    local_deps = []
                    for imp in deps.get("local_imports", []):
                        resolved = _resolve_import_to_file(imp, full_path.parent, project_path)
                        if resolved:
                            local_deps.append(str(resolved.relative_to(project_path)))
                    
                    graph[file_path] = local_deps
                    
                    # 建立反向圖
                    for dep in local_deps:
                        if dep not in reverse_graph:
                            reverse_graph[dep] = []
                        reverse_graph[dep].append(file_path)
        
        # 拓撲排序計算執行順序
        execution_order = _topological_sort(graph)
        
        # 識別模組群組
        clusters = _identify_clusters(graph, project_path)
        
        return {
            "success": True,
            "graph": graph,
            "reverse_graph": reverse_graph,
            "execution_order": execution_order,
            "clusters": clusters
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# 輔助函數
# ============================================================

def _is_local_import(module: str, project_root: Path) -> bool:
    """判斷是否為本地導入"""
    if not module:
        return True  # 相對導入
    
    parts = module.split('.')
    potential_path = project_root / '/'.join(parts)
    
    # 檢查是否為目錄或 .py 檔案
    if potential_path.is_dir() or (potential_path.parent / f"{parts[-1]}.py").exists():
        return True
    
    return False


def _get_decorator_name(node: ast.expr) -> str:
    """取得 decorator 名稱"""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return f"{_get_decorator_name(node.value)}.{node.attr}"
    elif isinstance(node, ast.Call):
        return _get_decorator_name(node.func)
    return ""


def _get_base_name(node: ast.expr) -> str:
    """取得基類名稱"""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return f"{_get_base_name(node.value)}.{node.attr}"
    return ""


def _check_main_block(file_path: Path) -> bool:
    """檢查檔案是否有 __main__ 區塊"""
    try:
        content = read_file(str(file_path))
        return 'if __name__' in content and '__main__' in content
    except:
        return False


def _get_entry_priority(filename: str, has_main_block: bool) -> int:
    """計算入口點優先級"""
    priority = 0
    
    if has_main_block:
        priority += 10
    
    priority_map = {
        "main.py": 20,
        "app.py": 15,
        "run.py": 12,
        "__main__.py": 18,
        "cli.py": 8,
        "server.py": 10,
        "manage.py": 5
    }
    
    priority += priority_map.get(filename, 0)
    
    return priority


def _resolve_import_to_file(
    import_name: str,
    current_dir: Path,
    project_root: Path
) -> Optional[Path]:
    """將 import 名稱解析為實際檔案路徑"""
    if not import_name:
        return None
    
    parts = import_name.split('.')
    
    # 嘗試從專案根目錄解析
    potential = project_root / '/'.join(parts)
    if potential.with_suffix('.py').exists():
        return potential.with_suffix('.py')
    if (potential / '__init__.py').exists():
        return potential / '__init__.py'
    
    return None


def _topological_sort(graph: Dict[str, List[str]]) -> List[str]:
    """拓撲排序"""
    visited: Set[str] = set()
    stack: List[str] = []
    
    def dfs(node: str):
        if node in visited:
            return
        visited.add(node)
        
        for neighbor in graph.get(node, []):
            dfs(neighbor)
        
        stack.append(node)
    
    for node in graph:
        dfs(node)
    
    return stack[::-1]


def _identify_clusters(
    graph: Dict[str, List[str]],
    project_root: Path
) -> Dict[str, List[str]]:
    """識別模組群組（按目錄）"""
    clusters: Dict[str, List[str]] = {}
    
    for file_path in graph.keys():
        parts = Path(file_path).parts
        if len(parts) > 1:
            cluster_name = parts[0]
        else:
            cluster_name = "root"
        
        if cluster_name not in clusters:
            clusters[cluster_name] = []
        clusters[cluster_name].append(file_path)
    
    return clusters


# ============================================================
# Tool 執行器
# ============================================================

def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    執行指定的工具
    
    Args:
        tool_name: 工具名稱
        arguments: 工具參數
        
    Returns:
        dict: 工具執行結果
    """
    tool_map = {
        "read_file_content": read_file_content,
        "analyze_file_dependencies": analyze_file_dependencies,
        "get_file_structure": get_file_structure,
        "find_entry_points": find_entry_points
    }
    
    if tool_name not in tool_map:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }
    
    try:
        return tool_map[tool_name](**arguments)
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
