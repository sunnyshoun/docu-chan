"""
CLI UI - 簡化版進度顯示

功能：
1. Phase 1: 多 Worker 平行顯示 + 總進度條
2. Phase 2/3: 任務進度顯示
3. 訊息輸出

不包含：
- Streaming 顯示（已移除）
- 滾動視窗（已移除）
"""
import sys
import shutil
import threading
from dataclasses import dataclass
from typing import Optional, Dict, List
from enum import Enum
from datetime import datetime


# ==================== Constants ====================

PROGRESS_BAR_WIDTH = 30


# ==================== Windows ANSI 支援 ====================

def enable_windows_ansi() -> bool:
    """啟用 Windows 終端的 ANSI escape code 支援"""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
            return True
        except Exception:
            return False
    return True


_ANSI_ENABLED = enable_windows_ansi()


# ==================== Enums ====================

class WorkerType(Enum):
    """Worker 類型"""
    FILE_READER = "file"
    IMAGE_READER = "image"
    CHART = "chart"
    DOC = "doc"


class WorkerStatus(Enum):
    """Worker 狀態"""
    IDLE = "idle"
    READING = "reading"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class PhaseType(Enum):
    """Phase 類型"""
    ANALYZE = 1
    PLAN = 2
    GENERATE = 3


# ==================== Data Classes ====================

@dataclass
class WorkerState:
    """Worker 狀態"""
    worker_id: int
    worker_type: WorkerType
    status: WorkerStatus = WorkerStatus.IDLE
    file_path: str = ""
    line_range: tuple = (0, 0)
    task_name: str = ""
    error_msg: str = ""


# ==================== Terminal Control ====================

class TerminalControl:
    """終端控制工具"""
    
    def __init__(self):
        self.ansi_enabled = _ANSI_ENABLED
        try:
            size = shutil.get_terminal_size()
            self.width = size.columns
            self.height = size.lines
        except:
            self.width = 80
            self.height = 24
    
    def move_up(self, n: int = 1):
        if n > 0 and self.ansi_enabled:
            sys.stdout.write(f"\033[{n}A")
    
    def clear_line(self):
        if self.ansi_enabled:
            sys.stdout.write("\033[2K\r")
        else:
            sys.stdout.write("\r" + " " * (self.width - 1) + "\r")
    
    def hide_cursor(self):
        if self.ansi_enabled:
            sys.stdout.write("\033[?25l")
    
    def show_cursor(self):
        if self.ansi_enabled:
            sys.stdout.write("\033[?25h")
    
    def flush(self):
        sys.stdout.flush()


# ==================== Progress Bar ====================

def render_progress_bar(current: int, total: int, width: int = PROGRESS_BAR_WIDTH, ansi: bool = True) -> str:
    """渲染進度條"""
    if total == 0:
        return f"({current}/{total})"
    
    if not ansi:
        return f"({current}/{total})"
    
    percent = current / total
    filled = int(percent * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {percent*100:.0f}% ({current}/{total})"


# ==================== Phase 1 UI ====================

class Phase1UI:
    """
    Phase 1 分析介面
    
    顯示格式:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    分析 47 個檔案 [████████████░░░░░░░░] 60% (28/47) 12.3s
    
      [file 1] 📖 agents/base.py (L1~L50)
      [file 2] 📖 utils/logger.py (L1~L50)
      [image 1] 🖼️  docs/arch.png
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    
    def __init__(self, total_files: int):
        self.total_files = total_files
        self.completed = 0
        self.workers: Dict[int, WorkerState] = {}
        self.start_time = datetime.now()
        self.term = TerminalControl()
        self._lock = threading.Lock()
        self._last_height = 0
        self._running = False
        self._errors: List[str] = []
    
    def start(self):
        """開始 UI"""
        self._running = True
        self.term.hide_cursor()
        self._render()
    
    def stop(self):
        """停止 UI"""
        self._running = False
        self.term.show_cursor()
        if self.term.ansi_enabled and self._last_height > 0:
            self.term.move_up(self._last_height)
            for _ in range(self._last_height):
                self.term.clear_line()
                sys.stdout.write("\n")
            self.term.move_up(self._last_height)
        self.term.flush()
    
    def update_worker(
        self,
        worker_id: int,
        worker_type: WorkerType,
        status: WorkerStatus,
        file_path: str = "",
        line_range: tuple = (0, 0),
        error_msg: str = ""
    ):
        """更新 Worker 狀態"""
        with self._lock:
            self.workers[worker_id] = WorkerState(
                worker_id=worker_id,
                worker_type=worker_type,
                status=status,
                file_path=file_path,
                line_range=line_range,
                error_msg=error_msg
            )
            
            if error_msg:
                self._errors.append(f"[{worker_type.value} {worker_id}] {error_msg}")
        
        self._render()
    
    def remove_worker(self, worker_id: int):
        """移除 Worker"""
        with self._lock:
            if worker_id in self.workers:
                del self.workers[worker_id]
        self._render()
    
    def increment_completed(self):
        """增加完成計數"""
        with self._lock:
            self.completed += 1
        self._render()
    
    def _render(self):
        """渲染 UI"""
        if not self._running:
            return
        
        with self._lock:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            
            if not self.term.ansi_enabled:
                self._render_fallback(elapsed)
                return
            
            lines = []
            sep = "━" * min(60, self.term.width - 2)
            lines.append(sep)
            
            progress = render_progress_bar(self.completed, self.total_files, ansi=True)
            lines.append(f"分析 {self.total_files} 個檔案 {progress} {elapsed:.1f}s")
            lines.append("")
            
            # Workers 狀態
            for worker in sorted(self.workers.values(), key=lambda w: (w.worker_type.value, w.worker_id)):
                lines.append(self._format_worker(worker))
            
            # 錯誤訊息
            for err in self._errors[-3:]:
                lines.append(f"  ❌ {err}")
            
            lines.append(sep)
            
            # 清除舊內容並渲染新內容
            if self._last_height > 0:
                self.term.move_up(self._last_height)
            
            for line in lines:
                self.term.clear_line()
                display_line = line[:self.term.width - 1] if len(line) >= self.term.width else line
                sys.stdout.write(display_line + "\n")
            
            if self._last_height > len(lines):
                for _ in range(self._last_height - len(lines)):
                    self.term.clear_line()
                    sys.stdout.write("\n")
                self.term.move_up(self._last_height - len(lines))
            
            self._last_height = len(lines)
            self.term.flush()
    
    def _render_fallback(self, elapsed: float):
        """Fallback 渲染"""
        progress = render_progress_bar(self.completed, self.total_files, ansi=False)
        print(f"\r分析進度: {progress} {elapsed:.1f}s", end="", flush=True)
    
    def _format_worker(self, worker: WorkerState) -> str:
        """格式化 Worker 顯示"""
        type_name = worker.worker_type.value
        wid = worker.worker_id
        
        if worker.status == WorkerStatus.READING:
            if worker.worker_type == WorkerType.IMAGE_READER:
                return f"  [{type_name} {wid}] 🖼️  {worker.file_path}"
            else:
                start, end = worker.line_range
                return f"  [{type_name} {wid}] 📖 {worker.file_path} (L{start}~L{end})"
        elif worker.status == WorkerStatus.PROCESSING:
            return f"  [{type_name} {wid}] ⏳ 處理中..."
        elif worker.status == WorkerStatus.DONE:
            return f"  [{type_name} {wid}] ✅ 完成"
        elif worker.status == WorkerStatus.ERROR:
            return f"  [{type_name} {wid}] ❌ {worker.error_msg[:30]}"
        else:
            return f"  [{type_name} {wid}] ⏸️  等待中"


# ==================== Phase 2/3 UI ====================

class TaskProgressUI:
    """
    任務進度介面
    
    顯示格式:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    📋 規劃中... [████████░░░░░░░░░░░░] 40% (2/5) 8.2s
    
      [chart] 🎨 架構圖 - 設計中
      [doc] 📝 README - 撰寫中
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    
    def __init__(self, title: str = "處理中...", total_tasks: int = 0):
        self.title = title
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.current_tasks: Dict[int, Dict[str, str]] = {}
        self.start_time = datetime.now()
        self.term = TerminalControl()
        self._lock = threading.Lock()
        self._last_height = 0
        self._running = False
        self._errors: List[str] = []
    
    def start(self):
        """開始 UI"""
        self._running = True
        self.start_time = datetime.now()
        self.term.hide_cursor()
        self._render()
    
    def stop(self):
        """停止 UI"""
        self._running = False
        self.term.show_cursor()
        if self.term.ansi_enabled and self._last_height > 0:
            self.term.move_up(self._last_height)
            for _ in range(self._last_height):
                self.term.clear_line()
                sys.stdout.write("\n")
            self.term.move_up(self._last_height)
        self.term.flush()
    
    def set_title(self, title: str):
        """設定標題"""
        self.title = title
        self._render()
    
    def update_task(self, task_id: int, task_type: str, name: str, status: str):
        """更新任務狀態"""
        with self._lock:
            self.current_tasks[task_id] = {
                "type": task_type,
                "name": name,
                "status": status
            }
        self._render()
    
    def complete_task(self, task_id: int):
        """完成任務"""
        with self._lock:
            self.completed_tasks += 1
            if task_id in self.current_tasks:
                del self.current_tasks[task_id]
        self._render()
    
    def add_error(self, error: str):
        """加入錯誤訊息"""
        with self._lock:
            self._errors.append(error)
        self._render()
    
    def _render(self):
        """渲染 UI"""
        if not self._running:
            return
        
        with self._lock:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            
            if not self.term.ansi_enabled:
                self._render_fallback(elapsed)
                return
            
            lines = []
            sep = "━" * min(60, self.term.width - 2)
            lines.append(sep)
            
            if self.total_tasks > 0:
                progress = render_progress_bar(self.completed_tasks, self.total_tasks, ansi=True)
                lines.append(f"{self.title} {progress} {elapsed:.1f}s")
            else:
                lines.append(f"{self.title} {elapsed:.1f}s")
            lines.append("")
            
            # 當前任務
            for task in self.current_tasks.values():
                icon = "🎨" if task["type"] == "chart" else "📝"
                lines.append(f"  [{task['type']}] {icon} {task['name']} - {task['status']}")
            
            # 錯誤訊息
            for err in self._errors[-2:]:
                lines.append(f"  ❌ {err[:50]}")
            
            lines.append(sep)
            
            # 渲染
            if self._last_height > 0:
                self.term.move_up(self._last_height)
            
            for line in lines:
                self.term.clear_line()
                display_line = line[:self.term.width - 1] if len(line) >= self.term.width else line
                sys.stdout.write(display_line + "\n")
            
            if self._last_height > len(lines):
                for _ in range(self._last_height - len(lines)):
                    self.term.clear_line()
                    sys.stdout.write("\n")
                self.term.move_up(self._last_height - len(lines))
            
            self._last_height = len(lines)
            self.term.flush()
    
    def _render_fallback(self, elapsed: float):
        """Fallback 渲染"""
        if self.total_tasks > 0:
            progress = render_progress_bar(self.completed_tasks, self.total_tasks, ansi=False)
            print(f"\r{self.title} {progress} {elapsed:.1f}s", end="", flush=True)
        else:
            print(f"\r{self.title} {elapsed:.1f}s", end="", flush=True)


# ==================== 整合管理器 ====================

class CLIUIManager:
    """
    CLI UI 管理器
    
    用法:
        ui = CLIUIManager()
        
        # Phase 1
        ui.start_phase1(total_files=47)
        ui.update_file_worker(1, "agents/base.py", (1, 50))
        ui.file_completed()
        ui.end_phase1()
        
        # Phase 2/3
        ui.start_task_progress("📋 規劃中...", total=5)
        ui.update_task(1, "chart", "架構圖", "設計中")
        ui.complete_task(1)
        ui.end_task_progress()
    """
    
    def __init__(self):
        self._phase1_ui: Optional[Phase1UI] = None
        self._task_ui: Optional[TaskProgressUI] = None
        self._current_phase: Optional[PhaseType] = None
        self._lock = threading.Lock()
    
    # ==================== Phase 1 ====================
    
    def start_phase1(self, total_files: int):
        """開始 Phase 1"""
        with self._lock:
            self._current_phase = PhaseType.ANALYZE
            self._phase1_ui = Phase1UI(total_files)
            self._phase1_ui.start()
    
    def update_file_worker(
        self,
        worker_id: int,
        file_path: str,
        line_range: tuple = (1, 50),
        is_image: bool = False
    ):
        """更新檔案 worker 狀態"""
        if self._phase1_ui:
            worker_type = WorkerType.IMAGE_READER if is_image else WorkerType.FILE_READER
            self._phase1_ui.update_worker(
                worker_id=worker_id,
                worker_type=worker_type,
                status=WorkerStatus.READING,
                file_path=file_path,
                line_range=line_range
            )
    
    def file_worker_done(self, worker_id: int):
        """檔案 worker 完成"""
        if self._phase1_ui:
            self._phase1_ui.remove_worker(worker_id)
            self._phase1_ui.increment_completed()
    
    def file_worker_error(self, worker_id: int, error: str):
        """檔案 worker 錯誤"""
        if self._phase1_ui:
            self._phase1_ui.update_worker(
                worker_id=worker_id,
                worker_type=WorkerType.FILE_READER,
                status=WorkerStatus.ERROR,
                error_msg=error
            )
    
    def end_phase1(self):
        """結束 Phase 1"""
        if self._phase1_ui:
            self._phase1_ui.stop()
            self._phase1_ui = None
        self._current_phase = None
    
    # ==================== Phase 2/3 (Task Progress) ====================
    
    def start_task_progress(self, title: str = "處理中...", total: int = 0):
        """開始任務進度顯示"""
        with self._lock:
            self._task_ui = TaskProgressUI(title, total)
            self._task_ui.start()
    
    def set_task_title(self, title: str):
        """設定任務標題"""
        if self._task_ui:
            self._task_ui.set_title(title)
    
    def update_task(self, task_id: int, task_type: str, name: str, status: str):
        """更新任務狀態"""
        if self._task_ui:
            self._task_ui.update_task(task_id, task_type, name, status)
    
    def complete_task(self, task_id: int):
        """完成任務"""
        if self._task_ui:
            self._task_ui.complete_task(task_id)
    
    def end_task_progress(self):
        """結束任務進度顯示"""
        if self._task_ui:
            self._task_ui.stop()
            self._task_ui = None
    
    # ==================== 通用 ====================
    
    @property
    def current_phase(self) -> Optional[PhaseType]:
        return self._current_phase
    
    @property
    def ansi_enabled(self) -> bool:
        return _ANSI_ENABLED
    
    def add_error(self, error: str):
        """加入錯誤訊息"""
        if self._phase1_ui:
            self._phase1_ui._errors.append(error)
            self._phase1_ui._render()
        elif self._task_ui:
            self._task_ui.add_error(error)


# ==================== 全域實例 ====================

_ui_manager: Optional[CLIUIManager] = None


def get_ui_manager() -> CLIUIManager:
    """取得全域 UI Manager"""
    global _ui_manager
    if _ui_manager is None:
        _ui_manager = CLIUIManager()
    return _ui_manager


def reset_ui_manager():
    """重置全域 UI Manager"""
    global _ui_manager
    _ui_manager = None


# ==================== 便利函數 ====================

def print_message(message: str):
    """印出訊息"""
    print(message)


def print_progress(message: str):
    """印出進度訊息（覆蓋式）"""
    sys.stdout.write(f"\r{message}")
    sys.stdout.flush()


def print_newline():
    """輸出換行"""
    print()
