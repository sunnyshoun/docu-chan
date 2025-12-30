"""
Doc Writer

技術文檔設計與撰寫。
整合了原本的 DocDesigner 功能，可以根據 DocTodo 自主讀取檔案、設計文檔結構並撰寫內容。
減少 Designer->Writer 的額外步驟，直接讓 Writer 邊設計邊寫文件。
"""
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from config.agents import AgentName
from agents.base import BaseAgent
from models import DocPlan, DocumentTask
from tools import get_tools, execute
from tools.file_ops import set_project_root


@dataclass
class SectionSpec:
    """章節規格"""
    title: str
    content_type: str  # overview, api_reference, code_example, etc.
    description: str
    key_points: List[str] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content_type": self.content_type,
            "description": self.description,
            "key_points": self.key_points,
            "source_files": self.source_files
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SectionSpec":
        return cls(
            title=data.get("title", ""),
            content_type=data.get("content_type", "general"),
            description=data.get("description", ""),
            key_points=data.get("key_points", []),
            source_files=data.get("source_files", [])
        )


class DocWriter(BaseAgent):
    """
    文件撰寫器（整合設計功能）
    
    職責：
    - 接收 Planner 的 DocTodo
    - 根據 DocTodo 自主讀取檔案來收集資訊
    - 設計文檔結構
    - 撰寫技術文檔
    - 審核文件品質
    
    支援兩種入口：
    1. execute_from_todo: 從 DocTodo 開始（新流程，整合設計+撰寫）
    2. execute_from_task: 從 DocumentTask 開始（舊流程，保持相容）
    """
    
    PROMPT_WRITE = "doc_generator/tech_writer"
    PROMPT_REVIEW = "doc_generator/doc_reviewer"
    
    MAX_TOOL_ITERATIONS = 8
    
    def __init__(self, project_path: Optional[str] = None):
        super().__init__(
            agent_name=AgentName.TECH_WRITER,
            display_name="DocWriter"
        )
        self._gathered_context: Dict[str, Any] = {}
        self._project_path = project_path
        
        if project_path:
            set_project_root(project_path)
    
    def execute_from_todo(
        self,
        todo,  # DocTodo from doc_planner
        report: Dict[str, Any],
        project_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        從 DocTodo 執行完整設計+撰寫流程（整合設計功能）
        
        Args:
            todo: Planner 產生的 DocTodo
            report: Phase 1 的 report.json
            project_path: 專案路徑
            
        Returns:
            dict: 包含 content, gathered_context, sections
        """
        if project_path:
            self._project_path = project_path
            set_project_root(project_path)
        
        self.log(f"Processing: {todo.title}")
        
        # Step 1: 收集上下文（使用 Tool Calling）
        self.log("Gathering context from source files...")
        gathered = self._gather_context_from_todo(todo, report)
        self._gathered_context = gathered
        
        # Step 2: 設計+撰寫（一次完成）
        self.log("Designing and writing document...")
        content = self._design_and_write(todo, gathered, report)
        
        # 驗證 content 不為空
        if not content or not content.strip():
            self.log("Warning: Generated content is empty, retrying...")
            content = self._design_and_write(todo, gathered, report)
        
        if not content or not content.strip():
            raise ValueError(f"Failed to generate content for: {todo.title}")
        
        # Step 3: 審核（傳入 todo 和 report 以檢查是否滿足需求）
        self.log("Reviewing document...")
        reviewed_content = self.review(content, todo=todo, report=report)
        
        # 確保審核後內容不為空
        if not reviewed_content or not reviewed_content.strip():
            self.log("Warning: Reviewed content is empty, using original content")
            reviewed_content = content
        
        return {
            "content": reviewed_content,
            "raw_content": content,
            "gathered_context": gathered,
            "todo": todo.to_dict()
        }
    
    def _gather_context_from_todo(
        self,
        todo,  # DocTodo
        report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用 Tool Calling 收集文件所需上下文"""
        gathered = {
            "files_read": [],
            "content_snippets": {},
            "classes_found": [],
            "functions_found": [],
            "api_definitions": [],
            "key_info": []
        }
        
        # 建立收集 prompt
        gather_prompt = self._build_gather_prompt_from_todo(todo, report)
        
        messages = [
            {"role": "system", "content": self._get_gather_system_prompt()},
            {"role": "user", "content": gather_prompt}
        ]
        
        for iteration in range(self.MAX_TOOL_ITERATIONS):
            response = self.chat_raw(
                messages=messages,
                tools=get_tools("read_file", "search_in_file", "list_directory"),
                keep_history=False
            )
            
            if not response.message.tool_calls:
                # 嘗試從最後回應提取 key_info
                try:
                    final_content = response.message.content or ""
                    if "key_info" in final_content.lower():
                        info_data = self.parse_json(final_content)
                        gathered["key_info"] = info_data.get("key_info", [])
                except:
                    pass
                self.log(f"  Context gathering complete after {iteration + 1} iterations")
                break
            
            # 處理 tool calls
            for tool_call in response.message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments) \
                        if isinstance(tool_call.function.arguments, str) \
                        else tool_call.function.arguments
                except json.JSONDecodeError:
                    arguments = {}
                
                self.log(f"  Tool: {tool_name}")
                
                try:
                    result = execute(tool_name, **arguments)
                    result_str = str(result)
                except Exception as e:
                    result_str = f"error: {e}"
                
                # 記錄讀取的檔案和提取資訊
                if tool_name == "read_file":
                    file_path = arguments.get("file_path", "unknown")
                    gathered["files_read"].append(file_path)
                    gathered["content_snippets"][file_path] = result_str[:2000]
                    # 提取程式碼元素
                    self._extract_code_elements(result_str, gathered)
                
                # 更新對話歷史
                messages.append({
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [tool_call]
                })
                messages.append({
                    "role": "tool",
                    "content": result_str[:3000]
                })
        
        return gathered
    
    def _extract_code_elements(self, content: str, gathered: Dict[str, Any]):
        """從程式碼中提取 classes 和 functions"""
        import re
        
        # Python class
        class_pattern = r'class\s+(\w+)(?:\(([^)]*)\))?:'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            bases = match.group(2) or ""
            gathered["classes_found"].append({
                "name": class_name,
                "bases": [b.strip() for b in bases.split(",") if b.strip()]
            })
        
        # Python function
        func_pattern = r'def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?:'
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1)
            args = match.group(2)
            returns = match.group(3) or "None"
            gathered["functions_found"].append({
                "name": func_name,
                "args": [a.strip().split(":")[0].strip() for a in args.split(",") if a.strip()],
                "returns": returns.strip()
            })
            gathered["api_definitions"].append({
                "type": "function",
                "name": func_name,
                "args": [a.strip().split(":")[0].strip() for a in args.split(",") if a.strip()],
                "returns": returns.strip()
            })
    
    def _build_gather_prompt_from_todo(self, todo, report: Dict[str, Any]) -> str:
        """建立收集資訊的 prompt"""
        metadata = report.get("metadata", {})
        entry_points = metadata.get('entry_points', [])
        
        parts = [
            f"# Document Task: {todo.title}",
            f"Type: {todo.doc_type}",
            f"Description: {todo.description}",
            "",
            "## Project Context:",
            f"Summary: {metadata.get('project_summary', 'N/A')[:500]}",
            ""
        ]
        
        # 強調 Entry Points
        if entry_points:
            parts.extend([
                "## Entry Points (START HERE!):",
                *[f"- **{ep}** ← Read this first to understand the main flow" for ep in entry_points],
                ""
            ])
        
        if todo.suggested_files:
            parts.extend([
                "## Suggested Files to Read:",
                *[f"- {f}" for f in todo.suggested_files],
                ""
            ])
        
        if todo.outline:
            parts.extend([
                "## Outline (must cover all items):",
                *[f"- {item}" for item in todo.outline],
                ""
            ])
        
        parts.extend([
            "## Your Task:",
            "1. **Start from entry points** to understand the application flow",
            "2. Follow imports to understand module relationships",
            "3. Use search_in_project to find specific patterns (e.g., config, API routes)",
            "4. Gather information for ALL outline sections",
            "5. When done, respond with a JSON containing key_info you found",
            "",
            "Stop when you have enough information for all outline sections."
        ])
        
        return "\n".join(parts)
    
    def _get_gather_system_prompt(self) -> str:
        """取得收集資訊的系統 prompt"""
        return """You are a technical writer gathering information from source code.

=== ANALYSIS STRATEGY ===

**START FROM ENTRY POINTS:**
1. Check report.json metadata for entry_points (e.g., main.py, app.py, Dockerfile)
2. Read the entry point to understand the application's structure
3. Follow imports to discover core modules and their purposes
4. Use search tools to find specific patterns (configs, APIs, etc.)

**TOOLS AVAILABLE:**
- read_file: Read file content (start with entry points!)
- search_in_file: Search for patterns in a specific file
- list_directory: Explore folder structure

**DOCUMENTATION STRATEGY:**
1. Entry point → understand app initialization and main flow
2. Config files → environment variables, settings
3. Routes/APIs → endpoints, parameters, responses
4. Services → business logic implementation
5. Models → data structures

**WHAT TO EXTRACT:**
- Code examples (copy actual code, don't invent)
- Function signatures with parameters
- Configuration values and defaults
- Setup and installation steps
- API endpoints and their usage

Be efficient - read entry points first, then follow the logical structure.
When you have enough information for all outline sections, stop calling tools.

At the end, summarize what you found in a JSON format with key_info array."""
    
    def _design_and_write(
        self,
        todo,  # DocTodo
        gathered: Dict[str, Any],
        report: Dict[str, Any]
    ) -> str:
        """設計並撰寫文檔（一步完成）"""
        # 建立完整的 context
        context = self._build_writing_context_from_gathered(todo, gathered, report)
        
        # 建立寫作 prompt
        writing_data = {
            "title": todo.title,
            "doc_type": todo.doc_type,
            "description": todo.description,
            "outline": todo.outline,
            "context": context
        }
        
        response = self.chat(
            prompt_name=self.PROMPT_WRITE,
            variables={
                "doc_plan": writing_data,
                "section": writing_data
            }
        )
        
        content = response.message.content or ""
        return content.strip()
    
    def _build_writing_context_from_gathered(
        self,
        todo,  # DocTodo
        gathered: Dict[str, Any],
        report: Dict[str, Any]
    ) -> str:
        """建立撰寫用的 context"""
        parts = []
        
        # 專案摘要
        metadata = report.get("metadata", {})
        if metadata.get("project_summary"):
            parts.append(f"## Project Summary:\n{metadata['project_summary'][:1000]}")
            parts.append("")
        
        # 加入 API 定義
        if gathered.get("api_definitions"):
            parts.append("## API Reference:")
            for api in gathered["api_definitions"][:20]:
                if api["type"] == "function":
                    args = ", ".join([a if isinstance(a, str) else a.get("name", "") for a in api.get("args", [])])
                    parts.append(f"- `{api['name']}({args})` -> {api.get('returns', 'None')}")
            parts.append("")
        
        # 加入 classes
        if gathered.get("classes_found"):
            parts.append("## Classes Found:")
            for cls in gathered["classes_found"][:15]:
                bases = ", ".join(cls.get("bases", []))
                parts.append(f"- `{cls['name']}` (bases: {bases or 'None'})")
            parts.append("")
        
        # 加入程式碼片段
        if gathered.get("content_snippets"):
            parts.append("## Code Snippets:")
            for file_path, code in list(gathered["content_snippets"].items())[:3]:
                parts.append(f"### {file_path}")
                parts.append(f"```python\n{code[:1500]}\n```")
            parts.append("")
        
        # 加入 key_info
        if gathered.get("key_info"):
            parts.append("## Key Information:")
            for info in gathered["key_info"][:10]:
                parts.append(f"- {info}")
            parts.append("")
        
        return "\n".join(parts)
    
    # ==================== 相容舊流程的方法 ====================
    
    def execute_from_task(
        self, 
        task: DocumentTask, 
        project_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        從 DocumentTask 執行完整撰寫流程（保持相容）
        
        Args:
            task: Planner 產生的文檔任務
            project_path: 專案路徑
            
        Returns:
            dict: 包含 content, gathered_context, task
        """
        if project_path:
            set_project_root(project_path)
        self.log("Gathering context from source files...")
        gathered = self.gather_context(task)
        self._gathered_context = gathered
        
        # Step 2: 撰寫文檔
        content = self.write_document(task, gathered)
        
        # Step 3: 審核
        reviewed_content = self.review(content)
        
        return {
            "content": reviewed_content,
            "raw_content": content,
            "gathered_context": gathered,
            "task": task.to_dict()
        }
    
    def gather_context(self, task: DocumentTask) -> Dict[str, Any]:
        """
        根據 task 的指引收集上下文資訊
        
        Args:
            task: 文檔任務
            
        Returns:
            dict: 收集到的上下文資訊
        """
        gathered = {
            "files_read": [],
            "classes_found": [],
            "functions_found": [],
            "code_snippets": {},
            "api_definitions": []
        }
        
        # 建立收集資訊的 prompt
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
                except Exception as e:
                    result_dict = {"success": False, "error": str(e)}
                
                if result_dict.get("success"):
                    self._process_tool_result(tool_name, arguments, result_dict, gathered)
                
                messages.append({
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [tool_call]
                })
                messages.append({
                    "role": "tool",
                    "content": json.dumps(result_dict, ensure_ascii=False)[:2000]
                })
        
        return gathered
    
    def _build_gather_prompt(self, task: DocumentTask) -> str:
        """建立收集資訊的 prompt"""
        parts = [
            f"# Document Task: {task.title}",
            f"Type: {task.doc_type.value}",
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
        
        if task.outline:
            parts.extend([
                "## Suggested Outline:",
                *[f"- {item}" for item in task.outline],
                ""
            ])
        
        if task.suggested_files:
            parts.extend([
                "## Suggested Files to Read:",
                *[f"- {f}" for f in task.suggested_files],
                ""
            ])
        
        parts.extend([
            "## Your Task:",
            "Use the available tools to read source files and gather information needed to write this documentation.",
            "Focus on:",
            "1. Code examples and usage patterns",
            "2. API definitions and parameters",
            "3. Class and function structures",
            "",
            "When you have enough information, stop calling tools."
        ])
        
        return "\n".join(parts)
    
    def _process_tool_result(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        gathered: Dict[str, Any]
    ):
        """處理工具結果，更新 gathered context"""
        if tool_name == "read_file":
            file_path = arguments.get("file_path", "unknown")
            gathered["files_read"].append(file_path)
            gathered["code_snippets"][file_path] = result.get("content", "")[:5000]
        
        elif tool_name == "get_class_info":
            for cls in result.get("classes", []):
                gathered["classes_found"].append({
                    "name": cls["name"],
                    "file": arguments.get("file_path"),
                    "docstring": cls.get("docstring", ""),
                    "methods": cls.get("methods", []),
                    "attributes": cls.get("attributes", [])
                })
                # 加入 API 定義
                for method in cls.get("methods", []):
                    gathered["api_definitions"].append({
                        "type": "method",
                        "class": cls["name"],
                        "name": method["name"],
                        "args": method.get("args", []),
                        "docstring": method.get("docstring", "")
                    })
        
        elif tool_name == "get_function_info":
            for func in result.get("functions", []):
                gathered["functions_found"].append(func)
                gathered["api_definitions"].append({
                    "type": "function",
                    "name": func["name"],
                    "args": func.get("args", []),
                    "returns": func.get("returns"),
                    "docstring": func.get("docstring", "")
                })
    
    def write_document(self, task: DocumentTask, gathered: Dict[str, Any]) -> str:
        """
        撰寫文檔
        
        Args:
            task: 文檔任務
            gathered: 收集到的上下文
            
        Returns:
            str: 文檔內容
        """
        self.log("Writing document...")
        
        # 建立完整的 context
        context = self._build_writing_context(task, gathered)
        
        response = self.chat(
            prompt_name=self.PROMPT_WRITE,
            variables={
                "doc_plan": task.to_dict(),
                "section": {
                    "title": task.title,
                    "description": task.description,
                    "context": context,
                    "outline": task.outline
                }
            }
        )
        
        return response.message.content
    
    def _build_writing_context(self, task: DocumentTask, gathered: Dict[str, Any]) -> str:
        """建立撰寫用的 context"""
        parts = []
        
        # 加入 API 定義
        if gathered.get("api_definitions"):
            parts.append("## API Reference:")
            for api in gathered["api_definitions"][:20]:
                if api["type"] == "function":
                    args = ", ".join([a["name"] if isinstance(a, dict) else a for a in api.get("args", [])])
                    parts.append(f"- `{api['name']}({args})` -> {api.get('returns', 'None')}")
                    if api.get("docstring"):
                        parts.append(f"  {api['docstring'][:200]}")
                else:
                    parts.append(f"- `{api.get('class', '')}.{api['name']}()`")
            parts.append("")
        
        # 加入程式碼片段
        if gathered.get("code_snippets"):
            parts.append("## Code Examples:")
            for file_path, code in list(gathered["code_snippets"].items())[:3]:
                parts.append(f"### {file_path}")
                parts.append(f"```python\n{code[:1000]}\n```")
            parts.append("")
        
        return "\n".join(parts)
    
    # ==================== 原有方法（保持相容） ====================
    
    def execute(self, doc_plan: DocPlan) -> Dict[str, Any]:
        """
        執行完整撰寫（舊入口，保持相容）
        
        Args:
            doc_plan: 文檔計畫
            
        Returns:
            dict: 包含 content 與 sections
        """
        self.log("Generating documentation...")
        
        sections_content = []
        
        for section in doc_plan.sections:
            content = self.write_section(doc_plan.to_dict(), section)
            sections_content.append(content)
        
        # 審核並合併
        full_content = "\n\n".join(sections_content)
        reviewed_content = self.review(full_content)
        
        return {
            "content": reviewed_content,
            "sections": sections_content
        }
    
    def write_section(self, doc_plan: Dict[str, Any], section: Dict[str, Any]) -> str:
        """
        撰寫單一章節
        
        Args:
            doc_plan: 文檔計畫字典
            section: 章節資訊
            
        Returns:
            str: 章節內容
        """
        self.log(f"Writing section: {section.get('title', 'unknown')}")
        
        response = self.chat(
            prompt_name=self.PROMPT_WRITE,
            variables={"doc_plan": doc_plan, "section": section}
        )
        return response.message.content
    
    def review(self, content: str, todo=None, report: Dict[str, Any] = None, max_revisions: int = 2) -> str:
        """
        審核文檔並修正問題
        
        Args:
            content: 文檔內容
            todo: DocTodo，用於檢查文件是否滿足需求
            report: Phase 1 的 report.json
            max_revisions: 最大修訂次數
            
        Returns:
            str: 審核並修正後的文檔內容
        """
        current_content = content
        
        # 建立 TODO 需求摘要
        todo_requirements = self._build_todo_requirements(todo) if todo else ""
        project_context = self._build_project_context_for_review(report) if report else ""
        
        for revision in range(max_revisions):
            self.log(f"Reviewing documentation (revision {revision + 1}/{max_revisions})...")
            
            # 建立審核變數
            review_variables = {
                "draft": current_content,
                "todo_requirements": todo_requirements,
                "project_context": project_context
            }
            
            # 請 LLM 審核
            response = self.chat(
                prompt_name=self.PROMPT_REVIEW,
                variables=review_variables,
                format="json"
            )
            
            # 解析審核結果
            try:
                review_result = self.parse_json(response.message.content or "{}")
            except Exception:
                # 如果無法解析，視為通過
                self.log("Review result parsing failed, returning current content")
                return current_content
            
            is_approved = review_result.get("is_approved", True)
            issues = review_result.get("issues", [])
            suggestions = review_result.get("suggestions", [])
            
            if is_approved or not issues:
                self.log("Document approved!")
                return current_content
            
            # 有問題，請 LLM 修正
            self.log(f"Found {len(issues)} issues, requesting revision...")
            
            revision_prompt = self._build_revision_prompt(current_content, issues, suggestions)
            
            revision_response = self.chat_raw(
                messages=[
                    {"role": "system", "content": "You are a technical writer. Revise the document based on the feedback. Return ONLY the revised markdown document, no explanations."},
                    {"role": "user", "content": revision_prompt}
                ],
                keep_history=False
            )
            
            revised_content = revision_response.message.content or ""
            
            # 清理可能的 code fence
            if revised_content.startswith("```markdown"):
                revised_content = revised_content[len("```markdown"):].strip()
            if revised_content.startswith("```md"):
                revised_content = revised_content[len("```md"):].strip()
            if revised_content.startswith("```"):
                revised_content = revised_content[3:].strip()
            if revised_content.endswith("```"):
                revised_content = revised_content[:-3].strip()
            
            # 確保修訂後內容不為空
            if revised_content.strip():
                current_content = revised_content
            else:
                self.log("Warning: Revision returned empty content, keeping previous version")
        
        return current_content
    
    def _build_revision_prompt(self, content: str, issues: List[str], suggestions: List[str]) -> str:
        """建立修訂 prompt"""
        parts = [
            "# Document to Revise:",
            content,
            "",
            "# Issues Found:"
        ]
        for i, issue in enumerate(issues[:10], 1):
            parts.append(f"{i}. {issue}")
        
        if suggestions:
            parts.append("")
            parts.append("# Suggestions:")
            for i, suggestion in enumerate(suggestions[:10], 1):
                parts.append(f"{i}. {suggestion}")
        
        parts.extend([
            "",
            "Please revise the document to address these issues.",
            "Return the complete revised markdown document."
        ])
        
        return "\n".join(parts)
    
    def _build_todo_requirements(self, todo) -> str:
        """建立 TODO 需求摘要給 reviewer"""
        if not todo:
            return "No TODO requirements available."
        
        parts = [
            f"Title: {todo.title}",
            f"Type: {todo.doc_type}",
            f"Description: {todo.description}",
            ""
        ]
        
        if todo.outline:
            parts.append("Required Outline (ALL items must be covered):")
            for i, item in enumerate(todo.outline, 1):
                parts.append(f"  {i}. {item}")
            parts.append("")
        
        if hasattr(todo, 'suggested_files') and todo.suggested_files:
            parts.append("Suggested source files to reference:")
            for f in todo.suggested_files[:10]:
                parts.append(f"  - {f}")
            parts.append("")
        
        return "\n".join(parts)
    
    def _build_project_context_for_review(self, report: Dict[str, Any]) -> str:
        """建立專案 context 給 reviewer"""
        if not report:
            return "No project context available."
        
        parts = []
        metadata = report.get("metadata", {})
        
        if metadata.get("project_summary"):
            parts.append(f"Project Summary: {metadata['project_summary'][:500]}")
            parts.append("")
        
        if metadata.get("entry_points"):
            parts.append(f"Entry Points: {', '.join(metadata['entry_points'][:5])}")
            parts.append("")
        
        if metadata.get("tech_stack"):
            parts.append(f"Tech Stack: {metadata['tech_stack']}")
            parts.append("")
        
        # 加入重要檔案摘要
        file_summaries = report.get("file_summaries", {})
        if file_summaries:
            parts.append("Key Files:")
            for path, summary in list(file_summaries.items())[:10]:
                parts.append(f"  - {path}: {summary[:100]}")
            parts.append("")
        
        return "\n".join(parts) if parts else "No project context available."
    
    @property
    def gathered_context(self) -> Dict[str, Any]:
        return self._gathered_context

