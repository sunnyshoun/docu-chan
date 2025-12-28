"""
Doc Writer

技術文檔撰寫與審核
"""
from typing import Dict, Any, Optional

from config.settings import get_config
from agents.base import BaseAgent
from models import DocPlan


class DocWriter(BaseAgent):
    """
    文件撰寫器
    
    負責：
    - 撰寫技術文檔各章節
    - 審核文件品質
    """
    
    PROMPT_WRITE = "doc_generator/tech_writer"
    PROMPT_REVIEW = "doc_generator/doc_reviewer"
    
    def __init__(
        self,
        writer_model: Optional[str] = None,
        reviewer_model: Optional[str] = None
    ):
        config = get_config()
        super().__init__(
            name="DocWriter",
            model=writer_model or config.models.tech_writer,
            think=False
        )
        self.writer_model = writer_model or config.models.tech_writer
        self.reviewer_model = reviewer_model or config.models.doc_reviewer
    
    def execute(self, doc_plan: DocPlan) -> Dict[str, Any]:
        """
        執行完整撰寫
        
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

