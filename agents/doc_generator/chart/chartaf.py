"""
CHARTAF - Chart Auto-Feedback System

基於 C2 論文 (NAACL 2025) 的簡化架構：
- 大模型 (120b) 根據圖表類型動態生成評估問題
- VLM (gemma) 逐一回答二元問題
- 生成 Granular Feedback (RETAIN/EDIT/DISCARD/ADD)

改進：
- 問題由大模型根據圖表類型動態生成
- VLM 只負責看圖回答 YES/NO
- 支援 async 平行處理

架構：
- QuestionGenerator: 使用大模型生成評估問題
- VisualInspector: 使用 VLM 回答二元問題
- ChartAF: 組合以上兩者，執行完整評估流程
"""
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from config.settings import get_config
from agents.base import BaseAgent
from models import VisualFeedback, FeedbackType, TPAAnalysis, StructureLogic
from utils.image_utils import encode_image_base64


@dataclass
class EvaluationQuestion:
    """評估問題定義"""
    id: int
    category: str
    question: str
    focus_points: str  # 該問題要檢查的重點


@dataclass 
class EvaluationResult:
    """評估結果"""
    id: int
    category: str
    question: str
    answer: bool  # True = YES, False = NO
    issue: str
    fix: str


@dataclass
class ChartAFResult:
    """CHARTAF 完整評估結果"""
    score: float  # 0.0 - 1.0
    is_approved: bool
    evaluations: List[EvaluationResult]
    feedback: VisualFeedback
    raw_data: Dict[str, Any]


# ==================== QuestionGenerator ====================

class QuestionGenerator(BaseAgent):
    """
    問題生成器
    
    使用大模型 (120b) 根據圖表類型動態生成評估問題
    僅支援 async 模式
    """
    
    PROMPT_NAME = "doc_generator/chartaf_question_generator"
    
    def __init__(self, model: Optional[str] = None):
        config = get_config()
        super().__init__(
            name="QuestionGenerator",
            model=model or config.models.project_analyzer,
            think=False
        )
    
    async def generate(
        self,
        diagram_type: str,
        user_request: str,
        design_spec: Optional[Dict[str, Any]] = None
    ) -> List[EvaluationQuestion]:
        """
        根據圖表設計規格生成確認問題 (async only)
        
        Args:
            diagram_type: 圖表類型 (flowchart, sequence, class, etc.)
            user_request: 使用者原始請求
            design_spec: Designer 產生的設計規格 (StructureLogic.to_dict())
            
        Returns:
            List[EvaluationQuestion]: 生成的確認問題列表
        """
        self.log(f"Generating confirmation questions for {diagram_type}...")
        
        # 準備設計規格摘要
        design_summary = self._format_design_spec(design_spec) if design_spec else "No design spec provided"
        
        try:
            # 使用 BaseAgent 的 chat_async 方法
            response = await self.chat_async(
                prompt_name=self.PROMPT_NAME,
                variables={
                    "diagram_type": diagram_type,
                    "user_request": user_request,
                    "design_spec": design_summary
                },
                keep_history=False
            )
            
            # 解析回應
            response_content = response.message.content
            result = self.parse_json(response_content)
            questions_data = result.get("questions", [])
            
            if not questions_data:
                raise ValueError("No questions in response")
            
            questions = []
            for i, q in enumerate(questions_data, 1):
                questions.append(EvaluationQuestion(
                    id=i,
                    category="auto",
                    question=q.get("question", ""),
                    focus_points=q.get("focus", "")
                ))
            
            self.log(f"Generated {len(questions)} questions")
            return questions
            
        except Exception as e:
            self.log(f"Failed to parse questions: {e}")
            self.log("Using fallback questions")
            return self._generate_fallback_questions(design_spec)
    
    def _format_design_spec(self, design_spec: Dict[str, Any]) -> str:
        """將設計規格格式化為易讀的摘要，包含連接模式分析"""
        lines = []
        
        # 圖表基本資訊
        diagram_type = design_spec.get("diagram_type", "unknown")
        direction = design_spec.get("direction", "TD")
        lines.append(f"Diagram Type: {diagram_type}")
        lines.append(f"Direction: {direction}")
        
        # 節點資訊
        nodes = design_spec.get("nodes", [])
        lines.append(f"\nNodes ({len(nodes)} total):")
        for node in nodes:
            node_id = node.get("id", "?")
            label = node.get("label", "?")
            node_type = node.get("type", "process")
            shape = node.get("shape", "rectangle")
            lines.append(f"  - {node_id}: \"{label}\" (type={node_type}, shape={shape})")
        
        # 邊資訊 - 分析連接模式
        edges = design_spec.get("edges", [])
        
        # 計算 fan-out (1對多) 和 fan-in (多對1) 模式
        from_counts: Dict[str, List[str]] = {}  # from_node -> [to_nodes]
        to_counts: Dict[str, List[str]] = {}    # to_node -> [from_nodes]
        
        for edge in edges:
            from_node = edge.get("from", "")
            to_node = edge.get("to", "")
            
            if from_node not in from_counts:
                from_counts[from_node] = []
            from_counts[from_node].append(to_node)
            
            if to_node not in to_counts:
                to_counts[to_node] = []
            to_counts[to_node].append(from_node)
        
        # 識別 fan-out 節點 (1對多)
        fanout_nodes = {k: v for k, v in from_counts.items() if len(v) > 1}
        # 識別 fan-in 節點 (多對1)
        fanin_nodes = {k: v for k, v in to_counts.items() if len(v) > 1}
        
        # 計算實際連接數（每個邊代表一條連接線）
        total_connections = len(edges)
        
        lines.append(f"\nConnections ({total_connections} edges):")
        
        # 顯示 fan-out 模式
        if fanout_nodes:
            lines.append(f"  Fan-out patterns (1-to-many):")
            for from_node, to_nodes in fanout_nodes.items():
                lines.append(f"    - {from_node} -> [{', '.join(to_nodes)}] ({len(to_nodes)} targets)")
        
        # 顯示 fan-in 模式  
        if fanin_nodes:
            lines.append(f"  Fan-in patterns (many-to-1):")
            for to_node, from_nodes in fanin_nodes.items():
                lines.append(f"    - [{', '.join(from_nodes)}] -> {to_node} ({len(from_nodes)} sources)")
        
        # 顯示所有邊
        lines.append(f"  All edges:")
        for edge in edges:
            from_node = edge.get("from", "?")
            to_node = edge.get("to", "?")
            edge_label = edge.get("label", "")
            if edge_label:
                lines.append(f"    - {from_node} --\"{edge_label}\"--> {to_node}")
            else:
                lines.append(f"    - {from_node} --> {to_node}")
        
        # 樣式資訊
        styling = design_spec.get("styling", {})
        if styling:
            lines.append(f"\nStyling: {styling}")
        
        return "\n".join(lines)
    
    def _generate_fallback_questions(
        self, design_spec: Optional[Dict[str, Any]] = None
    ) -> List[EvaluationQuestion]:
        """根據設計規格生成 fallback 問題"""
        questions = [
            EvaluationQuestion(1, "layout", "Are all elements properly spaced without overlapping?", "Check for overlaps"),
            EvaluationQuestion(2, "text", "Is all text clearly readable?", "Check text clarity"),
            EvaluationQuestion(3, "structure", "Does the diagram have proper flow direction?", "Check flow direction"),
            EvaluationQuestion(4, "completeness", "Are all elements fully visible without cutoff?", "Check for cut-off elements"),
        ]
        
        if design_spec:
            nodes = design_spec.get("nodes", [])
            edges = design_spec.get("edges", [])
            
            # 添加節點數量確認問題
            questions.append(EvaluationQuestion(
                5, "nodes",
                f"Does the diagram contain exactly {len(nodes)} nodes?",
                f"Verify node count matches design: {len(nodes)} nodes"
            ))
            
            # 檢查是否有 diamond/decision 節點
            decision_nodes = [n for n in nodes if n.get("shape") == "diamond" or n.get("type") == "decision"]
            if decision_nodes:
                questions.append(EvaluationQuestion(
                    6, "shapes",
                    f"Are there {len(decision_nodes)} diamond-shaped decision nodes?",
                    f"Verify decision nodes: {[n.get('label') for n in decision_nodes]}"
                ))
            
            # 檢查是否有 fan-out 模式
            from_counts: Dict[str, int] = {}
            for edge in edges:
                from_node = edge.get("from", "")
                from_counts[from_node] = from_counts.get(from_node, 0) + 1
            
            fanout_nodes = [k for k, v in from_counts.items() if v > 1]
            if fanout_nodes:
                questions.append(EvaluationQuestion(
                    len(questions) + 1, "fanout",
                    "Are fan-out patterns (one node to multiple nodes) rendered correctly?",
                    f"Check fan-out from nodes: {fanout_nodes}"
                ))
        
        return questions


# ==================== VisualInspector ====================

class VisualInspector(BaseAgent):
    """
    視覺檢查器
    
    使用 VLM 逐一回答二元問題（YES/NO）
    支援 async 平行處理
    """
    
    PROMPT_NAME = "doc_generator/chartaf_single_question"
    
    def __init__(self, model: Optional[str] = None):
        config = get_config()
        super().__init__(
            name="VisualInspector",
            model=model or config.models.visual_inspector,
            think=False  # VLM 不支援 thinking
        )
    
    async def evaluate_question(
        self,
        diagram_type: str,
        question: EvaluationQuestion,
        image_base64: str
    ) -> EvaluationResult:
        """
        評估單一問題
        
        Args:
            diagram_type: 圖表類型
            question: 評估問題
            image_base64: Base64 編碼的圖片
            
        Returns:
            EvaluationResult: 評估結果
        """
        try:
            response = await self.chat_async(
                prompt_name=self.PROMPT_NAME,
                variables={
                    "diagram_type": diagram_type,
                    "question": question.question,
                    "focus_points": question.focus_points
                },
                images=[image_base64],
                keep_history=False
            )
            
            # 解析回應：找第一個 YES 或 NO
            response_text = response.message.content.strip()
            response_upper = response_text.upper()
            
            # 找第一個 YES 或 NO 的位置
            yes_pos = response_upper.find("YES")
            no_pos = response_upper.find("NO")
            
            # 判斷答案（以先出現者為準）
            if yes_pos == -1 and no_pos == -1:
                answer = False
            elif yes_pos == -1:
                answer = False
            elif no_pos == -1:
                answer = True
            else:
                answer = yes_pos < no_pos
            
            # 提取修改建議（NO 後面的內容）
            fix_suggestion = ""
            if not answer and no_pos != -1:
                fix_suggestion = response_text[no_pos + 2:].lstrip(": -,\n")
                if not fix_suggestion:
                    fix_suggestion = question.focus_points
            
            return EvaluationResult(
                id=question.id,
                category=question.category,
                question=question.question,
                answer=answer,
                issue=question.question if not answer else "",
                fix=fix_suggestion
            )
            
        except Exception as e:
            return EvaluationResult(
                id=question.id,
                category=question.category,
                question=question.question,
                answer=False,
                issue=f"Evaluation error: {e}",
                fix=""
            )
    
    async def evaluate_all(
        self,
        diagram_type: str,
        questions: List[EvaluationQuestion],
        image_base64: str
    ) -> List[EvaluationResult]:
        """
        平行評估所有問題
        
        Args:
            diagram_type: 圖表類型
            questions: 評估問題列表
            image_base64: Base64 編碼的圖片
            
        Returns:
            List[EvaluationResult]: 評估結果列表
        """
        self.log(f"Evaluating {len(questions)} questions in parallel...")
        
        tasks = [
            self.evaluate_question(diagram_type, q, image_base64)
            for q in questions
        ]
        results = await asyncio.gather(*tasks)
        
        # 按 id 排序並印出結果
        results = sorted(results, key=lambda r: r.id)
        for r in results:
            answer_text = "YES" if r.answer else "NO"
            self.log(f"  Q{r.id}: {r.question[:40]}... -> {answer_text}")
        
        return results


# ==================== ChartAF ====================

class ChartAF:
    """
    CHARTAF - Chart Auto-Feedback
    
    組合 QuestionGenerator 和 VisualInspector，執行完整評估流程：
    1. 大模型 (120b) 根據圖表類型動態生成評估問題
    2. VLM (gemma) 逐一看圖回答二元問題
    3. 生成可操作的修改建議
    """
    
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
        "notation": FeedbackType.STYLE_ISSUE,
        "text": FeedbackType.UNREADABLE,
        "completeness": FeedbackType.CUTOFF,
        "appropriateness": FeedbackType.OTHER,
        "approved": FeedbackType.APPROVED,
        "other": FeedbackType.OTHER
    }
    
    # 通過閾值
    APPROVAL_THRESHOLD = 0.8
    
    def __init__(
        self,
        vlm_model: Optional[str] = None,
        question_generator_model: Optional[str] = None
    ):
        self.question_generator = QuestionGenerator(model=question_generator_model)
        self.visual_inspector = VisualInspector(model=vlm_model)
        self._eval_history: List[ChartAFResult] = []
    
    def log(self, message: str) -> None:
        """輸出日誌"""
        print(f"[ChartAF] {message}")
    
    async def evaluate(
        self,
        user_request: str,
        tpa: TPAAnalysis,
        mermaid_code: str,
        structure: Optional[StructureLogic] = None,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None
    ) -> VisualFeedback:
        """
        執行 CHARTAF 評估流程 (async only)
        
        1. 大模型 (120b) 根據設計規格生成確認問題
        2. VLM (gemma) 平行回答所有問題
        
        Args:
            user_request: 原始使用者請求
            tpa: TPA 分析結果
            mermaid_code: Mermaid 代碼
            structure: Designer 產生的結構邏輯（用於生成確認問題）
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
        
        diagram_type = tpa.task_type
        design_spec = structure.to_dict() if structure else None
        
        # Step 1: 使用 QuestionGenerator 生成確認問題 (async)
        questions = await self.question_generator.generate(diagram_type, user_request, design_spec)
        
        # Step 2: 使用 VisualInspector 平行回答所有二元問題
        self.log(f"VLM evaluating {diagram_type} with {len(questions)} questions (parallel)...")
        evaluations = await self.visual_inspector.evaluate_all(diagram_type, questions, image_base64)
        
        # 計算分數
        yes_count = sum(1 for e in evaluations if e.answer)
        score = yes_count / len(evaluations) if evaluations else 0.0
        is_approved = score >= self.APPROVAL_THRESHOLD
        
        self.log(f"Evaluation score: {score:.2f} ({yes_count}/{len(evaluations)}), approved: {is_approved}")
        
        # Step 3: 生成 Granular Feedback
        self.log("Generating granular feedback...")
        eval_result = self._build_eval_result(evaluations, score)
        feedback = self._generate_feedback(
            user_request, mermaid_code, eval_result, is_approved
        )
        
        # 組合結果並記錄
        chartaf_result = ChartAFResult(
            score=score,
            is_approved=is_approved,
            evaluations=evaluations,
            feedback=feedback,
            raw_data=eval_result
        )
        self._eval_history.append(chartaf_result)
        
        # 印出詳細評估結果
        self._print_evaluation_report(chartaf_result, eval_result)
        
        return feedback
    
    def _build_eval_result(
        self,
        evaluations: List[EvaluationResult],
        score: float
    ) -> Dict[str, Any]:
        """將評估結果轉為字典格式"""
        return {
            "evaluations": [
                {
                    "id": e.id,
                    "category": e.category,
                    "question": e.question,
                    "answer": "YES" if e.answer else "NO",
                    "issue": e.issue,
                    "fix": e.fix
                }
                for e in evaluations
            ],
            "score": score,
            "summary": f"Passed {sum(1 for e in evaluations if e.answer)}/{len(evaluations)} checks"
        }
    
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
    
    async def get_score(
        self,
        user_request: str,
        tpa: TPAAnalysis,
        mermaid_code: str,
        image_base64: str,
        structure: Optional[StructureLogic] = None
    ) -> float:
        """CHARTAF-S: 只取得分數 (async)"""
        await self.evaluate(
            user_request, tpa, mermaid_code,
            structure=structure, image_base64=image_base64
        )
        if self._eval_history:
            return self._eval_history[-1].score
        return 0.0
    
    @property
    def eval_history(self) -> List[ChartAFResult]:
        return self._eval_history.copy()
    
    def clear_eval_history(self) -> None:
        self._eval_history.clear()

