"""
Doc Planner - 文檔規劃器

職責：
1. 接收使用者需求 + 專案架構 (report.json)
2. 規劃需要生成的文件和圖表 TODO 清單
3. 輸出 PlannerOutput 傳遞給 DocWriter 和 ChartDesigner

預設只規劃 README 和 flow_chart，除非使用者明確要求更多。
"""
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List

from config.agents import AgentName
from agents.base import BaseAgent


@dataclass
class DocTodo:
    """文件待辦項目"""
    todo_id: str
    title: str
    doc_type: str  # readme, api_doc, user_guide, developer_guide, etc.
    description: str
    priority: int = 1  # 1=高, 2=中, 3=低
    suggested_files: List[str] = field(default_factory=list)
    outline: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "todo_id": self.todo_id,
            "title": self.title,
            "doc_type": self.doc_type,
            "description": self.description,
            "priority": self.priority,
            "suggested_files": self.suggested_files,
            "outline": self.outline
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocTodo":
        return cls(
            todo_id=data.get("todo_id", ""),
            title=data.get("title", ""),
            doc_type=data.get("doc_type", "custom"),
            description=data.get("description", ""),
            priority=data.get("priority", 1),
            suggested_files=data.get("suggested_files", []),
            outline=data.get("outline", [])
        )


@dataclass
class ChartTodo:
    """圖表待辦項目"""
    todo_id: str
    title: str
    chart_type: str  # flowchart, sequence, class, architecture, etc.
    description: str
    priority: int = 1
    suggested_files: List[str] = field(default_factory=list)
    suggested_participants: List[str] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "todo_id": self.todo_id,
            "title": self.title,
            "chart_type": self.chart_type,
            "description": self.description,
            "priority": self.priority,
            "suggested_files": self.suggested_files,
            "suggested_participants": self.suggested_participants,
            "questions": self.questions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChartTodo":
        return cls(
            todo_id=data.get("todo_id", ""),
            title=data.get("title", ""),
            chart_type=data.get("chart_type", "flowchart"),
            description=data.get("description", ""),
            priority=data.get("priority", 1),
            suggested_files=data.get("suggested_files", []),
            suggested_participants=data.get("suggested_participants", []),
            questions=data.get("questions", [])
        )


@dataclass
class PlannerOutput:
    """Planner 輸出結果"""
    doc_todos: List[DocTodo]
    chart_todos: List[ChartTodo]
    project_summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_todos": [t.to_dict() for t in self.doc_todos],
            "chart_todos": [t.to_dict() for t in self.chart_todos],
            "project_summary": self.project_summary
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlannerOutput":
        return cls(
            doc_todos=[DocTodo.from_dict(t) for t in data.get("doc_todos", [])],
            chart_todos=[ChartTodo.from_dict(t) for t in data.get("chart_todos", [])],
            project_summary=data.get("project_summary", "")
        )


class DocPlanner(BaseAgent):
    """
    文檔規劃器
    
    流程：
    1. 接收 report.json + user_request
    2. 根據專案架構規劃 doc_todos 和 chart_todos
    3. 預設只規劃 README + flow_chart
    4. 輸出 PlannerOutput
    """
    
    PROMPT_PLAN = "doc_planner/planner"
    
    def __init__(self):
        super().__init__(
            agent_name=AgentName.DOC_PLANNER,
            display_name="DocPlanner"
        )
    
    def execute(
        self,
        user_request: str,
        report: Dict[str, Any],
        project_path: str
    ) -> PlannerOutput:
        """
        執行文檔規劃
        
        Args:
            user_request: 使用者的文檔需求描述
            report: Phase 1 產生的 report.json 內容
            project_path: 專案根目錄路徑
            
        Returns:
            PlannerOutput: 規劃結果，包含 doc_todos 和 chart_todos
        """
        self.log(f"Planning documentation for: {user_request[:100]}...")
        
        # 準備 prompt 變數
        project_summary = self._extract_project_summary(report)
        
        # 呼叫 LLM 進行規劃
        response = self.chat(
            prompt_name=self.PROMPT_PLAN,
            variables={
                "user_request": user_request,
                "project_summary": project_summary,
                "entry_points": json.dumps(
                    report.get("metadata", {}).get("entry_points", []),
                    ensure_ascii=False
                ),
                "core_components": json.dumps(
                    report.get("metadata", {}).get("core_components", []),
                    ensure_ascii=False
                )
            }
        )
        
        # 解析結果
        result_data = self.parse_json(response.message.content)
        
        # 建立 output
        doc_todos = [DocTodo.from_dict(t) for t in result_data.get("doc_todos", [])]
        chart_todos = [ChartTodo.from_dict(t) for t in result_data.get("chart_todos", [])]
        
        output = PlannerOutput(
            doc_todos=doc_todos,
            chart_todos=chart_todos,
            project_summary=project_summary
        )
        
        self.log(f"Planned {len(doc_todos)} doc todos, {len(chart_todos)} chart todos")
        
        return output
    
    def _extract_project_summary(self, report: Dict[str, Any]) -> str:
        """從 report 提取專案摘要"""
        metadata = report.get("metadata", {})
        return metadata.get("project_summary", "")
    
    def _extract_important_files(self, report: Dict[str, Any]) -> List[Dict[str, str]]:
        """從 report 提取重要檔案清單"""
        files = report.get("files", {})
        important = []
        
        for path, info in files.items():
            if info.get("is_important", False):
                important.append({
                    "path": path,
                    "summary": info.get("summary", "")[:200]
                })
        
        return important
