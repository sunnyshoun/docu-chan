"""Mermaid Coder - 生成與修正 Mermaid 代碼"""
import json
import re
from typing import Optional

from agents.base import BaseAgent, AgentResult
from models import StructureLogic, MermaidCode, VisualFeedback


class MermaidCoder(BaseAgent):
    """Mermaid 代碼生成器"""
    
    PROMPT_GENERATE = "doc_generator/mermaid_coder"
    PROMPT_REVISE = "doc_generator/mermaid_revise"
    PROMPT_FIX_ERROR = "doc_generator/mermaid_fix_error"
    
    def __init__(self, model: Optional[str] = None, name: str = "MermaidCoder"):
        super().__init__(
            name=name,
            model=model or "gpt-oss:20b",
            use_thinking=True
        )
    
    def generate(self, structure: StructureLogic) -> AgentResult:
        """生成 Mermaid 代碼"""
        self._log(f"Generating Mermaid code for {structure.diagram_type}...")
        
        try:
            response = self._call_llm(
                prompt_name=self.PROMPT_GENERATE,
                variables={
                    "structure_logic": json.dumps(structure.to_dict(), ensure_ascii=False, indent=2),
                    "diagram_type": structure.diagram_type,
                    "direction": structure.direction
                }
            )
            
            code = self._extract_mermaid_code(response.content)
            if not code:
                raise ValueError("Failed to extract Mermaid code")
            
            return AgentResult(
                success=True,
                data=MermaidCode(code=code, diagram_type=structure.diagram_type, version=1)
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))
    
    def revise(self, structure: StructureLogic, previous_code: str, feedback: VisualFeedback) -> AgentResult:
        """根據視覺反饋修正代碼"""
        self._log(f"Revising code based on feedback: {feedback.feedback_type.value}")
        
        try:
            response = self._call_llm(
                prompt_name=self.PROMPT_REVISE,
                variables={
                    "structure_logic": json.dumps(structure.to_dict(), ensure_ascii=False, indent=2),
                    "previous_code": previous_code,
                    "feedback_type": feedback.feedback_type.value,
                    "issues": json.dumps(feedback.issues, ensure_ascii=False),
                    "suggestions": json.dumps(feedback.suggestions, ensure_ascii=False)
                }
            )
            
            code = self._extract_mermaid_code(response.content)
            if not code:
                raise ValueError("Failed to extract revised code")
            
            return AgentResult(
                success=True,
                data=MermaidCode(code=code, diagram_type=structure.diagram_type, version=1)
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))
    
    def fix_error(self, structure: StructureLogic, broken_code: str, error_message: str) -> AgentResult:
        """修復渲染錯誤（使用原始結構作為參考）"""
        self._log("Fixing render error...")
        
        try:
            response = self._call_llm(
                prompt_name=self.PROMPT_FIX_ERROR,
                variables={
                    "structure_logic": json.dumps(structure.to_dict(), ensure_ascii=False, indent=2),
                    "broken_code": broken_code,
                    "error_message": error_message
                }
            )
            
            code = self._extract_mermaid_code(response.content)
            if not code:
                raise ValueError("Failed to extract fixed code")
            
            if code.strip() == broken_code.strip():
                raise ValueError("Fixed code is identical to broken code")
            
            return AgentResult(
                success=True,
                data=MermaidCode(code=code, diagram_type=structure.diagram_type, version=1)
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))
    
    def _extract_mermaid_code(self, response: str) -> Optional[str]:
        """從回應中提取 Mermaid 代碼"""
        # 嘗試匹配 ```mermaid ... ```
        match = re.search(r'```mermaid\s*([\s\S]*?)\s*```', response)
        if match:
            return self._fix_newlines(match.group(1).strip())
        
        # 嘗試匹配一般 ``` ... ```
        match = re.search(r'```\s*([\s\S]*?)\s*```', response)
        if match:
            code = match.group(1).strip()
            if any(kw in code.lower() for kw in ['flowchart', 'graph', 'sequence', 'erdiagram']):
                return self._fix_newlines(code)
        
        return None
    
    def _fix_newlines(self, code: str) -> str:
        """修正 LLM 回傳的換行符號"""
        code = code.replace('\\r\\n', '\n')
        code = code.replace('\\n', '\n')
        code = code.replace('\\t', '    ')
        code = code.replace('\\"', '"')
        return code
