"""Diagram Designer - TPA 分析與結構設計"""
import json
from typing import Optional

from agents.base import BaseAgent, AgentResult
from models import TPAAnalysis, StructureLogic


class DiagramDesigner(BaseAgent):
    """圖表設計器：負責 TPA 分析與結構邏輯設計"""
    
    PROMPT_TPA = "doc_generator/designer_tpa"
    PROMPT_STRUCTURE = "doc_generator/designer_structure"
    
    def __init__(self, model: Optional[str] = None):
        super().__init__(
            name="DiagramDesigner",
            model=model or "gpt-oss:120b",
            use_thinking=True
        )
        self._last_tpa: Optional[TPAAnalysis] = None
        self._last_structure: Optional[StructureLogic] = None
    
    def execute(self, user_request: str, **kwargs) -> AgentResult:
        """設計圖表結構"""
        self._log(f"Processing request: {user_request[:100]}...")
        
        try:
            tpa_result = self._analyze_tpa(user_request)
            if not tpa_result.success:
                return tpa_result
            tpa = tpa_result.data
            self._last_tpa = tpa
            
            structure_result = self._design_structure(user_request, tpa)
            if not structure_result.success:
                return structure_result
            structure = structure_result.data
            self._last_structure = structure
            
            return AgentResult(
                success=True,
                data={"tpa": tpa, "structure": structure, "user_request": user_request}
            )
        except Exception as e:
            return AgentResult(success=False, data=None, error=str(e))
    
    def _analyze_tpa(self, user_request: str) -> AgentResult:
        """分析 Task, Purpose, Audience"""
        self._log("Analyzing TPA...")
        try:
            response = self._call_llm(
                prompt_name=self.PROMPT_TPA,
                variables={"user_request": user_request}
            )
            tpa_data = self._parse_json_response(response.content)
            return AgentResult(success=True, data=TPAAnalysis.from_dict(tpa_data))
        except Exception as e:
            return AgentResult(success=False, data=None, error=str(e))
    
    def _design_structure(self, user_request: str, tpa: TPAAnalysis) -> AgentResult:
        """設計圖表結構"""
        self._log("Designing structure...")
        try:
            response = self._call_llm(
                prompt_name=self.PROMPT_STRUCTURE,
                variables={
                    "tpa_analysis": json.dumps(tpa.to_dict(), ensure_ascii=False, indent=2),
                    "user_request": user_request
                }
            )
            structure_data = self._parse_json_response(response.content)
            return AgentResult(success=True, data=StructureLogic.from_dict(structure_data))
        except Exception as e:
            return AgentResult(success=False, data=None, error=str(e))
    
    @property
    def last_tpa(self) -> Optional[TPAAnalysis]:
        return self._last_tpa
    
    @property
    def last_structure(self) -> Optional[StructureLogic]:
        return self._last_structure
