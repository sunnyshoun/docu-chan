"""
Diagram Designer - TPA 分析與結構設計

支援 Tool Calling，可自主讀取檔案來補充 Planner 指引不足的資訊。
"""
import json
from typing import Optional, Dict, Any

from config.agents import AgentName
from agents.base import BaseAgent
from models import TPAAnalysis, StructureLogic, ChartTask
from tools import get_tools, execute
from tools.file_ops import set_project_root


class DiagramDesigner(BaseAgent):
    """
    圖表設計師
    
    職責：
    - 接收 Planner 的 ChartTask（包含指引和建議）
    - 根據指引自主讀取檔案來收集資訊
    - 執行 TPA 分析及結構邏輯設計
    - 根據 chart_type 使用對應的 structure prompt
    """
    
    PROMPT_TPA = "doc_generator/designer_tpa"
    PROMPT_STRUCTURE = "doc_generator/designer_structure"  # default fallback
    
    # 不同圖表類型對應的 structure prompts
    STRUCTURE_PROMPTS = {
        "flowchart": "doc_generator/structure_flowchart",
        "class": "doc_generator/structure_class",
        "architecture": "doc_generator/structure_architecture",
        "sequence": "doc_generator/structure_sequence",
    }
    
    MAX_TOOL_ITERATIONS = 5
    
    def __init__(self, project_path: Optional[str] = None):
        super().__init__(
            agent_name=AgentName.DIAGRAM_DESIGNER,
            display_name="DiagramDesigner"
        )
        self._last_tpa: Optional[TPAAnalysis] = None
        self._last_structure: Optional[StructureLogic] = None
        self._gathered_context: Dict[str, Any] = {}
        self._current_chart_type: Optional[str] = None
        
        if project_path:
            set_project_root(project_path)
    
    def execute_from_task(self, task: ChartTask, project_path: Optional[str] = None) -> dict:
        """
        從 ChartTask 執行完整設計流程
        
        Args:
            task: Planner 產生的圖表任務
            project_path: 專案路徑
            
        Returns:
            dict: 包含 tpa, structure, gathered_context
        """
        if project_path:
            set_project_root(project_path)
        
        self.log(f"Processing task: {task.title}")
        
        # 記錄 chart_type 用於選擇對應的 structure prompt
        self._current_chart_type = task.chart_type.value if hasattr(task.chart_type, 'value') else str(task.chart_type)
        
        # Step 1: 收集上下文
        self.log("Gathering context from source files...")
        gathered = self.gather_context(task)
        self._gathered_context = gathered
        
        # Step 2: 建立 user request
        user_request = self._build_request_from_task(task, gathered)
        
        # Step 3: TPA 分析
        tpa = self.analyze_tpa(user_request)
        
        # Step 4: 設計結構 (使用對應的 prompt)
        structure = self.design_structure(user_request, tpa)
        
        return {
            "tpa": tpa,
            "structure": structure,
            "gathered_context": gathered,
            "user_request": user_request,
            "task": task.to_dict()
        }
    
    def gather_context(self, task: ChartTask) -> Dict[str, Any]:
        """根據 task 的指引收集上下文資訊"""
        gathered = {
            "files_read": [],
            "classes_found": [],
            "functions_found": [],
            "relationships": [],
            "raw_content": {}
        }
        
        gather_prompt = self._build_gather_prompt(task)
        
        messages = [
            {"role": "system", "content": self._get_gather_system_prompt()},
            {"role": "user", "content": gather_prompt}
        ]
        
        for iteration in range(self.MAX_TOOL_ITERATIONS):
            response = self.chat_raw(
                messages=messages,
                tools=get_tools("read_file", "search_in_file", "search_in_project", "list_directory"),
                keep_history=False
            )
            
            if not response.message.tool_calls:
                self.log(f"Context gathering complete after {iteration + 1} iterations")
                break
            
            for tool_call in response.message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments) \
                        if isinstance(tool_call.function.arguments, str) \
                        else tool_call.function.arguments
                except json.JSONDecodeError:
                    arguments = {}
                
                self.log(f"  Calling tool: {tool_name}")
                try:
                    result = execute(tool_name, **arguments)
                    result_dict = {"success": True, "result": str(result)}
                    tool_content = json.dumps(result, ensure_ascii=False)[:2000]
                except Exception as e:
                    result_dict = {"success": False, "error": str(e)}
                    tool_content = json.dumps(result_dict, ensure_ascii=False)
                
                if result_dict.get("success"):
                    self._process_tool_result(tool_name, arguments, result_dict, gathered)
                
                messages.append({
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [tool_call]
                })
                messages.append({
                    "role": "tool",
                    "content": tool_content
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
            parts.extend(["## Planner Instructions:", task.instructions, ""])
        
        # 優先顯示建議檔案，標註 entry point
        if task.suggested_files:
            parts.extend([
                "## Files to Analyze (START FROM TOP!):",
                "Read these files in order to understand the execution flow:",
                ""
            ])
            for i, f in enumerate(task.suggested_files):
                if i == 0:
                    parts.append(f"1. **{f}** ← START HERE (entry point)")
                else:
                    parts.append(f"{i+1}. {f}")
            parts.append("")
        
        if task.questions_to_answer:
            parts.extend([
                "## Questions to Answer (your diagram should visualize these):",
                *[f"- {q}" for q in task.questions_to_answer],
                ""
            ])
        
        if task.suggested_participants:
            parts.extend([
                "## Components to Include:",
                *[f"- {p}" for p in task.suggested_participants],
                ""
            ])
        
        parts.extend([
            "## Your Task:",
            "1. **Start from the first suggested file** (usually the entry point)",
            "2. Follow the execution flow: entry → middleware → routes → services → database",
            "3. Use search_in_project to find patterns (e.g., all routers, all services)",
            "4. Map relationships between components",
            "5. When you understand the flow, stop calling tools."
        ])
        
        return "\n".join(parts)
    
    def _get_gather_system_prompt(self) -> str:
        """取得收集資訊的系統 prompt"""
        return """You are a diagram designer gathering information from source code.

=== ANALYSIS STRATEGY ===

**START FROM ENTRY POINTS:**
1. First, check the report.json metadata for entry_points (e.g., main.py, app.py)
2. Read the entry point file to understand the application's main flow
3. Follow imports and function calls to understand component relationships
4. Use search_in_project to find specific patterns across the codebase

**TOOLS AVAILABLE:**
- read_file: Read file content (start with entry points!)
- search_in_file: Search for patterns in a specific file
- search_in_project: Search across all project files (e.g., find all DB connections)
- list_directory: Explore folder structure

**FOR FLOWCHARTS:**
1. Start from entry point → trace the request/execution flow
2. Look for: middleware, routers, services, database calls
3. Map the sequence of function calls

**FOR ARCHITECTURE DIAGRAMS:**
1. Identify layers: API routes, services, database connections
2. Search for: imports, clients, connections between components
3. Find bidirectional relationships (Server <-> DB)

**FOR CLASS DIAGRAMS:**
1. Search for class definitions: search_in_project("class \\w+")
2. Check inheritance: look for class X(Parent)
3. Find method signatures and attributes

Be efficient - read entry points first, then follow the execution flow."""
    
    def _process_tool_result(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        gathered: Dict[str, Any]
    ):
        """處理工具結果並提取程式碼結構"""
        if tool_name == "read_file":
            file_path = arguments.get("file_path", "unknown")
            gathered["files_read"].append(file_path)
            content = str(result.get("result", ""))[:5000]
            gathered["raw_content"][file_path] = content
            
            # 自動解析 class 和 method 結構
            self._extract_code_structure(file_path, content, gathered)
    
    def _extract_code_structure(
        self,
        file_path: str,
        content: str,
        gathered: Dict[str, Any]
    ):
        """從程式碼內容提取 class、method 結構"""
        import re
        
        lines = content.split('\n')
        current_class = None
        
        for i, line in enumerate(lines):
            # 解析 class 定義
            class_match = re.match(r'^class\s+(\w+)(?:\(([^)]*)\))?:', line)
            if class_match:
                class_name = class_match.group(1)
                bases = class_match.group(2) or ""
                bases_list = [b.strip() for b in bases.split(',') if b.strip()]
                
                current_class = {
                    "name": class_name,
                    "file": file_path,
                    "bases": bases_list,
                    "methods": [],
                    "attributes": []
                }
                gathered["classes_found"].append(current_class)
                
                # 記錄繼承關係
                for base in bases_list:
                    gathered["relationships"].append(f"{class_name} inherits {base}")
            
            # 解析 method 定義 (在 class 內)
            method_match = re.match(r'^\s+(async\s+)?def\s+(\w+)\s*\(([^)]*)\)', line)
            if method_match and current_class:
                is_async = bool(method_match.group(1))
                method_name = method_match.group(2)
                params = method_match.group(3)
                
                # 過濾 dunder methods
                if not method_name.startswith('__') or method_name in ['__init__', '__call__']:
                    current_class["methods"].append({
                        "name": method_name,
                        "async": is_async,
                        "params": params[:50]
                    })
            
            # 解析 self.xxx = 屬性 (在 __init__ 內)
            attr_match = re.match(r'^\s+self\.(\w+)\s*=', line)
            if attr_match and current_class:
                attr_name = attr_match.group(1)
                if not attr_name.startswith('_'):
                    current_class["attributes"].append(attr_name)
            
            # 解析 class 結束（下一個非縮排行）
            if current_class and not line.startswith(' ') and not line.startswith('\t') and line.strip() and not line.startswith('class'):
                current_class = None
            
            # 解析頂層函數
            top_func_match = re.match(r'^(async\s+)?def\s+(\w+)\s*\(([^)]*)\)', line)
            if top_func_match and current_class is None:
                is_async = bool(top_func_match.group(1))
                func_name = top_func_match.group(2)
                params = top_func_match.group(3)
                
                gathered["functions_found"].append({
                    "name": func_name,
                    "file": file_path,
                    "async": is_async,
                    "args": [p.strip().split(':')[0].strip() for p in params.split(',') if p.strip()],
                    "returns": "unknown"
                })
            
            # 解析 import 關係
            import_match = re.match(r'^from\s+([\w.]+)\s+import\s+(.+)', line)
            if import_match:
                module = import_match.group(1)
                imports = import_match.group(2)
                for imp in imports.split(','):
                    imp_name = imp.strip().split(' as ')[0].strip()
                    if imp_name and not imp_name.startswith('('):
                        gathered["relationships"].append(f"{file_path} imports {imp_name} from {module}")
    
    def _build_request_from_task(self, task: ChartTask, gathered: Dict[str, Any]) -> str:
        """從 task 和 gathered context 建立完整的 user request"""
        parts = [
            f"Create a {task.chart_type.value} diagram.",
            f"Title: {task.title}",
            f"Description: {task.description}",
            ""
        ]
        
        # 展示發現的 class 結構（包含內部細節）
        if gathered.get("classes_found"):
            parts.append("## Discovered Classes (with internal structure):")
            for cls in gathered["classes_found"]:
                class_info = [f"### {cls['name']}"]
                if cls.get("bases"):
                    class_info.append(f"  - Inherits: {', '.join(cls['bases'])}")
                if cls.get("attributes"):
                    class_info.append(f"  - Attributes: {', '.join(cls['attributes'][:10])}")
                if cls.get("methods"):
                    method_names = [m['name'] if isinstance(m, dict) else m for m in cls['methods'][:8]]
                    class_info.append(f"  - Key Methods: {', '.join(method_names)}")
                parts.extend(class_info)
            parts.append("")
        
        if gathered.get("functions_found"):
            parts.append("## Discovered Functions:")
            for func in gathered["functions_found"][:15]:
                async_prefix = "async " if func.get("async") else ""
                parts.append(f"- {async_prefix}{func['name']}({', '.join(func['args'][:5])})")
            parts.append("")
        
        # 整理並去重關係
        if gathered.get("relationships"):
            unique_rels = []
            seen = set()
            for rel in gathered["relationships"]:
                # 只保留繼承和重要的 import 關係
                if "inherits" in rel or ("imports" in rel and any(kw in rel for kw in ["Agent", "Loop", "Worker", "Manager", "Coder", "Designer", "Writer", "Executor"])):
                    key = rel.split(" from ")[0] if " from " in rel else rel
                    if key not in seen:
                        seen.add(key)
                        unique_rels.append(rel)
            
            if unique_rels:
                parts.append("## Key Relationships:")
                for rel in unique_rels[:25]:
                    parts.append(f"- {rel}")
                parts.append("")
        
        if task.context:
            parts.extend(["## Additional Context:", task.context, ""])
        
        if task.tpa_hints:
            parts.extend(["## Design Hints:", json.dumps(task.tpa_hints, indent=2), ""])
        
        # 加入命名策略提示
        parts.extend([
            "## NAMING GUIDELINES:",
            "- For classDiagram: Use actual class names from discovered classes",
            "- For flowchart/architecture: Use readable, abstracted names that convey purpose",
            "- Base your understanding on the discovered code structure",
            "- Names should be clear to readers unfamiliar with implementation details",
            ""
        ])
        
        return "\n".join(parts)
    
    def analyze_tpa(self, user_request: str) -> TPAAnalysis:
        """分析 Task, Purpose, Audience"""
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
        """設計圖表結構（根據 chart_type 選擇對應 prompt）"""
        # 選擇對應的 structure prompt
        chart_type = self._current_chart_type or tpa.task.get("type", "flowchart")
        prompt_name = self.STRUCTURE_PROMPTS.get(chart_type, self.PROMPT_STRUCTURE)
        
        self.log(f"Designing structure using prompt: {prompt_name}")
        response = self.chat(
            prompt_name=prompt_name,
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
        """執行完整設計流程（簡易入口）"""
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

