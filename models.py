"""
Data models for Doc Generator

包含所有共用的資料結構
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


# ============================================================
# Phase 1 - Understanding 資料模型
# ============================================================

@dataclass
class CodeSummary:
    """代碼摘要"""
    file_path: str
    language: str
    summary: str
    key_functions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "language": self.language,
            "summary": self.summary,
            "key_functions": self.key_functions,
            "dependencies": self.dependencies
        }


@dataclass
class ImageDescription:
    """圖片描述"""
    file_path: str
    description: str
    image_type: str  # ui, diagram, screenshot, etc.
    elements: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "description": self.description,
            "image_type": self.image_type,
            "elements": self.elements
        }


# ============================================================
# Phase 2 - Planning 資料模型
# ============================================================

class TaskType(Enum):
    """任務類型"""
    CHART = "chart"
    DOCUMENT = "document"


class ChartType(Enum):
    """圖表類型"""
    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    CLASS_DIAGRAM = "class"
    STATE_DIAGRAM = "state"
    ER_DIAGRAM = "erDiagram"
    GANTT = "gantt"
    PIE = "pie"
    MINDMAP = "mindmap"
    ARCHITECTURE = "architecture"
    API_DIAGRAM = "api"
    CUSTOM = "custom"


class DocumentType(Enum):
    """文件類型"""
    README = "readme"
    API_DOC = "api_doc"
    COMPONENT_DOC = "component_doc"
    ARCHITECTURE_DOC = "architecture_doc"
    INSTALLATION_GUIDE = "installation_guide"
    USER_GUIDE = "user_guide"
    DEVELOPER_GUIDE = "developer_guide"
    CHANGELOG = "changelog"
    CUSTOM = "custom"


@dataclass
class FileContext:
    """檔案上下文 - 用於 CoA Worker 處理"""
    file_path: str
    content: str
    summary: str = ""
    dependencies: List[str] = field(default_factory=list)
    is_entry_point: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "content": self.content,
            "summary": self.summary,
            "dependencies": self.dependencies,
            "is_entry_point": self.is_entry_point
        }


@dataclass
class ChartTask:
    """
    單一圖表生成任務
    
    Planner 產生的任務包含：
    - 基本資訊（標題、描述、類型）
    - 指引資訊（instructions, questions_to_answer）
    - 建議資訊（suggested_files, suggested_participants）
    
    Designer 會根據指引自行讀取檔案補充細節
    """
    chart_type: ChartType
    title: str
    description: str
    # 指引欄位 - 讓 Designer 知道要做什麼、要回答什麼問題
    instructions: str = ""  # Planner 給的詳細指引
    questions_to_answer: List[str] = field(default_factory=list)  # Designer 需要回答的問題
    # 建議欄位 - Designer 可以參考，但可以自己決定要不要用
    suggested_files: List[str] = field(default_factory=list)  # 建議讀取的檔案
    suggested_participants: List[str] = field(default_factory=list)  # 建議的參與者/元件
    # 舊有欄位（保持相容）
    target_files: List[str] = field(default_factory=list)
    context: str = ""
    tpa_hints: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chart_type": self.chart_type.value,
            "title": self.title,
            "description": self.description,
            "instructions": self.instructions,
            "questions_to_answer": self.questions_to_answer,
            "suggested_files": self.suggested_files,
            "suggested_participants": self.suggested_participants,
            "target_files": self.target_files,
            "context": self.context,
            "tpa_hints": self.tpa_hints,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChartTask":
        chart_type_str = data.get("chart_type", "flowchart")
        try:
            chart_type = ChartType(chart_type_str.lower())
        except ValueError:
            chart_type = ChartType.CUSTOM
        
        return cls(
            chart_type=chart_type,
            title=data.get("title", ""),
            description=data.get("description", ""),
            instructions=data.get("instructions", ""),
            questions_to_answer=data.get("questions_to_answer", []),
            suggested_files=data.get("suggested_files", data.get("target_files", [])),
            suggested_participants=data.get("suggested_participants", []),
            target_files=data.get("target_files", []),
            context=data.get("context", ""),
            tpa_hints=data.get("tpa_hints", {}),
            priority=data.get("priority", 1)
        )


@dataclass
class DocumentSection:
    """文件章節"""
    title: str
    description: str
    content_type: str  # overview, api_reference, code_example, etc.
    source_files: List[str] = field(default_factory=list)
    context: str = ""
    subsections: List["DocumentSection"] = field(default_factory=list)
    order: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "content_type": self.content_type,
            "source_files": self.source_files,
            "context": self.context,
            "subsections": [s.to_dict() for s in self.subsections],
            "order": self.order
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentSection":
        return cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            content_type=data.get("content_type", "general"),
            source_files=data.get("source_files", []),
            context=data.get("context", ""),
            subsections=[cls.from_dict(s) for s in data.get("subsections", [])],
            order=data.get("order", 0)
        )


@dataclass
class DocumentTask:
    """
    單一文件生成任務
    
    Planner 產生的任務包含：
    - 基本資訊（標題、描述、類型）
    - 指引資訊（instructions, questions_to_answer）
    - 建議資訊（suggested_files, outline）
    
    Writer 會根據指引自行讀取檔案補充細節
    """
    doc_type: DocumentType
    title: str
    description: str
    # 指引欄位 - 讓 Writer 知道要做什麼
    instructions: str = ""  # Planner 給的詳細指引
    questions_to_answer: List[str] = field(default_factory=list)  # Writer 需要回答的問題
    outline: List[str] = field(default_factory=list)  # 建議的大綱
    # 建議欄位
    suggested_files: List[str] = field(default_factory=list)  # 建議讀取的檔案
    # 舊有欄位
    sections: List[DocumentSection] = field(default_factory=list)
    target_files: List[str] = field(default_factory=list)
    style_guide: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_type": self.doc_type.value,
            "title": self.title,
            "description": self.description,
            "instructions": self.instructions,
            "questions_to_answer": self.questions_to_answer,
            "outline": self.outline,
            "suggested_files": self.suggested_files,
            "sections": [s.to_dict() for s in self.sections],
            "target_files": self.target_files,
            "style_guide": self.style_guide,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentTask":
        doc_type_str = data.get("doc_type", "readme")
        try:
            doc_type = DocumentType(doc_type_str.lower())
        except ValueError:
            doc_type = DocumentType.CUSTOM
        
        return cls(
            doc_type=doc_type,
            title=data.get("title", ""),
            description=data.get("description", ""),
            instructions=data.get("instructions", ""),
            questions_to_answer=data.get("questions_to_answer", []),
            outline=data.get("outline", []),
            suggested_files=data.get("suggested_files", data.get("target_files", [])),
            sections=[DocumentSection.from_dict(s) for s in data.get("sections", [])],
            target_files=data.get("target_files", []),
            style_guide=data.get("style_guide", {}),
            priority=data.get("priority", 1)
        )


@dataclass
class ChartPlan:
    """圖表規劃結果"""
    tasks: List[ChartTask]
    project_context: str = ""
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    execution_order: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tasks": [t.to_dict() for t in self.tasks],
            "project_context": self.project_context,
            "dependency_graph": self.dependency_graph,
            "execution_order": self.execution_order
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChartPlan":
        return cls(
            tasks=[ChartTask.from_dict(t) for t in data.get("tasks", [])],
            project_context=data.get("project_context", ""),
            dependency_graph=data.get("dependency_graph", {}),
            execution_order=data.get("execution_order", [])
        )


@dataclass
class DocPlan:
    """文檔規劃"""
    sections: List[Dict[str, Any]]
    charts_needed: List[Dict[str, Any]]
    style_guide: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sections": self.sections,
            "charts_needed": self.charts_needed,
            "style_guide": self.style_guide
        }


@dataclass
class EnhancedDocPlan:
    """增強版文檔規劃結果"""
    tasks: List[DocumentTask]
    project_context: str = ""
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    execution_order: List[int] = field(default_factory=list)
    charts_needed: List[ChartTask] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tasks": [t.to_dict() for t in self.tasks],
            "project_context": self.project_context,
            "dependency_graph": self.dependency_graph,
            "execution_order": self.execution_order,
            "charts_needed": [c.to_dict() for c in self.charts_needed]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnhancedDocPlan":
        return cls(
            tasks=[DocumentTask.from_dict(t) for t in data.get("tasks", [])],
            project_context=data.get("project_context", ""),
            dependency_graph=data.get("dependency_graph", {}),
            execution_order=data.get("execution_order", []),
            charts_needed=[ChartTask.from_dict(c) for c in data.get("charts_needed", [])]
        )


@dataclass
class PlannerResult:
    """Planner 總體結果"""
    chart_plan: Optional[ChartPlan] = None
    doc_plan: Optional[EnhancedDocPlan] = None
    project_summary: str = ""
    entry_points: List[str] = field(default_factory=list)
    file_summaries: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chart_plan": self.chart_plan.to_dict() if self.chart_plan else None,
            "doc_plan": self.doc_plan.to_dict() if self.doc_plan else None,
            "project_summary": self.project_summary,
            "entry_points": self.entry_points,
            "file_summaries": self.file_summaries
        }


@dataclass
class CoAWorkerState:
    """CoA Worker 狀態 - 用於長文本處理"""
    worker_id: int
    assigned_files: List[str]
    local_summary: str = ""
    communication_unit: str = ""
    is_complete: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "assigned_files": self.assigned_files,
            "local_summary": self.local_summary,
            "communication_unit": self.communication_unit,
            "is_complete": self.is_complete
        }


# ============================================================
# Phase 3 - Chart Generation 資料模型
# ============================================================

@dataclass
class TPAAnalysis:
    """Task, Purpose, Audience 分析結果"""
    task: Dict[str, Any]
    purpose: Dict[str, Any]
    audience: Dict[str, Any]
    design_recommendations: Dict[str, Any]
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TPAAnalysis":
        return cls(
            task=data.get("task", {}),
            purpose=data.get("purpose", {}),
            audience=data.get("audience", {}),
            design_recommendations=data.get("design_recommendations", {}),
            raw_data=data
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return self.raw_data if self.raw_data else {
            "task": self.task,
            "purpose": self.purpose,
            "audience": self.audience,
            "design_recommendations": self.design_recommendations
        }
    
    @property
    def task_type(self) -> str:
        return self.task.get("type", "unknown")
    
    @property
    def complexity(self) -> str:
        return self.design_recommendations.get("complexity_level", "moderate")


@dataclass
class StructureLogic:
    """流程圖結構邏輯"""
    diagram_type: str
    direction: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    subgraphs: List[Dict[str, Any]] = field(default_factory=list)
    styling: Dict[str, Any] = field(default_factory=dict)
    annotations: List[Dict[str, Any]] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StructureLogic":
        return cls(
            diagram_type=data.get("diagram_type", "flowchart"),
            direction=data.get("direction", "TB"),
            nodes=data.get("nodes", []),
            edges=data.get("edges", []),
            subgraphs=data.get("subgraphs", []),
            styling=data.get("styling", {}),
            annotations=data.get("annotations", []),
            raw_data=data
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return self.raw_data if self.raw_data else {
            "diagram_type": self.diagram_type,
            "direction": self.direction,
            "nodes": self.nodes,
            "edges": self.edges,
            "subgraphs": self.subgraphs,
            "styling": self.styling,
            "annotations": self.annotations
        }
    
    @property
    def node_count(self) -> int:
        return len(self.nodes)
    
    @property
    def edge_count(self) -> int:
        return len(self.edges)


@dataclass
class MermaidCode:
    """Mermaid 代碼"""
    code: str
    diagram_type: str
    version: int = 1
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MermaidCode":
        return cls(
            code=data.get("mermaid_code", data.get("code", "")),
            diagram_type=data.get("diagram_type", "flowchart"),
            version=data.get("version", 1),
            raw_data=data
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {"code": self.code, "diagram_type": self.diagram_type, "version": self.version}
    
    def __str__(self) -> str:
        return self.code


class FeedbackType(Enum):
    """視覺反饋類型"""
    APPROVED = "approved"
    OVERLAP = "overlap"
    CUTOFF = "cutoff"
    UNREADABLE = "unreadable"
    LAYOUT_ISSUE = "layout_issue"
    STYLE_ISSUE = "style_issue"
    OTHER = "other"


@dataclass
class VisualFeedback:
    """視覺檢查反饋"""
    is_approved: bool
    feedback_type: FeedbackType
    issues: List[str]
    suggestions: List[str]
    confidence: float = 0.0
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisualFeedback":
        feedback_type_str = data.get("feedback_type", "other")
        try:
            feedback_type = FeedbackType(feedback_type_str.lower())
        except ValueError:
            feedback_type = FeedbackType.OTHER
        
        return cls(
            is_approved=data.get("is_approved", data.get("looks_good", False)),
            feedback_type=feedback_type,
            issues=data.get("issues", []),
            suggestions=data.get("suggestions", []),
            confidence=data.get("confidence", 0.0),
            raw_data=data
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_approved": self.is_approved,
            "feedback_type": self.feedback_type.value,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "confidence": self.confidence
        }
    
    @property
    def needs_revision(self) -> bool:
        return not self.is_approved


@dataclass
class ChartResult:
    """Chart Generation Loop 的最終結果"""
    success: bool
    tpa: Optional[TPAAnalysis] = None
    structure: Optional[StructureLogic] = None
    mermaid_code: Optional[MermaidCode] = None
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    iterations: int = 0
    feedback_history: List[VisualFeedback] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "tpa": self.tpa.to_dict() if self.tpa else None,
            "structure": self.structure.to_dict() if self.structure else None,
            "mermaid_code": self.mermaid_code.to_dict() if self.mermaid_code else None,
            "image_path": self.image_path,
            "iterations": self.iterations,
            "feedback_history": [f.to_dict() for f in self.feedback_history],
            "error": self.error
        }


# ============================================================
# Global Context
# ============================================================

@dataclass
class GlobalContext:
    """全域上下文 - 儲存從 Phase 1 到 Phase 4 的所有中間結果"""
    from pathlib import Path
    
    project_path: Optional[Path] = None
    project_name: str = ""
    
    # Phase 1 結果
    code_summaries: List[CodeSummary] = field(default_factory=list)
    image_descriptions: List[ImageDescription] = field(default_factory=list)
    project_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Phase 2 結果
    doc_plan: Optional[DocPlan] = None
    
    # Phase 3 結果
    generated_charts: List[Dict[str, Any]] = field(default_factory=list)
    readme_content: str = ""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_code_summary(self, summary: CodeSummary):
        self.code_summaries.append(summary)
    
    def add_image_description(self, desc: ImageDescription):
        self.image_descriptions.append(desc)
    
    def add_chart(self, chart_data: Dict[str, Any]):
        self.generated_charts.append(chart_data)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": str(self.project_path) if self.project_path else None,
            "project_name": self.project_name,
            "code_summaries": [s.to_dict() for s in self.code_summaries],
            "image_descriptions": [d.to_dict() for d in self.image_descriptions],
            "project_analysis": self.project_analysis,
            "doc_plan": self.doc_plan.to_dict() if self.doc_plan else None,
            "generated_charts": self.generated_charts,
            "readme_content": self.readme_content,
            "metadata": self.metadata
        }
