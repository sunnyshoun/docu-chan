"""
統一日誌系統 - Docu-chan

提供以下功能：
1. 統一日誌格式
2. 控制台即時更新（覆蓋式顯示進度）
3. 完整的檔案日誌記錄
4. 錯誤與警告必須顯示並記錄
5. 操作類型標籤（讀檔、分析、設計等）
"""
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from enum import Enum
from dataclasses import dataclass

# ==================== 日誌等級 ====================

class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    PROGRESS = 25  # 自訂等級：進度更新
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


# ==================== 操作類型標籤 ====================

class Operation(Enum):
    """操作類型（用於進度顯示）"""
    SCAN = "📂 掃描"
    READ = "📖 讀取"
    ANALYZE = "🔍 分析"
    PLAN = "📋 規劃"
    DESIGN = "🎨 設計"
    GENERATE = "✏️ 生成"
    BUILD = "🔨 建構"
    PACK = "📦 打包"
    WAIT = "⏳ 等待"
    DONE = "✅ 完成"
    ERROR = "❌ 錯誤"


# 添加自訂日誌等級
logging.addLevelName(LogLevel.PROGRESS.value, "PROGRESS")


# ==================== Console Handler 支援覆蓋式輸出 ====================

class ConsoleHandler(logging.Handler):
    """
    控制台 Handler，支援：
    - 一般日誌：正常輸出
    - 進度更新：覆蓋同一行
    - 錯誤/警告：始終顯示，不會被覆蓋
    """
    
    def __init__(self, show_thinking: bool = True):
        super().__init__()
        self._last_was_progress = False
        self._show_thinking = show_thinking
        self._terminal_width = 80
        
        # 嘗試取得終端寬度
        try:
            import shutil
            self._terminal_width = shutil.get_terminal_size().columns
        except:
            pass
    
    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            
            # 進度訊息：覆蓋式輸出
            if record.levelno == LogLevel.PROGRESS.value:
                if self._show_thinking:
                    # 清除當前行並輸出
                    sys.stdout.write('\r' + ' ' * self._terminal_width + '\r')
                    # 截斷過長的訊息
                    display_msg = msg[:self._terminal_width - 1]
                    sys.stdout.write(display_msg)
                    sys.stdout.flush()
                    self._last_was_progress = True
                return
            
            # 錯誤與警告：始終顯示到 stderr
            if record.levelno >= logging.WARNING:
                if self._last_was_progress:
                    sys.stdout.write('\n')
                    self._last_was_progress = False
                sys.stderr.write(msg + '\n')
                sys.stderr.flush()
                return
            
            # 一般訊息：正常輸出
            if self._last_was_progress:
                sys.stdout.write('\n')
                self._last_was_progress = False
            
            sys.stdout.write(msg + '\n')
            sys.stdout.flush()
            
        except Exception:
            self.handleError(record)
    
    def flush(self):
        """確保進度行結束"""
        if self._last_was_progress:
            sys.stdout.write('\n')
            sys.stdout.flush()
            self._last_was_progress = False


# ==================== Logger 類別 ====================

@dataclass
class LoggerConfig:
    """日誌配置"""
    name: str = "docu-chan"
    log_dir: Optional[Path] = None
    session_id: Optional[str] = None
    console_level: int = logging.INFO
    file_level: int = logging.DEBUG
    show_thinking: bool = True


class DocuLogger:
    """
    Docu-chan 統一日誌器
    
    使用方式：
        logger = DocuLogger.get_logger()
        logger.info("一般訊息")
        logger.progress("正在分析...")  # 覆蓋式更新
        logger.warning("警告")  # 始終顯示並記錄
        logger.error("錯誤")  # 始終顯示並記錄
    """
    
    _instances: dict = {}
    
    def __init__(self, config: LoggerConfig):
        self.config = config
        self._logger = logging.getLogger(config.name)
        self._logger.setLevel(logging.DEBUG)
        self._logger.handlers.clear()
        
        # Console Handler
        console_handler = ConsoleHandler(show_thinking=config.show_thinking)
        console_handler.setLevel(config.console_level)
        console_handler.setFormatter(self._create_console_formatter())
        self._logger.addHandler(console_handler)
        self._console_handler = console_handler
        
        # File Handler（如果有設定）
        if config.log_dir:
            self._setup_file_handler(config.log_dir, config.session_id)
    
    def _create_console_formatter(self) -> logging.Formatter:
        """建立控制台格式化器"""
        return logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
    
    def _create_file_formatter(self) -> logging.Formatter:
        """建立檔案格式化器（更詳細）"""
        return logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def _setup_file_handler(self, log_dir: Path, session_id: Optional[str] = None):
        """設定檔案 Handler"""
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 日誌檔名
        if session_id:
            log_file = log_dir / session_id / "session.log"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"docu-chan_{timestamp}.log"
        
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(self.config.file_level)
        file_handler.setFormatter(self._create_file_formatter())
        self._logger.addHandler(file_handler)
        self._log_file = log_file
    
    def set_log_dir(self, log_dir: Path, session_id: Optional[str] = None):
        """動態設定日誌目錄"""
        self._setup_file_handler(log_dir, session_id)
    
    # ==================== 日誌方法 ====================
    
    def debug(self, msg: str, *args, **kwargs):
        """Debug 訊息（僅記錄到檔案）"""
        self._logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """一般資訊"""
        self._logger.info(msg, *args, **kwargs)
    
    def progress(self, msg: str, op: Optional[Operation] = None, *args, **kwargs):
        """
        進度更新（覆蓋式輸出）
        
        Args:
            msg: 進度訊息
            op: 操作類型（可選，會加上對應的 emoji 標籤）
        """
        if op:
            msg = f"{op.value} {msg}"
        self._logger.log(LogLevel.PROGRESS.value, msg, *args, **kwargs)
    
    def op_progress(self, op: Operation, msg: str):
        """帶操作類型的進度更新"""
        self._logger.log(LogLevel.PROGRESS.value, f"{op.value} {msg}")
    
    def warning(self, msg: str, *args, **kwargs):
        """警告（始終顯示）"""
        self._logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, exc_info: bool = False, **kwargs):
        """錯誤（始終顯示）"""
        self._logger.error(msg, *args, exc_info=exc_info, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """嚴重錯誤"""
        self._logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        """記錄例外（包含 traceback）"""
        self._logger.exception(msg, *args, **kwargs)
    
    def finish_progress(self):
        """結束進度更新（換行）"""
        self._console_handler.flush()
    
    # ==================== 靜態方法 ====================
    
    @classmethod
    def get_logger(
        cls, 
        name: str = "docu-chan",
        log_dir: Optional[Path] = None,
        session_id: Optional[str] = None,
        show_thinking: bool = True
    ) -> 'DocuLogger':
        """
        取得或建立 Logger 實例
        
        Args:
            name: Logger 名稱
            log_dir: 日誌目錄
            session_id: Session ID
            show_thinking: 是否顯示 thinking/進度
        
        Returns:
            DocuLogger 實例
        """
        if name not in cls._instances:
            config = LoggerConfig(
                name=name,
                log_dir=log_dir,
                session_id=session_id,
                show_thinking=show_thinking
            )
            cls._instances[name] = cls(config)
        return cls._instances[name]
    
    @classmethod
    def reset(cls, name: str = "docu-chan"):
        """重置 Logger"""
        if name in cls._instances:
            del cls._instances[name]


# ==================== 便利函數 ====================

_default_logger: Optional[DocuLogger] = None


def setup_logger(
    log_dir: Optional[Path] = None,
    session_id: Optional[str] = None,
    show_thinking: bool = True
) -> DocuLogger:
    """設定並取得預設 Logger"""
    global _default_logger
    _default_logger = DocuLogger.get_logger(
        name="docu-chan",
        log_dir=log_dir,
        session_id=session_id,
        show_thinking=show_thinking
    )
    return _default_logger


def get_logger() -> DocuLogger:
    """取得預設 Logger（如未設定則建立新的）"""
    global _default_logger
    if _default_logger is None:
        _default_logger = DocuLogger.get_logger()
    return _default_logger


def log(msg: str, level: str = "INFO"):
    """相容舊版 log 函數"""
    logger = get_logger()
    level_upper = level.upper()
    
    if level_upper == "DEBUG":
        logger.debug(msg)
    elif level_upper == "INFO":
        logger.info(msg)
    elif level_upper == "PROGRESS":
        logger.progress(msg)
    elif level_upper == "WARNING":
        logger.warning(msg)
    elif level_upper == "ERROR":
        logger.error(msg)
    elif level_upper == "CRITICAL":
        logger.critical(msg)
    else:
        logger.info(msg)


# 便利函數別名
def debug(msg: str): get_logger().debug(msg)
def info(msg: str): get_logger().info(msg)
def progress(msg: str, op: Optional[Operation] = None): get_logger().progress(msg, op)
def op_progress(op: Operation, msg: str): get_logger().op_progress(op, msg)
def warning(msg: str): get_logger().warning(msg)
def error(msg: str, exc_info: bool = False): get_logger().error(msg, exc_info=exc_info)
def critical(msg: str): get_logger().critical(msg)
def exception(msg: str): get_logger().exception(msg)
def finish_progress(): get_logger().finish_progress()
