"""Chart Loop Controller - 協調整個圖表生成流程"""
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from agents.context import AgentContext
from models import (
    TPAAnalysis, StructureLogic, MermaidCode,
    VisualFeedback, FeedbackType, ChartResult
)
from utils.file_utils import ensure_dir

from .designer import DiagramDesigner
from .coder import MermaidCoder
from .executor import CodeExecutor
from .chartaf import ChartAF


class ChartLoop:
    """
    圖表生成迴圈控制器
    
    流程：Designer → Coder → Executor → ChartAF (→ Coder)
    
    使用 CHARTAF (C2 論文) 進行視覺檢查：
    - Module 1: TPA + Basic Criteria (Domain Grounding)
    - Module 2: Query-Specific 二元問題評估
    - Module 3: Granular Feedback (RETAIN/EDIT/DISCARD/ADD)
    """
    
    MAX_VISUAL_ITERATIONS = 3
    MAX_RENDER_RETRIES = 4
    
    def __init__(
        self,
        log_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        max_iterations: int = 5,
        designer_model: Optional[str] = None,
        coder_model: Optional[str] = None,
        evaluator_model: Optional[str] = None,
        vlm_model: str = "gemma3:4b"
    ):
        self.max_iterations = max_iterations
        
        # 路徑配置
        self.log_dir = Path(log_dir) if log_dir else Path("logs/phase3/charts")
        self.output_dir = Path(output_dir) if output_dir else Path("outputs/final/diagrams")
        ensure_dir(self.log_dir)
        ensure_dir(self.output_dir)
        
        # 初始化各組件（使用共用 AgentContext）
        self.designer = DiagramDesigner(model=designer_model)
        self.coder = MermaidCoder(model=coder_model)
        self.executor = CodeExecutor(output_dir=str(self.log_dir))
        
        # CHARTAF 視覺檢查器 (C2 架構)
        self.chartaf = ChartAF(
            vlm_model=vlm_model,
            evaluator_model=evaluator_model or "gpt-oss:20b"
        )
        
        self._current_result: Optional[ChartResult] = None
        self._session_log: List[Dict[str, Any]] = []
        self._session_id: Optional[str] = None
    
    def run(
        self,
        user_request: str,
        output_name: Optional[str] = None,
        skip_inspection: bool = False,
        **kwargs
    ) -> ChartResult:
        """執行圖表生成迴圈"""
        # 建立 session ID 和日誌目錄
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = self.log_dir / self._session_id
        ensure_dir(session_dir)
        self._session_log = []
        
        print(f"\n{'='*60}")
        print("Chart Generation Loop Started")
        print(f"{'='*60}")
        print(f"Request: {user_request[:100]}...")
        
        feedback_history: List[VisualFeedback] = []
        
        # Step 1: Design
        print("\n[Step 1] Designing chart structure...")
        design_result = self.designer.execute(user_request)
        
        if not design_result.success:
            return ChartResult(success=False, error=f"Design failed: {design_result.error}")
        
        tpa: TPAAnalysis = design_result.data["tpa"]
        structure: StructureLogic = design_result.data["structure"]
        
        print(f"  ✓ TPA Analysis: {tpa.task_type}")
        print(f"  ✓ Structure: {structure.node_count} nodes, {structure.edge_count} edges")
        
        current_code: Optional[MermaidCode] = None
        current_feedback: Optional[VisualFeedback] = None
        final_image_path: Optional[str] = None
        final_image_base64: Optional[str] = None
        
        visual_iterations = 0  # 視覺檢查次數（限制為 MAX_VISUAL_ITERATIONS）
        render_attempts = 0  # 渲染嘗試次數
        max_render_attempts = self.MAX_RENDER_RETRIES * 2  # 防止無限迴圈
        
        while visual_iterations < self.MAX_VISUAL_ITERATIONS and render_attempts < max_render_attempts:
            render_attempts += 1
            print(f"\n[Iteration {visual_iterations + 1}/{self.MAX_VISUAL_ITERATIONS}] (attempt {render_attempts})")
            
            # Step 2: Generate/Revise Code
            if current_code is None:
                print("  [Step 2] Generating Mermaid code...")
                code_result = self.coder.generate(structure)
            else:
                print("  [Step 2] Revising Mermaid code based on feedback...")
                code_result = self.coder.revise(structure, current_code.code, current_feedback)
            
            if not code_result.success:
                print(f"  ✗ Code generation failed: {code_result.error}")
                # 檢查是否重複失敗
                if self._is_repeated_error(feedback_history, code_result.error):
                    print("  ⚠ Repeated code generation error, simplifying approach...")
                    # 簡化反饋，要求更簡單的圖表
                    current_feedback = VisualFeedback(
                        is_approved=False,
                        feedback_type=FeedbackType.OTHER,
                        issues=["Previous attempts failed repeatedly"],
                        suggestions=[
                            "Simplify the diagram significantly",
                            "Use fewer nodes (max 8-10)",
                            "Avoid subgraphs",
                            "Use shorter labels (max 15 chars)"
                        ]
                    )
                else:
                    current_feedback = VisualFeedback(
                        is_approved=False,
                        feedback_type=FeedbackType.OTHER,
                        issues=[f"Code generation error: {code_result.error}"],
                        suggestions=["Simplify the structure", "Try a different approach"]
                    )
                feedback_history.append(current_feedback)
                continue
            
            current_code = code_result.data
            print(f"  ✓ Code generated (version {current_code.version})")
            
            # Step 3: Render
            print("  [Step 3] Rendering to PNG...")
            render_name = f"{output_name or 'chart'}_{render_attempts}" if render_attempts > 1 else output_name
            render_result = self.executor.render(current_code.code, output_name=render_name)
            
            if not render_result.success:
                # 簡化錯誤訊息，只保留關鍵部分
                print(render_result.error)
                short_error = self._extract_error_message(render_result.error)
                print(f"  ✗ Render failed: {short_error}")
                
                current_feedback = VisualFeedback(
                    is_approved=False,
                    feedback_type=FeedbackType.OTHER,
                    issues=[short_error],
                    suggestions=[
                        "Wrap all labels in double quotes",
                        "Remove special characters from labels",
                        "Ensure node IDs don't use reserved words (end, graph, subgraph)"
                    ]
                )
                feedback_history.append(current_feedback)
                # Render 失敗不計入視覺迭代次數，直接繼續
                continue
            
            # Render 成功，進行視覺檢查
            visual_iterations += 1
            
            final_image_path = render_result.image_path
            final_image_base64 = render_result.image_base64
            print(f"  ✓ Rendered: {final_image_path}")
            
            # Step 4: CHARTAF Inspection (optional)
            if skip_inspection:
                print("  [Step 4] Skipping visual inspection")
                break
            
            print("  [Step 4] CHARTAF evaluation (C2 framework)...")
            inspect_result = self.chartaf.evaluate(
                user_request=user_request,
                tpa=tpa,
                mermaid_code=current_code.code,
                image_base64=final_image_base64
            )
            
            if not inspect_result.success:
                print(f"  ⚠ CHARTAF evaluation failed: {inspect_result.error}")
                break
            
            current_feedback = inspect_result.data
            feedback_history.append(current_feedback)
            
            # 顯示 CHARTAF 分數
            score = inspect_result.metadata.get("score", 0.0)
            print(f"  📊 CHARTAF Score: {score:.2f}")
            
            if current_feedback.is_approved:
                print("  ✓ Chart approved!")
                break
            else:
                print(f"  ✗ Issues found: {current_feedback.feedback_type.value}")
                for issue in current_feedback.issues[:3]:  # 最多顯示 3 個
                    print(f"    - {issue}")
                
                # 檢查是否重複相同問題（無效迴圈）
                if self._is_repeated_feedback(feedback_history, current_feedback):
                    print("  ⚠ Similar issues repeated, accepting current result...")
                    break
        
        if visual_iterations >= self.MAX_VISUAL_ITERATIONS:
            print(f"\n  ⚠ Max visual iterations ({self.MAX_VISUAL_ITERATIONS}) reached, outputting best result...")
        
        # 判斷成功條件：有產出圖片即可，不強制要求 approved
        has_output = current_code is not None and final_image_path is not None
        is_approved = skip_inspection or (feedback_history and feedback_history[-1].is_approved)
        
        # 複製最終圖片到 output_dir
        final_output_path = None
        if has_output and final_image_path:
            final_output_path = self._copy_to_output(final_image_path, output_name)
        
        result = ChartResult(
            success=has_output,  # 只要有輸出就算成功
            tpa=tpa,
            structure=structure,
            mermaid_code=current_code,
            image_path=str(final_output_path) if final_output_path else final_image_path,
            image_base64=final_image_base64,
            iterations=visual_iterations,
            feedback_history=feedback_history,
            error=None if has_output else "Failed to generate chart"
        )
        
        self._current_result = result
        
        # 儲存 session 日誌
        self._save_session_log(result, user_request)
        
        status = "Completed" if is_approved else ("Completed (with issues)" if has_output else "Failed")
        print(f"\n{'='*60}")
        print(f"Chart Generation {status}")
        if final_output_path:
            print(f"Output: {final_output_path}")
        print(f"{'='*60}\n")
        
        return result
    
    def _log_step(self, step: str, data: Dict[str, Any]):
        """記錄步驟到 session log"""
        self._session_log.append({
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "data": data
        })
    
    def _copy_to_output(self, source_path: str, output_name: Optional[str]) -> Path:
        """複製最終圖片到 output_dir"""
        source = Path(source_path)
        if output_name:
            dest_name = f"{output_name}{source.suffix}"
        else:
            dest_name = source.name
        
        dest = self.output_dir / dest_name
        ensure_dir(self.output_dir)
        shutil.copy2(source, dest)
        print(f"  ✓ Final output saved: {dest}")
        return dest
    
    def _save_session_log(self, result: ChartResult, user_request: str):
        """儲存完整的 session 日誌"""
        if not self._session_id:
            return
        
        session_dir = self.log_dir / self._session_id
        
        # 儲存對話紀錄
        log_data = {
            "session_id": self._session_id,
            "timestamp": datetime.now().isoformat(),
            "user_request": user_request,
            "success": result.success,
            "iterations": result.iterations,
            "steps": self._session_log,
            "tpa": result.tpa.to_dict() if result.tpa else None,
            "structure": result.structure.to_dict() if result.structure else None,
            "mermaid_code": result.mermaid_code.code if result.mermaid_code else None,
            "feedback_history": [
                {
                    "is_approved": f.is_approved,
                    "feedback_type": f.feedback_type.value,
                    "issues": f.issues,
                    "suggestions": f.suggestions
                }
                for f in result.feedback_history
            ],
            "error": result.error
        }
        
        log_file = session_dir / "session.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        # 儲存 Mermaid 代碼
        if result.mermaid_code:
            code_file = session_dir / "final_code.mmd"
            with open(code_file, "w", encoding="utf-8") as f:
                f.write(result.mermaid_code.code)
        
        print(f"  ✓ Session log saved: {session_dir}")
    
    def _extract_error_message(self, error: str) -> str:
        """從 mmdc 錯誤中提取關鍵資訊"""
        import re
        
        # 尋找 "Error: ..." 開頭的行
        error_match = re.search(r'Error:\s*(.+?)(?:\n|$)', error)
        if error_match:
            error_line = error_match.group(1).strip()
            
            # 提取 "Expecting ... got ..." 模式
            expecting_match = re.search(r"Expecting\s+'([^']+)'.*got\s+'([^']+)'", error_line)
            if expecting_match:
                return f"Syntax error: expected '{expecting_match.group(1)}', got '{expecting_match.group(2)}'"
            
            # 提取 Parse error 行號資訊
            parse_match = re.search(r'Parse error on line (\d+)', error_line)
            if parse_match:
                line_num = parse_match.group(1)
                # 嘗試找出問題的程式碼片段
                snippet_match = re.search(r'\.\.\.(.{10,40})\.\.\.', error_line)
                if snippet_match:
                    return f"Parse error at line {line_num} near: {snippet_match.group(1)}"
                return f"Parse error at line {line_num}"
            
            # 限制長度
            return error_line[:100]
        
        # 回退：取第一行，移除路徑
        first_line = error.split('\n')[0]
        # 移除 Windows/Unix 路徑
        first_line = re.sub(r'[A-Za-z]:\\[^\s]+', '', first_line)
        first_line = re.sub(r'/[^\s]+', '', first_line)
        return first_line.strip()[:100] or "Unknown render error"
    
    def _is_repeated_error(self, feedback_history: List[VisualFeedback], current_error: str) -> bool:
        """檢查是否重複相同錯誤（觸發策略變更）"""
        if not current_error or len(feedback_history) < 2:
            return False
        
        # 提取錯誤關鍵字
        error_keywords = set(current_error.lower().split())
        similar_count = 0
        
        for feedback in feedback_history[-3:]:  # 檢查最近 3 次
            for issue in feedback.issues:
                issue_keywords = set(issue.lower().split())
                # 如果有超過 50% 的關鍵字重複，視為相似錯誤
                overlap = len(error_keywords & issue_keywords)
                if overlap > len(error_keywords) * 0.5:
                    similar_count += 1
                    break
        
        return similar_count >= 2
    
    def _is_repeated_feedback(self, feedback_history: List[VisualFeedback], current_feedback: VisualFeedback) -> bool:
        """檢查是否重複相同視覺問題（超過 2 次則接受當前結果）"""
        if len(feedback_history) < 2:
            return False
        
        current_issues = set(' '.join(current_feedback.issues).lower().split())
        similar_count = 0
        
        for feedback in feedback_history[-2:]:  # 檢查最近 2 次
            past_issues = set(' '.join(feedback.issues).lower().split())
            # 計算相似度
            if current_issues and past_issues:
                overlap = len(current_issues & past_issues)
                similarity = overlap / max(len(current_issues), len(past_issues))
                if similarity > 0.6:  # 60% 相似度
                    similar_count += 1
        
        return similar_count >= 2
