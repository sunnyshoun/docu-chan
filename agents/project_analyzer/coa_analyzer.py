"""
CoA Project Analyzer - Chain of Agents 架構的專案分析器

使用 CoA 架構提升分析準確度與速度：
1. Worker Agents: 平行處理各檔案，產生 local summary
2. Manager Agent: 整合所有 worker 結果，優化最終報告
3. 支援 async 平行處理，大幅提升多檔案分析速度
4. 自動處理 .gitignore 排除規則
5. Worker timeout 防止卡住
"""
import json
import asyncio
import traceback
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from config.agents import AgentName
from agents.base import BaseAgent
from agents.project_analyzer.models import FileInfo, FileAnalysisResult, ProjectContext
from agents.project_analyzer.scanner import GitIgnoreParser, FileScanner
from agents.project_analyzer.file_worker import FileAnalyzerWorker, WORKER_TIMEOUT, LINES_PER_READ
from agents.project_analyzer.manager import AnalysisManager
from agents.project_analyzer.image_worker import ImageWorker
from utils import file_utils
from utils.logger import get_logger
from utils.cli_ui import get_ui_manager
from tools.file_ops import set_project_root, clear_reports


class CoAProjectAnalyzer(BaseAgent):
    """
    CoA 專案分析器 - 使用 Chain of Agents 架構
    
    特點：
    1. 自動處理 .gitignore 排除規則
    2. Worker 帶 timeout 防止卡住
    3. 主流 Agent 檔案讀取架構（不一個一個詢問）
    4. 平行處理提升速度
    """
    
    def __init__(
        self, 
        root_dir: str, 
        prompt_dir: str, 
        dump_file: str, 
        report_file: str,
        max_parallel: int = 5,
        worker_timeout: float = WORKER_TIMEOUT
    ) -> None:
        super().__init__(
            agent_name=AgentName.FILE_WORKER,
            display_name="CoAProjectAnalyzer"
        )
        
        self.root_dir = Path(root_dir).resolve()
        self.dump_file = dump_file
        self.report_file = report_file
        self.max_parallel = max_parallel
        self.worker_timeout = worker_timeout
        self.dumps: List[Dict] = []
        self.report: Dict[str, Dict] = {}
        self.metadata: Dict[str, Any] = {}
        
        # 設定 tools 根目錄
        set_project_root(str(self.root_dir))
        
        # 初始化 GitIgnore 解析器
        self.gitignore = GitIgnoreParser(self.root_dir)
        
        # 掃描檔案（尊重 gitignore）
        scanner = FileScanner(self.root_dir, self.gitignore)
        self.files = scanner.scan()
        
        if not self.files:
            raise FileNotFoundError(f"No files found in: {root_dir}")
        
        # 為了相容性
        self.file_nodes = self.files
        self.file_paths = [f.path for f in self.files]
        
        # 建立檔案樹字串
        self.file_tree_str = self._build_file_tree_str()
        
        # 初始化圖片分析 Worker
        try:
            self.image_worker = ImageWorker(
                base=str(self.root_dir.parent),
                prompt_file=Path(prompt_dir) / "image_reader.json"
            )
        except Exception:
            self.image_worker = None
        
        # 初始化 Manager
        self.manager = AnalysisManager()
        
        self.log(f"Initialized with {len(self.files)} files (ignored {len(self.gitignore.patterns)} patterns)")
    
    def _build_file_tree_str(self) -> str:
        """建立檔案樹字串"""
        lines = [f"- {f.path}" for f in sorted(self.files, key=lambda x: x.path)[:100]]
        if len(self.files) > 100:
            lines.append(f"... and {len(self.files) - 100} more files")
        return '\n'.join(lines)
    
    def _identify_entry_points(self) -> List[str]:
        """識別入口檔案"""
        entry_patterns = {
            'main.py', 'app.py', 'cli.py', '__main__.py',
            'index.js', 'index.ts', 'main.js', 'main.ts',
            'server.py', 'server.js', 'setup.py', 'pyproject.toml', 'package.json'
        }
        return [f.path for f in self.files if f.abs_path.name.lower() in entry_patterns]
    
    def execute(self, project_path: str = "", **kwargs) -> Dict[str, Any]:
        """執行分析（同步包裝）"""
        asyncio.run(self.start_async())
        return {"report": self.report, "metadata": self.metadata}
    
    def start(self, max_retries: int = 3):
        """開始分析（同步包裝）"""
        asyncio.run(self.start_async(max_retries))
    
    async def start_async(self, max_retries: int = 3):
        """開始非同步分析"""
        logger = get_logger()
        ui = get_ui_manager()
        clear_reports()
        
        start_time = datetime.now()
        logger.info(f"分析 {len(self.files)} 個檔案 (parallel={self.max_parallel}, timeout={self.worker_timeout}s)")
        
        # 建立專案上下文
        context = ProjectContext(
            root_dir=self.root_dir,
            files=self.files,
            file_tree_str=self.file_tree_str,
            gitignore_patterns=self.gitignore.patterns,
            entry_points=self._identify_entry_points()
        )
        
        # 分組處理檔案
        groups = self._group_files_by_directory()
        
        # 使用 Phase 1 UI（啟動後不要用 print）
        ui.start_phase1(total_files=len(self.files))
        
        try:
            all_results: List[FileAnalysisResult] = []
            
            for group_name, group_files in groups.items():
                logger.debug(f"[CoAAnalyzer] 處理分組: {group_name} ({len(group_files)} files)")
                results = await self._process_group_async(group_files, context)
                all_results.extend(results)
            
            # 先停止 UI 再輸出後續訊息
            ui.end_phase1()
            
            # Manager 整合
            logger.info("🔨 整合分析結果...")
            self.report, self.metadata = await self.manager.aggregate(all_results, context)
            
            # 保存結果
            self._save_progress()
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ 分析完成：{duration:.1f}s ({len(self.report)} files)")
            
        except Exception as e:
            logger.error(f"❗ 分析失敗: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            # 確保 UI 被停止（錯誤時）
            ui.end_phase1()
            raise
    
    def _group_files_by_directory(self) -> Dict[str, List[FileInfo]]:
        """按目錄分組檔案"""
        groups: Dict[str, List[FileInfo]] = {}
        for f in self.files:
            parts = Path(f.path).parts
            key = parts[0] if len(parts) > 1 else "_root"
            if key not in groups:
                groups[key] = []
            groups[key].append(f)
        return groups
    
    async def _process_group_async(
        self, files: List[FileInfo], context: ProjectContext
    ) -> List[FileAnalysisResult]:
        """平行處理一組檔案 - 簡化顯示模式，只顯示讀取資訊"""
        logger = get_logger()
        ui = get_ui_manager()
        semaphore = asyncio.Semaphore(self.max_parallel)
        
        # 追蹤 worker 狀態
        worker_counter = [0]  # 使用 list 讓 closure 可以修改
        total_files = len(files)
        completed = [0]
        
        logger.debug(f"[CoAAnalyzer] 開始處理 {total_files} 個檔案 (parallel={self.max_parallel})")
        
        async def analyze_one(file_info: FileInfo, file_idx: int) -> FileAnalysisResult:
            logger.debug(f"[CoAAnalyzer] 排隊等待 semaphore: {file_info.path} (idx={file_idx})")
            async with semaphore:
                logger.debug(f"[CoAAnalyzer] 取得 semaphore: {file_info.path}")
                # 分配 worker ID
                worker_counter[0] += 1
                worker_id = worker_counter[0] % self.max_parallel + 1
                
                # 判斷 worker 類型
                is_image = file_info.abs_path.suffix.lower() in FileScanner.IMAGE_EXTENSIONS
                
                # 計算估計的行數
                try:
                    line_count = len(file_info.abs_path.read_text(encoding='utf-8', errors='replace').splitlines())
                    end_line = min(LINES_PER_READ, line_count)
                except:
                    line_count = 0
                    end_line = 0
                
                # 使用新 API 更新 worker 狀態
                ui.update_file_worker(worker_id, file_info.path, (1, end_line), is_image)
                
                worker = FileAnalyzerWorker(
                    root_dir=self.root_dir,
                    image_worker=self.image_worker
                )
                
                logger.debug(f"[CoAAnalyzer] 開始分析: {file_info.path}")
                result = await worker.analyze(
                    file_info,
                    context=context.file_tree_str,
                    timeout=self.worker_timeout
                )
                logger.debug(f"[CoAAnalyzer] 分析完成: {file_info.path} -> {result.summary[:50] if result.summary else 'N/A'}...")
                
                # 更新完成計數並標記 worker 完成
                completed[0] += 1
                ui.file_worker_done(worker_id)
                
                # 記錄錯誤
                if result.error:
                    logger.warning(f"⚠ {file_info.path}: {result.error}")
                    ui.add_error(f"{file_info.path}: {result.error}")
                
                self.dumps.append({
                    "time": str(datetime.now()),
                    "file": file_info.path,
                    "important": result.is_important,
                    "error": result.error
                })
                
                return result
        
        tasks = [analyze_one(f, i) for i, f in enumerate(files)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        final_results = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                logger.error(f"❌ {files[i].path}: {r}")
                final_results.append(FileAnalysisResult(
                    file_path=files[i].path, is_important=False,
                    summary=f"[Error: {r}]", error=str(r)
                ))
            else:
                final_results.append(r)
        
        return final_results
    
    def _save_progress(self):
        """保存分析進度"""
        file_utils.write_file(self.dump_file, json.dumps(self.dumps, indent=2, ensure_ascii=False))
        report_data = {"metadata": self.metadata, "files": self.report}
        file_utils.write_file(self.report_file, json.dumps(report_data, indent=2, ensure_ascii=False))


def create_coa_analyzer(
    root_dir: str,
    prompt_dir: str,
    dump_file: str,
    report_file: str,
    max_parallel: int = 5,
    worker_timeout: float = WORKER_TIMEOUT
) -> CoAProjectAnalyzer:
    """
    建立 CoA 分析器的工廠函數
    
    Args:
        root_dir: 專案根目錄
        prompt_dir: Prompt 目錄
        dump_file: Dump 輸出檔案路徑
        report_file: 報告輸出檔案路徑
        max_parallel: 最大平行 Worker 數量
        worker_timeout: Worker 超時時間（秒）
    
    Returns:
        CoAProjectAnalyzer: 配置好的分析器
    """
    return CoAProjectAnalyzer(
        root_dir=root_dir,
        prompt_dir=prompt_dir,
        dump_file=dump_file,
        report_file=report_file,
        max_parallel=max_parallel,
        worker_timeout=worker_timeout
    )
