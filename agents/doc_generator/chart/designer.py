"""Diagram Designer - TPA 分析與結構設計"""
from typing import Optional

from config.settings import get_config
from agents.base import BaseAgent
from models import TPAAnalysis, StructureLogic


class DiagramDesigner(BaseAgent):
    """圖表設計師，負責 TPA 分析及結構邏輯設計"""
    
    PROMPT_TPA = "doc_generator/designer_tpa"
    PROMPT_STRUCTURE = "doc_generator/designer_structure"
    
    def __init__(self, model: Optional[str] = None):
        config = get_config()
        super().__init__(
            name="DiagramDesigner",
            model=model or config.models.diagram_designer,
            think=True
        )
        self._last_tpa: Optional[TPAAnalysis] = None
        self._last_structure: Optional[StructureLogic] = None
    
    def analyze_tpa(self, user_request: str) -> TPAAnalysis:
        """
        分析 Task, Purpose, Audience
        
        Args:
            user_request: 使用者請求
            
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
        執行完整設計流程
        
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

