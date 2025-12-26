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
