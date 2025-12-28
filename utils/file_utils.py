"""
File utility functions for Doc Generator
"""
import chardet
import git
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


class FileNode:
    path: str
    name: str
    is_dir: bool
    is_text: Optional[bool]
    encoding: Optional[str]    
    confidence: Optional[float]
    children: List['FileNode']
    error: Optional[str]
    def __init__(self, path: str|Path, *, sample_size=10240, significance = 0.95):
        self.path = Path(path).as_posix()
        self.name = ""
        self.is_dir = False
        self.is_text = None
        self.encoding = None
        self.confidence = None
        self.children = []
        self.error = None
        try:
            path_obj = Path(path)
            self.name = path_obj.name or str(path_obj)
            if not path_obj.exists():
                self.error = "Path does not exist"
                return
            if path_obj.is_dir():
                self.is_text = False
                self.is_dir = True
            else:
                self._detect_encoding(sample_size, significance)

        except PermissionError:
            self.error = "Permission Denied (Init)"
            self.name = str(path)

    def add_child(self, node: 'FileNode'):
        self.children.append(node)

    def _detect_encoding(self, sample_size, significance):
        try:
            read_file(self.path)
            self.is_text = True
            self.encoding = "utf-8"
            self.confidence = 1.0
            return
        except UnicodeDecodeError:
            pass

        try:
            with open(self.path, 'rb') as f:
                raw_data = f.read(sample_size)

            result = chardet.detect(raw_data)
            
            self.encoding = result['encoding']
            self.confidence = result['confidence']

            if self.encoding and self.confidence > significance:
                self.is_text = True
            else:
                self.is_text = False
                self.encoding = f"likely {result['encoding']}"
            
        except PermissionError:
            self.error = "Permission Denied (Read Content)"
            self.is_text = False
        except Exception as e:
            self.error = f"Read Error: {e}"
            self.is_text = False

    def __repr__(self):
        status = f" [ERR: {self.error}]" if self.error else ""
        type_str = 'Dir' if self.is_dir else 'File'
        return f"<{type_str}: {self.name}{status}, text_encoding:{self.encoding}, p={self.confidence}>"
    
    def to_dict(self):
        # 1. 建立基本資訊
        data = {
            "name": self.name,
            "path": self.path,
            "is_dir": self.is_dir,
            "error": self.error
        }

        # 2. 如果是檔案，加入編碼資訊 (過濾掉 None 以保持 JSON 乾淨，可選)
        if not self.is_dir:
            data.update({
                "is_text": self.is_text,
                "encoding": self.encoding,
                "confidence": self.confidence
            })

        # 3. 遞迴處理子節點 (如果有 children 才加入這欄位)
        if self.children:
            data["children"] = [child.to_dict() for child in self.children]
        
        return data
    
    def to_list(self) -> list['FileNode']:
        if self.is_dir:
            ret: list['FileNode'] = []
            for child in self.children:
                ret += child.to_list()
            return ret
        return [self]
    
    def relative_to(self, other: str) -> str:
        return get_relative_path(self.path, other).as_posix()


def build_file_tree(
    root_path: str, 
    search_hidden: bool = False,
    chunk_size: int = 400
) -> Optional[FileNode]:
    path_obj = Path(root_path)
    if not path_obj.exists():
        return None
    
    repo = git.Repo(path_obj, search_parent_directories=True)
    all_files = [str(p) for p in path_obj.rglob('*') if p.is_file()]
    ignored_files = []
    for i in range(0, len(all_files), chunk_size):
        ignored_files.extend(repo.ignored(*all_files[i:i+chunk_size]))

    node = build_nodes(path_obj, search_hidden=search_hidden, ignored_files=ignored_files)

    return node

def build_nodes(
    path: str|Path,
    search_hidden: bool = False,
    ignored_files: list[str] = []
) -> Optional[FileNode]:
    path_obj = Path(path)
    if not path_obj.exists():
        return None
    if path in ignored_files:
        return None
    
    node = FileNode(path_obj)
    if node.is_dir:
        try:
            for item in path_obj.iterdir():
                if not search_hidden and item.name.startswith('.') and item.name != ".gitignore":
                    continue

                child_node = build_nodes(
                    str(item), 
                    search_hidden=search_hidden, 
                    ignored_files=ignored_files
                )
                
                if child_node:
                    node.add_child(child_node)

        except PermissionError:
            node.error = "Permission Denied"  # 假設 FileNode 有 error 欄位
        except Exception as e:

            print(f"讀取錯誤 {node.path}: {e}")
        if len(node.children) == 0:
            return None
        
    return node
