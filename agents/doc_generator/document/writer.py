"""
Doc Writer

技術文檔撰寫與審核。
支援 Tool Calling，可自主讀取檔案來補充 Planner 指引不足的資訊。
"""
import json
from typing import Dict, Any, Optional, List

from config.settings import get_config
from agents.base import BaseAgent
from models import DocPlan, DocumentTask
from tools import get_tools, execute
from tools.file_ops import set_project_root


class DocWriter(BaseAgent):
    """
    文件撰寫器
    
    職責：
    - 接收 Planner 的 DocumentTask（包含指引和建議）
    - 根據指引自主讀取檔案來收集資訊
    - 撰寫技術文檔各章節
    - 審核文件品質
    
    工作流程：
    1. gather_context(): 根據 task 的指引讀取相關檔案
    2. write_document(): 撰寫文檔
    3. review(): 審核並修正
    """
    
    PROMPT_WRITE = "doc_generator/tech_writer"
    PROMPT_REVIEW = "doc_generator/doc_reviewer"
    PROMPT_GATHER = "doc_generator/writer_gather"
    
    MAX_TOOL_ITERATIONS = 5
    
    def __init__(
        self,
        writer_model: Optional[str] = None,
        reviewer_model: Optional[str] = None,
        project_path: Optional[str] = None
    ):
        config = get_config()
        super().__init__(
            name="DocWriter",
            model=writer_model or config.models.tech_writer,
            think=False
        )
        self.writer_model = writer_model or config.models.tech_writer
        self.reviewer_model = reviewer_model or config.models.doc_reviewer
        self._gathered_context: Dict[str, Any] = {}
        
        if project_path:
            set_project_root(project_path)
    
    def execute_from_task(
        self, 
        task: DocumentTask, 
        project_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        從 DocumentTask 執行完整撰寫流程（新的主要入口）
        
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
                tools=get_tools("read_file", "report_summary"),
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
    
    def _get_gather_system_prompt(self) -> str:
        """取得收集資訊的系統 prompt"""
        return """You are a technical writer gathering information from source code.

Your job is to use the provided tools to read source files and extract information needed to write documentation.

Available tools:
- read_source_file: Read file content for code examples
- get_class_info: Get class structure for API documentation
- get_function_info: Get function details for reference docs
- get_module_overview: Get overview of a module/directory

Strategy:
1. Start with suggested files from the planner
2. Focus on public APIs and important functions
3. Collect code examples that would help users
4. Stop when you have enough information

Be efficient - gather what's needed for good documentation."""
    
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
    
    def review(self, content: str) -> str:
        """
        審核文檔
        
        Args:
            content: 文檔內容
            
        Returns:
            str: 審核後的文檔內容
        """
        self.log("Reviewing documentation...")
        
        # 暫時切換模型進行審核
        original_model = self.model
        self.model = self.reviewer_model
        
        response = self.chat(
            prompt_name=self.PROMPT_REVIEW,
            variables={"content": content}
        )
        
        self.model = original_model
        return response.message.content
    
    @property
    def gathered_context(self) -> Dict[str, Any]:
        return self._gathered_context

