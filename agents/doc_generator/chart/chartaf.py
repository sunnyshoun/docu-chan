"""
CHARTAF - Chart Auto-Feedback System

基於 C2 論文 (NAACL 2025) 的簡化架構：
- VLM 直接回答二元問題（減少錯誤傳播）
- 強調圖表結構檢查（流程圖需由上而下有序）
- 生成 Granular Feedback (RETAIN/EDIT/DISCARD/ADD)
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from config.settings import get_config
from agents.base import BaseAgent
from models import VisualFeedback, FeedbackType, TPAAnalysis
from utils.image_utils import encode_image_base64


@dataclass
class EvaluationResult:
    """評估結果"""
    id: int
    question: str
    answer: bool  # True = YES, False = NO
    evidence: str


@dataclass
class ChartAFResult:
    """CHARTAF 完整評估結果"""
    score: float  # 0.0 - 1.0
    is_approved: bool
    evaluations: List[EvaluationResult]
    feedback: VisualFeedback
    raw_data: Dict[str, Any]


class ChartAF(BaseAgent):
    """
    CHARTAF - Chart Auto-Feedback
    
    簡化架構（方案 A）：
    1. VLM 直接看圖回答二元問題（減少錯誤傳播）
    2. 根據 TPA 生成針對性評估問題
    3. 生成可操作的修改建議
    """
    
    PROMPT_EVALUATE = "doc_generator/chartaf_visual_eval"
    PROMPT_FEEDBACK = "doc_generator/chartaf_feedback"
    
    # 問題類型映射
    ISSUE_TYPE_MAP = {
        "structure": FeedbackType.LAYOUT_ISSUE,
        "overlap": FeedbackType.OVERLAP,
        "cutoff": FeedbackType.CUTOFF,
        "unreadable": FeedbackType.UNREADABLE,
        "layout": FeedbackType.LAYOUT_ISSUE,
        "layout_issue": FeedbackType.LAYOUT_ISSUE,
        "style": FeedbackType.STYLE_ISSUE,
        "style_issue": FeedbackType.STYLE_ISSUE,
        "approved": FeedbackType.APPROVED,
        "other": FeedbackType.OTHER
    }
    
    # 通過閾值
    APPROVAL_THRESHOLD = 0.8
    
    def __init__(
        self,
        vlm_model: Optional[str] = None,
        evaluator_model: Optional[str] = None
    ):
        config = get_config()
        super().__init__(
            name="ChartAF",
            model=vlm_model or config.models.visual_inspector,
            think=False  # VLM 不支援 thinking
        )
        self.vlm_model = vlm_model or config.models.visual_inspector
        self.evaluator_model = evaluator_model or config.models.diagram_designer
        self._eval_history: List[ChartAFResult] = []
    
    def evaluate(
        self,
        user_request: str,
        tpa: TPAAnalysis,
        mermaid_code: str,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None
    ) -> VisualFeedback:
        """
        執行 CHARTAF 評估流程
        
        Args:
            user_request: 原始使用者請求
            tpa: TPA 分析結果
            mermaid_code: Mermaid 代碼
            image_path: 圖片路徑 (二選一)
            image_base64: Base64 編碼的圖片 (二選一)
        
        Returns:
            VisualFeedback: 視覺反饋
        """
        # 讀取圖片
        if image_base64 is None and image_path:
            image_base64 = encode_image_base64(image_path)
        
        if image_base64 is None:
            raise ValueError("No image provided")
        
        # Step 1: VLM 直接評估圖片（回答二元問題）
        self.log("Evaluating chart with VLM (binary questions)...")
        eval_result = self._evaluate_with_vlm(tpa, mermaid_code, image_base64)
        
        score = eval_result.get("score", 0.0)
        is_approved = score >= self.APPROVAL_THRESHOLD
        
        self.log(f"Evaluation score: {score:.2f}, approved: {is_approved}")
        
        # Step 2: 生成 Granular Feedback
        self.log("Generating granular feedback...")
        feedback = self._generate_feedback(
            user_request, mermaid_code, eval_result, is_approved
        )
        
        # 組合結果並記錄
        chartaf_result = ChartAFResult(
            score=score,
            is_approved=is_approved,
            evaluations=self._parse_evaluations(eval_result),
            feedback=feedback,
            raw_data=eval_result
        )
        self._eval_history.append(chartaf_result)
        
        # 印出詳細評估結果
        self._print_evaluation_report(chartaf_result, eval_result)
        
        return feedback
    
    def _print_evaluation_report(
        self,
        result: ChartAFResult,
        raw_eval: Dict[str, Any]
    ) -> None:
        """印出詳細的評估報告"""
        print("\n" + "=" * 60)
        print("  CHARTAF Evaluation Report")
        print("=" * 60)
        
        # 總分
        status = "APPROVED" if result.is_approved else "NEEDS REVISION"
        symbol = "[v]" if result.is_approved else "[x]"
        print(f"\n  Score: {result.score:.2f} / 1.00  {symbol} {status}")
        print(f"  Threshold: {self.APPROVAL_THRESHOLD}")
        
        # 各項評估
        print("\n  Evaluation Details:")
        print("  " + "-" * 56)
        
        for item in raw_eval.get("evaluations", []):
            q_id = item.get("id", "?")
            category = item.get("category", "unknown").upper()
            answer = item.get("answer", "?")
            question = item.get("question", "")
            
            # 截斷問題文字
            if len(question) > 35:
                question = question[:35] + "..."
            
            # 根據答案選擇符號
            if answer.upper() == "YES":
                mark = "[v]"
                answer_text = "YES"
            else:
                mark = "[x]"
                answer_text = "NO"
            
            print(f"  [{q_id}] {mark} [{category:10}] {question:<38} -> {answer_text}")
            
            # 如果是 NO，顯示問題和建議
            if answer.upper() == "NO":
                issue = item.get("issue", "")
                fix = item.get("fix", "")
                if issue:
                    issue_text = issue[:55] + "..." if len(issue) > 55 else issue
                    print(f"       Issue: {issue_text}")
                if fix:
                    fix_text = fix[:55] + "..." if len(fix) > 55 else fix
                    print(f"       Fix:   {fix_text}")
        
        # 總結
        summary = raw_eval.get("summary", "")
        if summary:
            print(f"\n  Summary: {summary}")
        
        # 最終反饋（僅當不通過時）
        if not result.is_approved:
            print("\n  Feedback to Coder:")
            print("  " + "-" * 56)
            
            if result.feedback.issues:
                print("  Issues:")
                for i, issue in enumerate(result.feedback.issues[:3], 1):
                    issue_text = issue[:65] + "..." if len(issue) > 65 else issue
                    print(f"    {i}. {issue_text}")
            
            if result.feedback.suggestions:
                print("  Suggestions:")
                for i, sug in enumerate(result.feedback.suggestions[:3], 1):
                    sug_text = sug[:65] + "..." if len(sug) > 65 else sug
                    print(f"    {i}. {sug_text}")
        
        print("\n" + "=" * 60 + "\n")
    
    def _evaluate_with_vlm(
        self,
        tpa: TPAAnalysis,
        mermaid_code: str,
        image_base64: str
    ) -> Dict[str, Any]:
        """VLM 直接看圖回答二元問題"""
        response = self.chat(
            prompt_name=self.PROMPT_EVALUATE,
            variables={
                "tpa_analysis": tpa.to_dict(),
                "diagram_type": tpa.task_type,
                "mermaid_code": mermaid_code
            },
            images=[image_base64],
            keep_history=False  # 評估不需要保留歷史
        )
        
        return self.parse_json(response.message.content)
    
    def _generate_feedback(
        self,
        user_request: str,
        mermaid_code: str,
        evaluation: Dict[str, Any],
        is_approved: bool
    ) -> VisualFeedback:
        """生成可操作的反饋"""
        
        # 從評估結果提取問題
        issues = []
        suggestions = []
        feedback_type = FeedbackType.APPROVED if is_approved else FeedbackType.LAYOUT_ISSUE
        
        for item in evaluation.get("evaluations", []):
            if item.get("answer", "").upper() == "NO":
                issue = item.get("issue", item.get("question", ""))
                if issue:
                    issues.append(issue)
                
                fix = item.get("fix", item.get("suggestion", ""))
                if fix:
                    suggestions.append(fix)
                
                # 判斷問題類型
                category = item.get("category", "").lower()
                if category in self.ISSUE_TYPE_MAP:
                    feedback_type = self.ISSUE_TYPE_MAP[category]
        
        # 如果沒有具體建議，使用通用建議
        if not suggestions and not is_approved:
            suggestions = [
                "Reorganize layout to follow top-to-bottom flow",
                "Reduce crossing edges",
                "Group related nodes together"
            ]
        
        return VisualFeedback(
            is_approved=is_approved,
            feedback_type=feedback_type,
            issues=issues,
            suggestions=suggestions,
            confidence=evaluation.get("score", 0.5),
            raw_data=evaluation
        )
    
    def _parse_evaluations(self, eval_result: Dict[str, Any]) -> List[EvaluationResult]:
        """解析評估結果"""
        results = []
        for item in eval_result.get("evaluations", []):
            results.append(EvaluationResult(
                id=item.get("id", len(results) + 1),
                question=item.get("question", ""),
                answer=item.get("answer", "").upper() == "YES",
                evidence=item.get("evidence", item.get("issue", ""))
            ))
        return results
    
    def get_score(
        self,
        user_request: str,
        tpa: TPAAnalysis,
        mermaid_code: str,
        image_base64: str
    ) -> float:
        """CHARTAF-S: 只取得分數"""
        feedback = self.evaluate(user_request, tpa, mermaid_code, image_base64=image_base64)
        if self._eval_history:
            return self._eval_history[-1].score
        return 0.0
    
    @property
    def eval_history(self) -> List[ChartAFResult]:
        return self._eval_history.copy()
    
    def clear_eval_history(self) -> None:
        self._eval_history.clear()

