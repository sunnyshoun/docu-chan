"""Mermaid Coder - 生成與修正 Mermaid 代碼"""
import json
import re
from typing import Optional, List

from agents.base import BaseAgent, AgentResult
from models import StructureLogic, MermaidCode, VisualFeedback


class MermaidCoder(BaseAgent):
    """Mermaid 代碼生成器：根據結構生成代碼，並根據反饋修正"""
    
    PROMPT_GENERATE = "doc_generator/mermaid_coder"
    PROMPT_REVISE = "doc_generator/mermaid_revise"
    
    def __init__(self, model: Optional[str] = None):
        super().__init__(
            name="MermaidCoder",
            model=model or "gpt-oss:20b",
            use_thinking=True
        )
        self._code_history: List[MermaidCode] = []
    
    def execute(self, structure: StructureLogic, feedback: Optional[VisualFeedback] = None, **kwargs) -> AgentResult:
        """執行 Mermaid 代碼生成或修正"""
        if feedback is not None and self._code_history:
            # 有反饋且有歷史代碼，進行修正
            previous_code = self._code_history[-1].code
            return self.revise(structure, previous_code, feedback)
        else:
            # 生成新代碼
            return self.generate(structure)
    
    def generate(self, structure: StructureLogic) -> AgentResult:
        """生成 Mermaid 代碼"""
        self._log(f"Generating Mermaid code for {structure.diagram_type}...")
        
        response = None
        try:
            response = self._call_llm(
                prompt_name=self.PROMPT_GENERATE,
                variables={
                    "structure_logic": json.dumps(structure.to_dict(), ensure_ascii=False, indent=2),
                    "diagram_type": structure.diagram_type,
                    "direction": structure.direction
                }
            )
            
            # 優先嘗試從 markdown code block 提取（更穩健）
            code = self._extract_mermaid_code(response.content)
            result_data = {}
            
            if not code:
                # 退回 JSON 解析
                result_data = self._parse_json_response(response.content)
                raw_code = result_data.get("mermaid_code", result_data.get("code", ""))
                code = self._fix_newlines(raw_code)
            else:
                code = self._fix_newlines(code)
            
            mermaid_code = MermaidCode(
                code=code,
                diagram_type=structure.diagram_type,
                version=len(self._code_history) + 1,
                raw_data=result_data
            )
            
            if not mermaid_code.code.strip():
                raise ValueError("Generated Mermaid code is empty")
            
            self._code_history.append(mermaid_code)
            return AgentResult(success=True, data=mermaid_code, raw_response=response.content)
            
        except (json.JSONDecodeError, ValueError) as e:
            # 最後嘗試從回應中提取代碼
            if response and hasattr(response, 'content'):
                code = self._extract_mermaid_code(response.content)
                if code:
                    mermaid_code = MermaidCode(
                        code=code,
                        diagram_type=structure.diagram_type,
                        version=len(self._code_history) + 1
                    )
                    self._code_history.append(mermaid_code)
                    return AgentResult(success=True, data=mermaid_code)
            return AgentResult(success=False, data=None, error=f"Failed to parse response: {e}")
        except Exception as e:
            return AgentResult(success=False, data=None, error=str(e))
    
    def revise(
        self,
        structure: StructureLogic,
        previous_code: str,
        feedback: VisualFeedback
    ) -> AgentResult:
        """根據反饋修正代碼"""
        self._log(f"Revising code based on feedback: {feedback.feedback_type.value}")
        
        response = None
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
            
            # 優先嘗試從 markdown code block 提取（更穩健）
            code = self._extract_mermaid_code(response.content)
            result_data = {}
            
            if not code:
                # 退回 JSON 解析
                result_data = self._parse_json_response(response.content)
                raw_code = result_data.get("mermaid_code", result_data.get("code", ""))
                code = self._fix_newlines(raw_code)
            else:
                code = self._fix_newlines(code)
            
            if not code or not code.strip():
                raise ValueError("Revised Mermaid code is empty")
            
            mermaid_code = MermaidCode(
                code=code,
                diagram_type=structure.diagram_type,
                version=len(self._code_history) + 1,
                raw_data=result_data
            )
            self._code_history.append(mermaid_code)
            return AgentResult(success=True, data=mermaid_code)
        except (json.JSONDecodeError, ValueError) as e:
            # 最後嘗試從回應中提取代碼
            if response and hasattr(response, 'content'):
                code = self._extract_mermaid_code(response.content)
                if code:
                    mermaid_code = MermaidCode(
                        code=code,
                        diagram_type=structure.diagram_type,
                        version=len(self._code_history) + 1
                    )
                    self._code_history.append(mermaid_code)
                    return AgentResult(success=True, data=mermaid_code)
            return AgentResult(success=False, data=None, error=f"Failed to revise: {e}")
    
    def _extract_mermaid_code(self, response: str) -> Optional[str]:
        """從回應中提取 Mermaid 代碼"""
        # 1. 嘗試匹配 ```mermaid ... ```
        mermaid_pattern = r'```mermaid\s*([\s\S]*?)\s*```'
        matches = re.findall(mermaid_pattern, response)
        if matches:
            return self._fix_newlines(matches[0].strip())
        
        # 2. 嘗試從 JSON 中提取 mermaid_code 欄位
        try:
            json_data = self._parse_json_response(response)
            if isinstance(json_data, dict):
                code = json_data.get("mermaid_code", json_data.get("code", ""))
                if code and any(kw in code.lower() for kw in ['flowchart', 'graph', 'sequencediagram', 'erdiagram']):
                    return self._fix_newlines(code)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # 3. 嘗試匹配一般代碼塊
        code_pattern = r'```\s*([\s\S]*?)\s*```'
        matches = re.findall(code_pattern, response)
        for match in matches:
            if any(kw in match.lower() for kw in ['flowchart', 'graph', 'sequencediagram']):
                return self._fix_newlines(match.strip())
        return None
    
    def _fix_newlines(self, code: str) -> str:
        """
        修正 LLM 回傳的換行符號
        
        LLM 在 JSON 中可能回傳:
        - "\\n" -> 解析後變成字面 "\n" 兩字元 (錯誤)
        - "\n" -> 解析後變成真正換行 (正確)
        
        此方法將字面的 "\n" 轉換為真正的換行符
        """
        # 將字面的 \n (兩個字元) 轉換為真正的換行
        # 注意: 需要處理 \r\n 和 \n 兩種情況
        code = code.replace('\\\\', '\\')  # \\ -> \
        code = code.replace('\\r\\n', '\n')  # Windows 換行
        code = code.replace('\\n', '\n')      # Unix 換行
        code = code.replace('\\t', '    ')    # Tab 轉空格
        code = code.replace('\\"', '\"')    # 引號轉換
        return code
    
    @property
    def code_history(self) -> List[MermaidCode]:
        return self._code_history.copy()
    
    def clear_history(self):
        """清除代碼歷史"""
        self._code_history.clear()
