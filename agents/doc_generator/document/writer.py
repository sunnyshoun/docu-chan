"""
Doc Writer

技術文檔撰寫和審核
"""
from typing import Dict, Any, Optional

from agents.base import BaseAgent, AgentResult
from models import DocPlan


class DocWriter(BaseAgent):
    """
    文檔撰寫器
    
    負責：
    - 撰寫技術文檔各章節
    - 審核文檔品質
    """
    
    PROMPT_WRITE = "doc_generator/tech_writer"
    PROMPT_REVIEW = "doc_generator/doc_reviewer"
    
    def __init__(
        self,
        writer_model: Optional[str] = None,
        reviewer_model: Optional[str] = None
    ):
        super().__init__(name="DocWriter", model=writer_model or "gpt-oss:20b")
        self.writer_model = writer_model or "gpt-oss:20b"
        self.reviewer_model = reviewer_model or "gpt-oss:20b"
    
    def execute(self, doc_plan: DocPlan, **kwargs) -> AgentResult:
        """生成完整文檔"""
        self._log("Generating documentation...")
        
        try:
            sections_content = []
            
            for section in doc_plan.sections:
                result = self.write_section(doc_plan.to_dict(), section)
                if result.success:
                    sections_content.append(result.data)
            
            # 審核並合併
            full_content = "\n\n".join(sections_content)
            review_result = self.review(full_content)
            
            return AgentResult(
                success=True,
                data={
                    "content": review_result.data if review_result.success else full_content,
                    "sections": sections_content
                }
            )
        except Exception as e:
            return AgentResult(success=False, data=None, error=str(e))
    
    def write_section(self, doc_plan: Dict[str, Any], section: Dict[str, Any]) -> AgentResult:
        """撰寫文檔章節"""
        self._log(f"Writing section: {section.get('title', 'unknown')}")
        
        try:
            response = self._call_llm(
                prompt_name=self.PROMPT_WRITE,
                variables={"doc_plan": doc_plan, "section": section},
                model=self.writer_model
            )
            return AgentResult(success=True, data=response.content)
        except Exception as e:
            return AgentResult(success=False, data=None, error=str(e))
    
    def review(self, content: str) -> AgentResult:
        """審核文檔"""
        self._log("Reviewing documentation...")
        
        try:
            response = self._call_llm(
                prompt_name=self.PROMPT_REVIEW,
                variables={"content": content},
                model=self.reviewer_model
            )
            return AgentResult(success=True, data=response.content)
        except Exception as e:
            return AgentResult(success=False, data=None, error=str(e))
