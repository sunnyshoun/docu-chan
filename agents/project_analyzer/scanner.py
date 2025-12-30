"""
Project Analyzer - File Scanner

GitIgnore 解析器與檔案掃描器
"""
from typing import List, Set
from pathlib import Path

from agents.project_analyzer.models import FileInfo


# 預設忽略的目錄和檔案模式
DEFAULT_IGNORE_PATTERNS = {
    '__pycache__', '.venv', 'venv', 'env', '.env',
    '.mypy_cache', '.pytest_cache', '.ruff_cache',
    '*.pyc', '*.pyo', '*.egg-info', '.eggs',
    'node_modules', '.npm', '.yarn',
    'dist', 'build', 'out', 'target',
    '.idea', '.vscode', '.vs',
    '.git', '.svn', '.hg',
    '.DS_Store', 'Thumbs.db',
    '*.log', '.cache', '.tox', 'htmlcov', '.coverage',
}


class GitIgnoreParser:
    """解析 .gitignore 並判斷檔案是否應被忽略"""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.patterns: Set[str] = set(DEFAULT_IGNORE_PATTERNS)
        self._load_gitignore()
    
    def _load_gitignore(self):
        """載入 .gitignore 規則"""
        gitignore_path = self.root_dir / ".gitignore"
        if gitignore_path.exists():
            try:
                content = gitignore_path.read_text(encoding='utf-8')
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    pattern = line.rstrip('/')
                    if pattern:
                        self.patterns.add(pattern)
            except Exception:
                pass
    
    def should_ignore(self, path: Path) -> bool:
        """判斷檔案是否應被忽略"""
        path_str = str(path)
        name = path.name
        
        for pattern in self.patterns:
            if name == pattern:
                return True
            if pattern in path.parts:
                return True
            if pattern.startswith('*') and name.endswith(pattern[1:]):
                return True
            if pattern.endswith('*') and name.startswith(pattern[:-1]):
                return True
        
        return False


class FileScanner:
    """掃描專案檔案（尊重 gitignore）"""
    
    TEXT_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.vue', '.svelte',
        '.java', '.kt', '.scala', '.go', '.rs', '.c', '.cpp', '.h', '.hpp',
        '.cs', '.rb', '.php', '.swift', '.m', '.mm',
        '.html', '.css', '.scss', '.sass', '.less',
        '.json', '.yaml', '.yml', '.toml', '.xml', '.ini', '.cfg',
        '.md', '.txt', '.rst', '.tex',
        '.sql', '.graphql', '.prisma',
        '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
    }
    
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp', '.ico'}
    
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
    
    def __init__(self, root_dir: Path, gitignore_parser: GitIgnoreParser):
        self.root_dir = root_dir
        self.gitignore = gitignore_parser
    
    def scan(self) -> List[FileInfo]:
        """掃描所有檔案"""
        files: List[FileInfo] = []
        
        for path in self.root_dir.rglob('*'):
            if path.is_dir():
                continue
            
            try:
                rel_path = path.relative_to(self.root_dir)
            except ValueError:
                continue
            
            if self.gitignore.should_ignore(rel_path):
                continue
            
            ext = path.suffix.lower()
            is_text = ext in self.TEXT_EXTENSIONS or path.name in {
                'Makefile', 'Dockerfile', 'Procfile', 'Gemfile',
                'Rakefile', 'Vagrantfile', 'LICENSE', 'README',
            }
            
            # 標記二進制檔案（不跳過，但標記為非文字）
            is_binary = ext in self.BINARY_EXTENSIONS
            
            try:
                size = path.stat().st_size
            except Exception:
                size = 0
            
            files.append(FileInfo(
                path=str(rel_path).replace('\\', '/'),
                abs_path=path,
                is_text=is_text and not is_binary,
                extension=ext,
                size=size
            ))
        
        return files
