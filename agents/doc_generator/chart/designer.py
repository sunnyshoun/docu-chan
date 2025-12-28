"""
Diagram Designer - TPA 分析與結構設計

支援 Tool Calling，可自主讀取檔案來補充 Planner 指引不足的資訊。
"""
import json
from typing import Optional, Dict, Any, List

from config.settings import get_config
from agents.base import BaseAgent
from models import TPAAnalysis, StructureLogic, ChartTask
from utils.generator_tools import (
    GENERATOR_TOOLS, execute_generator_tool, set_project_path
)


class DiagramDesigner(BaseAgent):
    """
    圖表設計師
    
    職責：
    - 接收 Planner 的 ChartTask（包含指引和建議）
    - 根據指引自主讀取檔案來收集資訊
    - 執行 TPA 分析及結構邏輯設計
    
    工作流程：
    1. gather_context(): 根據 task 的指引讀取相關檔案
    2. analyze_tpa(): TPA 分析
    3. design_structure(): 設計圖表結構
    """
    
    PROMPT_TPA = "doc_generator/designer_tpa"
    PROMPT_STRUCTURE = "doc_generator/designer_structure"
    PROMPT_GATHER = "doc_generator/designer_gather"  # 新增：收集資訊用
    
    MAX_TOOL_ITERATIONS = 5  # 最多呼叫 5 次工具
    
    def __init__(
        self, 
        model: Optional[str] = None,
        project_path: Optional[str] = None
    ):
        config = get_config()
        super().__init__(
            name="DiagramDesigner",
            model=model or config.models.diagram_designer,
            think=True
        )
        self._last_tpa: Optional[TPAAnalysis] = None
        self._last_structure: Optional[StructureLogic] = None
        self._gathered_context: Dict[str, Any] = {}
        
        # 設定專案路徑（用於 tool calling）
        if project_path:
            set_project_path(project_path)
    
    def execute_from_task(self, task: ChartTask, project_path: Optional[str] = None) -> dict:
        """
        從 ChartTask 執行完整設計流程（新的主要入口）
        
        Args:
            task: Planner 產生的圖表任務
            project_path: 專案路徑
            
        Returns:
            dict: 包含 tpa, structure, gathered_context
        """
        if project_path:
            set_project_path(project_path)
        
        self.log(f"Processing task: {task.title}")
        
        # Step 1: 根據 task 收集上下文
        self.log("Gathering context from source files...")
        gathered = self.gather_context(task)
        self._gathered_context = gathered
        
        # Step 2: 建立完整的 user request（結合 task 資訊和收集到的上下文）
        user_request = self._build_request_from_task(task, gathered)
        
        # Step 3: TPA 分析
        tpa = self.analyze_tpa(user_request)
        
        # Step 4: 設計結構
        structure = self.design_structure(user_request, tpa)
        
        return {
            "tpa": tpa,
            "structure": structure,
            "gathered_context": gathered,
            "user_request": user_request,
            "task": task.to_dict()
        }
    
    def gather_context(self, task: ChartTask) -> Dict[str, Any]:
        """
        根據 task 的指引收集上下文資訊
        
        使用 tool calling 讓 LLM 決定要讀取哪些檔案。
        
        Args:
            task: 圖表任務
            
        Returns:
            dict: 收集到的上下文資訊
        """
        gathered = {
            "files_read": [],
            "classes_found": [],
            "functions_found": [],
            "relationships": [],
            "raw_content": {}
        }
        
        # 建立收集資訊的 prompt
        gather_prompt = self._build_gather_prompt(task)
        
        # 使用 tool calling 讓 LLM 決定要讀什麼
        messages = [
            {"role": "system", "content": self._get_gather_system_prompt()},
            {"role": "user", "content": gather_prompt}
        ]
        
        for iteration in range(self.MAX_TOOL_ITERATIONS):
            response = self.chat_raw(
                messages=messages,
                tools=GENERATOR_TOOLS,
                keep_history=False
            )
            
            # 檢查是否有 tool calls
            if not response.message.tool_calls:
                # 沒有更多工具呼叫，LLM 認為資訊已足夠
                self.log(f"Context gathering complete after {iteration + 1} iterations")
                break
            
            # 執行 tool calls
            for tool_call in response.message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments) \
                        if isinstance(tool_call.function.arguments, str) \
                        else tool_call.function.arguments
                except json.JSONDecodeError:
                    arguments = {}
                
                self.log(f"  Calling tool: {tool_name}")
                result = execute_generator_tool(tool_name, arguments)
                
                # 記錄結果
                if result.get("success"):
                    self._process_tool_result(tool_name, arguments, result, gathered)
                
                # 加入 tool 結果到對話
                messages.append({
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [tool_call]
                })
                messages.append({
                    "role": "tool",
                    "content": json.dumps(result, ensure_ascii=False)[:2000]  # 限制長度
                })
        
        return gathered
    
    def _build_gather_prompt(self, task: ChartTask) -> str:
        """建立收集資訊的 prompt"""
        parts = [
            f"# Task: {task.title}",
            f"Type: {task.chart_type.value}",
            f"Description: {task.description}",
            ""
        ]
        
        if task.instructions:
            parts.extend([
                "## Planner Instructions:",
                task.instructions,
                ""
            ])
        
        if task.questions_to_answer:
            parts.extend([
                "## Questions to Answer:",
                *[f"- {q}" for q in task.questions_to_answer],
                ""
            ])
        
        if task.suggested_files:
            parts.extend([
                "## Suggested Files to Read:",
                *[f"- {f}" for f in task.suggested_files],
                ""
            ])
        
        if task.suggested_participants:
            parts.extend([
                "## Suggested Participants/Components:",
                *[f"- {p}" for p in task.suggested_participants],
                ""
            ])
        
        parts.extend([
            "## Your Task:",
            "Use the available tools to read source files and gather information needed to design this diagram.",
            "Focus on finding:",
            "1. Class/function definitions relevant to this diagram",
            "2. Relationships between components",
            "3. Data flow or control flow patterns",
            "",
            "When you have enough information, stop calling tools."
        ])
        
        return "\n".join(parts)
    
    def _get_gather_system_prompt(self) -> str:
        """取得收集資訊的系統 prompt"""
        return """You are a diagram designer gathering information from source code.

Your job is to use the provided tools to read source files and extract information needed to design a diagram.

Available tools:
- read_source_file: Read file content
- get_class_info: Get class structure (methods, attributes)
- get_function_info: Get function details (args, returns)
- find_references: Find where a symbol is used
- get_module_overview: Get overview of a module/directory
- analyze_call_flow: Trace function calls

Strategy:
1. Start with suggested files from the planner
2. Look at class/function structures
3. Find relationships and dependencies
4. Stop when you have enough information

Be efficient - don't read more files than necessary."""
    
    def _process_tool_result(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        gathered: Dict[str, Any]
    ):
        """處理工具結果，更新 gathered context"""
        if tool_name == "read_source_file":
            file_path = arguments.get("file_path", "unknown")
            gathered["files_read"].append(file_path)
            gathered["raw_content"][file_path] = result.get("content", "")[:3000]
        
        elif tool_name == "get_class_info":
            for cls in result.get("classes", []):
                gathered["classes_found"].append({
                    "name": cls["name"],
                    "file": arguments.get("file_path"),
                    "methods": [m["name"] for m in cls.get("methods", [])],
                    "bases": cls.get("bases", [])
                })
        
        elif tool_name == "get_function_info":
            for func in result.get("functions", []):
                gathered["functions_found"].append({
                    "name": func["name"],
                    "file": arguments.get("file_path"),
                    "args": [a["name"] for a in func.get("args", [])],
                    "returns": func.get("returns")
                })
        
        elif tool_name == "find_references":
            gathered["relationships"].extend([
                f"{ref['file']}:{ref['line']}: {ref['content']}"
                for ref in result.get("references", [])[:10]
            ])
        
        elif tool_name == "analyze_call_flow":
            calls = result.get("calls", [])
            gathered["relationships"].extend([
                f"{arguments.get('function_name')} -> {c['name']}"
                for c in calls
            ])
    
    def _build_request_from_task(self, task: ChartTask, gathered: Dict[str, Any]) -> str:
        """從 task 和 gathered context 建立完整的 user request"""
        parts = [
            f"Create a {task.chart_type.value} diagram.",
            f"Title: {task.title}",
            f"Description: {task.description}",
            ""
        ]
        
        # 加入收集到的類別資訊
        if gathered.get("classes_found"):
            parts.append("## Discovered Classes:")
            for cls in gathered["classes_found"]:
                parts.append(f"- {cls['name']}: methods={cls['methods']}, bases={cls['bases']}")
            parts.append("")
        
        # 加入收集到的函數資訊
        if gathered.get("functions_found"):
            parts.append("## Discovered Functions:")
            for func in gathered["functions_found"]:
                parts.append(f"- {func['name']}({', '.join(func['args'])}) -> {func['returns']}")
            parts.append("")
        
        # 加入關係資訊
        if gathered.get("relationships"):
            parts.append("## Discovered Relationships:")
            for rel in gathered["relationships"][:20]:
                parts.append(f"- {rel}")
            parts.append("")
        
        # 加入原有的 context 和 hints
        if task.context:
            parts.extend(["## Additional Context:", task.context, ""])
        
        if task.tpa_hints:
            parts.extend(["## Design Hints:", json.dumps(task.tpa_hints, indent=2), ""])
        
        return "\n".join(parts)
    
    # ==================== 原有方法（保持相容） ====================
    
    def analyze_tpa(self, user_request: str) -> TPAAnalysis:
        """
        分析 Task, Purpose, Audience
        
        Args:
            user_request: 使用者請求（已包含收集到的上下文）
            
        Returns:
            TPAAnalysis: TPA 分析結果
        """
        self.log("Analyzing TPA...")
        response = self.chat(
            prompt_name=self.PROMPT_TPA,
            variables={"user_request": user_request}
        )
        tpa_data = self.parse_json(response.message.content)
        tpa = TPAAnalysis.from_dict(tpa_data)
        self._last_tpa = tpa
        return tpa
    
    def design_structure(self, user_request: str, tpa: TPAAnalysis) -> StructureLogic:
        """
        設計圖表結構
        
        Args:
            user_request: 使用者請求
            tpa: TPA 分析結果
            
        Returns:
            StructureLogic: 結構邏輯
        """
        self.log("Designing structure...")
        response = self.chat(
            prompt_name=self.PROMPT_STRUCTURE,
            variables={
                "tpa_analysis": tpa.to_dict(),
                "user_request": user_request
            }
        )
        structure_data = self.parse_json(response.message.content)
        structure = StructureLogic.from_dict(structure_data)
        self._last_structure = structure
        return structure
    
    def execute(self, user_request: str) -> dict:
        """
        執行完整設計流程（舊入口，保持相容）
        
        Args:
            user_request: 使用者請求
            
        Returns:
            dict: 包含 tpa, structure, user_request
        """
        self.log(f"Processing request: {user_request[:100]}...")
        tpa = self.analyze_tpa(user_request)
        structure = self.design_structure(user_request, tpa)
        return {
            "tpa": tpa,
            "structure": structure,
            "user_request": user_request
        }
    
    @property
    def last_tpa(self) -> Optional[TPAAnalysis]:
        return self._last_tpa
    
    @property
    def last_structure(self) -> Optional[StructureLogic]:
        return self._last_structure
    
    @property
    def gathered_context(self) -> Dict[str, Any]:
        return self._gathered_context

