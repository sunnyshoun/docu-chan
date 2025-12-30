from base64 import b64encode
from pathlib import Path
from typing import Optional
from git import Repo, exc

import chardet


class FileInfo:
    path: Path
    name: str
    is_dir: bool
    size: Optional[int]
    is_text: Optional[bool]
    file_type: Optional[str]    
    confidence: Optional[float]
    error: Optional[str]
    def __init__(self, path: str|Path, *, sample_size=1024, significance = 0.95):
        self.path = Path(path)
        self.name = ""
        self.is_dir = False
        self.size = 0
        self.is_text = None
        self.file_type = None
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
                self.size = path_obj.stat().st_size
                self._detect_encoding(sample_size, significance)

        except PermissionError:
            self.error = "Permission Denied (Init)"
            self.name = str(path)

    def _detect_encoding(self, sample_size: int = 1024, significance: float = 0.9):
        self.confidence = 1.0
        self.is_text = False
        self.file_type = "utf-8"
        if self.is_dir:
            self.file_type = "Directory"
            return
        if self.size == 0:
            self.file_type = "Empty"
            return
        try:
            file_bytes = self.path.read_bytes()
        except PermissionError:
            self.error = "Permission Denied (Read Content)"
            return
        except Exception as e:
            self.error = f"Read Error: {e}"
            return

        try:
            file_bytes.decode("utf-8")
            self.is_text = True
            return
        except UnicodeDecodeError:
            pass
            
        result = chardet.detect(file_bytes[:sample_size])
        self.file_type = result['encoding']
        self.confidence = result['confidence']
        if self.confidence > significance:
            self.is_text = True
            return
        self.file_type = self.path.suffix

    def __repr__(self):
        status = f" [ERR: {self.error}]" if self.error else ""
        type_str = 'Dir' if self.is_dir else 'File'
        return f"{type_str}: {self.name+status:<30}, type:{self.file_type:<10}, p={self.confidence}"
    
    def relative_to(self, other: str | Path) -> Path:
        return self.path.relative_to(Path(other))
    
    def read_text_line(self, line: int) -> str:
        if not self.is_text:
            return "<<<base64encoded>>>\n" + b64encode(self.path.read_bytes()[:line**2]).decode()
        
        lines: list[str] = []
        shrink: list[str] = []
        with open(self.path, "r", encoding=self.file_type) as f:
            lines = f.readlines()
        
        for l in lines:
            ll = l.strip()
            if len(ll) > 0:
                shrink.append(ll)
            
        return "\n".join(shrink[:line])



def build_file_list(
    root_path: str | Path, 
    search_hidden: bool = True,
    chunk_size: int = 400
) -> list[FileInfo]:
    path_obj = Path(root_path)
    if not path_obj.exists():
        return []
    all_files = []
    repo = Repo.init(path_obj)

    for p in path_obj.rglob('*'):
        if not search_hidden and p.name.startswith(".") and p.name != ".gitignore":
            continue
        if p.is_relative_to(path_obj/".git"):
            continue
        if p.is_file():
            all_files.append(str(p))
    included = set(all_files)

    for i in range(0, len(all_files), chunk_size):
        included -= set(repo.ignored(*all_files[i:i+chunk_size]))
    
    return [FileInfo(f) for f in included]
        
