"""
Utility modules for Doc Generator
"""
from .file_utils import (
    ensure_dir, read_file, write_file, list_files,
    get_file_extension, get_relative_path,
    FileNode, build_file_tree
)
from .image_utils import encode_image_base64, decode_image_base64, resize_image
from .coa_utils import (
    CoAProcessor, CoAChunk, WorkerOutput, ManagerOutput,
    create_file_chunks, aggregate_worker_outputs
)
from .tools import (
    PLANNER_TOOLS, execute_tool,
    read_file_content, analyze_file_dependencies,
    get_file_structure, find_entry_points,
    build_dependency_graph
)
from .generator_tools import (
    GENERATOR_TOOLS, execute_generator_tool,
    set_project_path, get_project_path,
    read_source_file, get_class_info, get_function_info,
    find_references, get_module_overview, analyze_call_flow
)

__all__ = [
    # file_utils
    "ensure_dir",
    "read_file",
    "write_file",
    "list_files",
    "get_file_extension",
    "get_relative_path",
    "FileNode",
    "build_file_tree",
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
    # tools (Planner)
    "PLANNER_TOOLS",
    "execute_tool",
    "read_file_content",
    "analyze_file_dependencies",
    "get_file_structure",
    "find_entry_points",
    "build_dependency_graph",
    # generator_tools (Designer/Writer)
    "GENERATOR_TOOLS",
    "execute_generator_tool",
    "set_project_path",
    "get_project_path",
    "read_source_file",
    "get_class_info",
    "get_function_info",
    "find_references",
    "get_module_overview",
    "analyze_call_flow"
]
