"""
Utility modules for Doc Generator
"""
from .file_utils import (
    ensure_dir, read_file, write_file, list_files,
    get_file_extension, get_relative_path
)
from .image_utils import encode_image_base64, decode_image_base64, resize_image
from .coa_utils import (
    CoAProcessor, CoAChunk, WorkerOutput, ManagerOutput,
    create_file_chunks, aggregate_worker_outputs
)
from .logger import (
    DocuLogger, setup_logger, get_logger, log,
    debug, info, progress, warning, error, critical, exception, finish_progress,
    Operation
)
from .cli_ui import (
    CLIUIManager, WorkerType, WorkerStatus, WorkerState, PhaseType,
    Phase1UI, TaskProgressUI,
    get_ui_manager, reset_ui_manager,
    print_message, print_progress, print_newline
)

__all__ = [
    # file_utils
    "ensure_dir",
    "read_file",
    "write_file",
    "list_files",
    "get_file_extension",
    "get_relative_path",
    # image_utils
    "encode_image_base64",
    "decode_image_base64",
    "resize_image",
    # coa_utils
    "CoAProcessor",
    "CoAChunk",
    "WorkerOutput",
    "ManagerOutput",
    "create_file_chunks",
    "aggregate_worker_outputs",
    # logger
    "DocuLogger",
    "setup_logger",
    "get_logger",
    "log",
    "debug",
    "info",
    "progress",
    "warning",
    "error",
    "critical",
    "exception",
    "finish_progress",
    "Operation",
    # cli_ui
    "CLIUIManager",
    "WorkerType",
    "WorkerStatus",
    "WorkerState",
    "PhaseType",
    "Phase1UI",
    "TaskProgressUI",
    "get_ui_manager",
    "reset_ui_manager",
    "print_message",
    "print_progress",
    "print_newline",
]
