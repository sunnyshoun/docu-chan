"""Mermaid Coder - 生成與修改 Mermaid 代碼"""
import re
from typing import Optional

from config.agents import AgentName
from agents.base import BaseAgent
from models import StructureLogic, MermaidCode, VisualFeedback


class MermaidCoder(BaseAgent):
    """Mermaid 代碼生成器"""
    
    PROMPT_GENERATE = "doc_generator/mermaid_coder"
    PROMPT_REVISE = "doc_generator/mermaid_revise"
    PROMPT_FIX_ERROR = "doc_generator/mermaid_fix_error"
    
    def __init__(self, coder_id: str = "A"):
        super().__init__(
            agent_name=AgentName.MERMAID_CODER,
            display_name=f"MermaidCoder-{coder_id}"
        )
    
    def generate(self, structure: StructureLogic) -> MermaidCode:
        """
        生成 Mermaid 代碼
        
        Args:
            structure: 結構邏輯
            
        Returns:
            MermaidCode: Mermaid 代碼物件
        """
        self.log(f"Generating Mermaid code for {structure.diagram_type}...")
        
        response = self.chat(
            prompt_name=self.PROMPT_GENERATE,
            variables={
                "structure_logic": structure.to_dict(),
                "diagram_type": structure.diagram_type,
                "direction": structure.direction
            }
        )
        
        code = self._extract_mermaid_code(response.message.content)
        if not code:
            raise ValueError("Failed to extract Mermaid code")
        
        return MermaidCode(code=code, diagram_type=structure.diagram_type, version=1)
    
    def revise(self, structure: StructureLogic, previous_code: str, feedback: VisualFeedback) -> MermaidCode:
        """
        根據視覺反饋修正代碼
        
        Args:
            structure: 結構邏輯
            previous_code: 之前的代碼
            feedback: 視覺反饋
            
        Returns:
            MermaidCode: 修正後的 Mermaid 代碼
        """
        self.log(f"Revising code based on feedback: {feedback.feedback_type.value}")
        
        response = self.chat(
            prompt_name=self.PROMPT_REVISE,
            variables={
                "structure_logic": structure.to_dict(),
                "previous_code": previous_code,
                "feedback_type": feedback.feedback_type.value,
                "issues": feedback.issues,
                "suggestions": feedback.suggestions
            }
        )
        
        code = self._extract_mermaid_code(response.message.content)
        if not code:
            raise ValueError("Failed to extract revised code")
        
        return MermaidCode(code=code, diagram_type=structure.diagram_type, version=1)
    
    def fix_error(self, structure: StructureLogic, broken_code: str, error_message: str) -> MermaidCode:
        """
        修復渲染錯誤（使用原始結構作為參考）
        
        Args:
            structure: 結構邏輯
            broken_code: 有問題的代碼
            error_message: 錯誤訊息
            
        Returns:
            MermaidCode: 修復後的 Mermaid 代碼
        """
        self.log("Fixing render error...")
        
        response = self.chat(
            prompt_name=self.PROMPT_FIX_ERROR,
            variables={
                "structure_logic": structure.to_dict(),
                "broken_code": broken_code,
                "error_message": error_message
            }
        )
        
        code = self._extract_mermaid_code(response.message.content)
        if not code:
            raise ValueError("Failed to extract fixed code")
        
        if code.strip() == broken_code.strip():
            raise ValueError("Fixed code is identical to broken code")
        
        return MermaidCode(code=code, diagram_type=structure.diagram_type, version=1)
    
    def _extract_mermaid_code(self, response: str) -> Optional[str]:
        """從回應中提取 Mermaid 代碼"""
        # 嘗試提取 ```mermaid ... ```
        match = re.search(r'```mermaid\s*([\s\S]*?)\s*```', response)
        if match:
            return self._fix_newlines(match.group(1).strip())
        
        # 嘗試提取一般 ``` ... ```
        match = re.search(r'```\s*([\s\S]*?)\s*```', response)
        if match:
            code = match.group(1).strip()
            # 支援 flowchart, graph, sequence, erDiagram, classDiagram
            if any(kw in code.lower() for kw in ['flowchart', 'graph', 'sequence', 'erdiagram', 'classdiagram']):
                return self._fix_newlines(code)
        
        return None
    
    def _fix_newlines(self, code: str) -> str:
        """修正 LLM 回傳的換行符"""
        code = code.replace('\\r\\n', '\n')
        code = code.replace('\\n', '\n')
        code = code.replace('\\t', '    ')
        code = code.replace('\\"', '"')
        return code

