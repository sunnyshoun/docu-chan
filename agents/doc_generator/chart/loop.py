"""Chart Loop Controller - 協調各個圖表生成元件"""
import asyncio
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

from config import config
from models import (
    TPAAnalysis, StructureLogic, MermaidCode,
    VisualFeedback, FeedbackType, ChartResult, ChartTask
)
from utils.file_utils import ensure_dir

from .designer import DiagramDesigner
from .coder import MermaidCoder
from .executor import CodeExecutor
from .chartaf import ChartAF


class ChartLoop:
    """
    圖表生成迴圈控制器
    
    流程：Designer -> Coder -> Executor -> ChartAF (-> Coder)
    
    支援雙 Coder ping-pong 機制修復渲染錯誤。
    """
    
    MAX_VISUAL_ITERATIONS = 3
    MAX_RENDER_RETRIES = 4
    MAX_PING_PONG_ROUNDS = 3
    
    def __init__(
        self,
        log_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        designer_model: Optional[str] = None,
        coder_model: Optional[str] = None,
        coder_model_b: Optional[str] = None,
        evaluator_model: Optional[str] = None,
        vlm_model: Optional[str] = None,
        use_dual_coder: bool = True
    ):
        self.use_dual_coder = use_dual_coder
        self.coder_model_a = coder_model or config.models.mermaid_coder
        self.coder_model_b = coder_model_b or self.coder_model_a
        self.vlm_model = vlm_model or config.models.visual_inspector
        self.evaluator_model = evaluator_model or config.models.visual_inspector
        
        # 路徑配置
        self.log_dir = Path(log_dir) if log_dir else Path("logs/phase3/charts")
        self.output_dir = Path(output_dir) if output_dir else Path("outputs/final/diagrams")
        ensure_dir(self.log_dir)
        ensure_dir(self.output_dir)
        
        # 初始化元件
        self.designer = DiagramDesigner(model=designer_model)
        self.executor = CodeExecutor(output_dir=str(self.log_dir))
        self.chartaf = ChartAF(
            vlm_model=self.vlm_model,
            question_generator_model=self.evaluator_model
        )
        
        self._session_id: Optional[str] = None
    
    def _create_coder(self, coder_id: str = "A") -> MermaidCoder:
        """建立全新的 Coder 實例（乾淨 context）"""
        model = self.coder_model_a if coder_id == "A" else self.coder_model_b
        return MermaidCoder(model=model, name=f"Coder-{coder_id}")
    
    def _ping_pong_fix(
        self,
        structure: StructureLogic,
        broken_code: str,
        error_message: str
    ) -> Tuple[bool, Optional[MermaidCode]]:
        """
        雙 Coder ping-pong 修復機制
        
        流程：A -> B -> A -> B...
        每次修復都建立全新 Coder，避免 context 污染。
        """
        current_code = broken_code
        current_error = error_message
        max_attempts = self.MAX_PING_PONG_ROUNDS * 2  # A 和 B 各 N 次
        
        for attempt in range(max_attempts):
            # A 和 B 交替，0=A, 1=B, 2=A, 3=B...
            coder_id = "A" if attempt % 2 == 0 else "B"
            round_num = attempt // 2 + 1
            
            print(f"    [Coder {coder_id}] Fixing (round {round_num})...")
            
            # 建立全新 Coder
            coder = self._create_coder(coder_id)
            
            try:
                fixed_code = coder.fix_error(structure, current_code, current_error)
            except Exception as e:
                print(f"    [Coder {coder_id}] x {e}")
                # 修復失敗，直接傳給下一個 Coder（不更新 current_code）
                continue
            
            fixed_code_obj = fixed_code
            
            # 嘗試渲染
            render_result = self.executor.render(fixed_code_obj.code, output_name=f"_fix_{attempt}")
            
            if render_result.success:
                print(f"    [Coder {coder_id}] v Fixed!")
                return True, fixed_code_obj
            
            # 渲染失敗，把結果傳給下一個 Coder
            print(f"    [Coder {coder_id}] x Still error, passing to next...")
            current_code = fixed_code_obj.code
            current_error = self._extract_error_message(render_result.error)
        
        print(f"    x Max attempts ({max_attempts}) reached")
        return False, None
    
    def run(
        self,
        user_request: str,
        output_name: Optional[str] = None,
        skip_inspection: bool = False,
        **kwargs
    ) -> ChartResult:
        """執行圖表生成迴圈"""
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = self.log_dir / self._session_id
        ensure_dir(session_dir)
        
        # 設定 executor 輸出到 session_dir
        self.executor.output_dir = session_dir
        
        print(f"\n{'='*60}")
        print("Chart Generation Loop Started")
        print(f"{'='*60}")
        print(f"Request: {user_request[:100]}...")
        print(f"Session: {self._session_id}")
        
        feedback_history: List[VisualFeedback] = []
        
        # Step 1: Design
        print("\n[Step 1] Designing chart structure...")
        
        try:
            design_data = self.designer.execute(user_request)
            tpa: TPAAnalysis = design_data["tpa"]
            structure: StructureLogic = design_data["structure"]
        except Exception as e:
            return ChartResult(success=False, error=f"Design failed: {e}")
        
        print(f"  v TPA: {tpa.task_type}")
        print(f"  v Structure: {structure.node_count} nodes, {structure.edge_count} edges")
        
        current_code: Optional[MermaidCode] = None
        current_feedback: Optional[VisualFeedback] = None
        final_image_path: Optional[str] = None
        final_image_base64: Optional[str] = None
        
        visual_iterations = 0
        render_attempts = 0
        max_attempts = self.MAX_RENDER_RETRIES * 2
        
        while visual_iterations < self.MAX_VISUAL_ITERATIONS and render_attempts < max_attempts:
            render_attempts += 1
            print(f"\n[Iteration {visual_iterations + 1}/{self.MAX_VISUAL_ITERATIONS}] (attempt {render_attempts})")
            
            # Step 2: Generate/Revise Code（每次用全新 Coder）
            coder = self._create_coder("A")
            
            try:
                if current_code is None:
                    print("  [Step 2] Generating Mermaid code...")
                    current_code = coder.generate(structure)
                else:
                    print("  [Step 2] Revising code based on feedback...")
                    current_code = coder.revise(structure, current_code.code, current_feedback)
                print(f"  v Code generated")
            except Exception as e:
                print(f"  x Code generation failed: {e}")
                current_feedback = VisualFeedback(
                    is_approved=False,
                    feedback_type=FeedbackType.OTHER,
                    issues=[f"Code error: {e}"],
                    suggestions=["Simplify the structure"]
                )
                feedback_history.append(current_feedback)
                continue
            
            # Step 3: Render
            print("  [Step 3] Rendering to PNG...")
            attempt_name = f"attempt_{render_attempts}"
            
            # 保存 mermaid 代碼到 session_dir
            self._save_attempt_mmd(current_code.code, render_attempts)
            
            render_result = self.executor.render(current_code.code, output_name=attempt_name)
            
            if not render_result.success:
                short_error = self._extract_error_message(render_result.error)
                print(f"  x Render failed: {short_error}")
                
                # 嘗試 ping-pong 修復
                if self.use_dual_coder:
                    print("  [Step 3.5] Dual Coder ping-pong...")
                    fixed, fixed_code = self._ping_pong_fix(structure, current_code.code, short_error)
                    
                    if fixed and fixed_code:
                        current_code = fixed_code
                        # 保存修復後的代碼
                        self._save_attempt_mmd(current_code.code, render_attempts, suffix="_fixed")
                        render_result = self.executor.render(current_code.code, output_name=f"{attempt_name}_fixed")
                        
                        if render_result.success:
                            visual_iterations += 1
                            final_image_path = render_result.image_path
                            final_image_base64 = render_result.image_base64
                            print(f"  v Rendered: {final_image_path}")
                        else:
                            current_feedback = VisualFeedback(
                                is_approved=False,
                                feedback_type=FeedbackType.OTHER,
                                issues=[self._extract_error_message(render_result.error)],
                                suggestions=["Simplify diagram"]
                            )
                            feedback_history.append(current_feedback)
                            continue
                    else:
                        current_feedback = VisualFeedback(
                            is_approved=False,
                            feedback_type=FeedbackType.OTHER,
                            issues=[short_error],
                            suggestions=["Simplify diagram significantly"]
                        )
                        feedback_history.append(current_feedback)
                        continue
                else:
                    current_feedback = VisualFeedback(
                        is_approved=False,
                        feedback_type=FeedbackType.OTHER,
                        issues=[short_error],
                        suggestions=["Fix syntax error"]
                    )
                    feedback_history.append(current_feedback)
                    continue
            else:
                visual_iterations += 1
                final_image_path = render_result.image_path
                final_image_base64 = render_result.image_base64
                print(f"  v Rendered: {final_image_path}")
            
            # Step 4: CHARTAF Inspection
            if skip_inspection:
                print("  [Step 4] Skipping inspection")
                break
            
            print("  [Step 4] CHARTAF evaluation...")
            
            try:
                current_feedback = asyncio.run(self.chartaf.evaluate(
                    user_request=user_request,
                    tpa=tpa,
                    mermaid_code=current_code.code,
                    structure=structure,
                    image_base64=final_image_base64
                ))
                feedback_history.append(current_feedback)
            except Exception as e:
                print(f"  x Evaluation failed: {e}")
                break
            
            if current_feedback.is_approved:
                print("  v Approved!")
                break
            else:
                print(f"  x Issues: {current_feedback.feedback_type.value}")
                for issue in current_feedback.issues[:2]:
                    print(f"    - {issue}")
                
                if self._is_repeated_feedback(feedback_history):
                    print("  > Repeated issues, accepting...")
                    break
        
        # 結果
        has_output = current_code is not None and final_image_path is not None
        
        final_output_path = None
        if has_output:
            # 保存 final.mmd 和 final.png 到 session_dir
            self._save_final_files(current_code.code, final_image_path)
            # 複製到 output_dir
            final_output_path = self._copy_to_output(final_image_path, current_code.code, output_name)
        
        result = ChartResult(
            success=has_output,
            tpa=tpa,
            structure=structure,
            mermaid_code=current_code,
            image_path=str(final_output_path) if final_output_path else final_image_path,
            image_base64=final_image_base64,
            iterations=visual_iterations,
            feedback_history=feedback_history,
            error=None if has_output else "Failed to generate chart"
        )
        
        self._save_session_log(result, user_request)
        
        status = "Completed" if has_output else "Failed"
        print(f"\n{'='*60}")
        print(f"Chart Generation {status}")
        if final_output_path:
            print(f"Output: {final_output_path}")
        print(f"{'='*60}\n")
        
        return result
    
    def run_from_task(
        self,
        task: ChartTask,
        project_path: str,
        output_name: Optional[str] = None,
        skip_inspection: bool = False
    ) -> ChartResult:
        """
        從 ChartTask 執行圖表生成（新的主要入口）
        
        與 run() 的差異：
        - Designer 會根據 task 的指引自主讀取檔案
        - 使用 execute_from_task() 而非 execute()
        
        Args:
            task: Planner 產生的圖表任務
            project_path: 專案路徑（用於 Designer 讀檔）
            output_name: 輸出檔名
            skip_inspection: 是否跳過視覺檢查
            
        Returns:
            ChartResult: 生成結果
        """
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = self.log_dir / self._session_id
        ensure_dir(session_dir)
        
        self.executor.output_dir = session_dir
        
        print(f"\n{'='*60}")
        print("Chart Generation Loop Started (from Task)")
        print(f"{'='*60}")
        print(f"Task: {task.title}")
        print(f"Type: {task.chart_type.value}")
        print(f"Session: {self._session_id}")
        
        feedback_history: List[VisualFeedback] = []
        
        # Step 1: Design（使用新的 execute_from_task，Designer 會自己讀檔）
        print("\n[Step 1] Designing chart structure...")
        print("  Designer will gather context from source files...")
        
        # 建立帶有專案路徑的 Designer
        designer = DiagramDesigner(project_path=project_path)
        
        try:
            design_data = designer.execute_from_task(task, project_path)
            tpa: TPAAnalysis = design_data["tpa"]
            structure: StructureLogic = design_data["structure"]
            user_request = design_data["user_request"]  # 包含收集到的資訊
            gathered = design_data.get("gathered_context", {})
            
            files_read = len(gathered.get("files_read", []))
            print(f"  v Files read by Designer: {files_read}")
        except Exception as e:
            return ChartResult(success=False, error=f"Design failed: {e}")
        
        print(f"  v TPA: {tpa.task_type}")
        print(f"  v Structure: {structure.node_count} nodes, {structure.edge_count} edges")
        
        # 後續流程與 run() 相同
        current_code: Optional[MermaidCode] = None
        current_feedback: Optional[VisualFeedback] = None
        final_image_path: Optional[str] = None
        final_image_base64: Optional[str] = None
        
        visual_iterations = 0
        render_attempts = 0
        max_attempts = self.MAX_RENDER_RETRIES * 2
        
        while visual_iterations < self.MAX_VISUAL_ITERATIONS and render_attempts < max_attempts:
            render_attempts += 1
            print(f"\n[Iteration {visual_iterations + 1}/{self.MAX_VISUAL_ITERATIONS}] (attempt {render_attempts})")
            
            coder = self._create_coder("A")
            
            try:
                if current_code is None:
                    print("  [Step 2] Generating Mermaid code...")
                    current_code = coder.generate(structure)
                else:
                    print("  [Step 2] Revising code based on feedback...")
                    current_code = coder.revise(structure, current_code.code, current_feedback)
                print(f"  v Code generated")
            except Exception as e:
                print(f"  x Code generation failed: {e}")
                current_feedback = VisualFeedback(
                    is_approved=False,
                    feedback_type=FeedbackType.OTHER,
                    issues=[f"Code error: {e}"],
                    suggestions=["Simplify the structure"]
                )
                feedback_history.append(current_feedback)
                continue
            
            print("  [Step 3] Rendering to PNG...")
            attempt_name = f"attempt_{render_attempts}"
            self._save_attempt_mmd(current_code.code, render_attempts)
            
            render_result = self.executor.render(current_code.code, output_name=attempt_name)
            
            if not render_result.success:
                short_error = self._extract_error_message(render_result.error)
                print(f"  x Render failed: {short_error}")
                
                if self.use_dual_coder:
                    print("  [Step 3.5] Dual Coder ping-pong...")
                    fixed, fixed_code = self._ping_pong_fix(structure, current_code.code, short_error)
                    
                    if fixed and fixed_code:
                        current_code = fixed_code
                        self._save_attempt_mmd(current_code.code, render_attempts, suffix="_fixed")
                        render_result = self.executor.render(current_code.code, output_name=f"{attempt_name}_fixed")
                        
                        if render_result.success:
                            visual_iterations += 1
                            final_image_path = render_result.image_path
                            final_image_base64 = render_result.image_base64
                            print(f"  v Rendered: {final_image_path}")
                        else:
                            current_feedback = VisualFeedback(
                                is_approved=False,
                                feedback_type=FeedbackType.OTHER,
                                issues=[self._extract_error_message(render_result.error)],
                                suggestions=["Simplify diagram"]
                            )
                            feedback_history.append(current_feedback)
                            continue
                    else:
                        current_feedback = VisualFeedback(
                            is_approved=False,
                            feedback_type=FeedbackType.OTHER,
                            issues=[short_error],
                            suggestions=["Simplify diagram significantly"]
                        )
                        feedback_history.append(current_feedback)
                        continue
                else:
                    current_feedback = VisualFeedback(
                        is_approved=False,
                        feedback_type=FeedbackType.OTHER,
                        issues=[short_error],
                        suggestions=["Fix syntax error"]
                    )
                    feedback_history.append(current_feedback)
                    continue
            else:
                visual_iterations += 1
                final_image_path = render_result.image_path
                final_image_base64 = render_result.image_base64
                print(f"  v Rendered: {final_image_path}")
            
            if skip_inspection:
                print("  [Step 4] Skipping inspection")
                break
            
            print("  [Step 4] CHARTAF evaluation...")
            
            try:
                current_feedback = asyncio.run(self.chartaf.evaluate(
                    user_request=user_request,
                    tpa=tpa,
                    mermaid_code=current_code.code,
                    structure=structure,
                    image_base64=final_image_base64
                ))
                feedback_history.append(current_feedback)
            except Exception as e:
                print(f"  x Evaluation failed: {e}")
                break
            
            if current_feedback.is_approved:
                print("  v Approved!")
                break
            else:
                print(f"  x Issues: {current_feedback.feedback_type.value}")
                for issue in current_feedback.issues[:2]:
                    print(f"    - {issue}")
                
                if self._is_repeated_feedback(feedback_history):
                    print("  > Repeated issues, accepting...")
                    break
        
        has_output = current_code is not None and final_image_path is not None
        
        final_output_path = None
        if has_output:
            self._save_final_files(current_code.code, final_image_path)
            final_output_path = self._copy_to_output(final_image_path, current_code.code, output_name or task.title.replace(" ", "_"))
        
        result = ChartResult(
            success=has_output,
            tpa=tpa,
            structure=structure,
            mermaid_code=current_code,
            image_path=str(final_output_path) if final_output_path else final_image_path,
            image_base64=final_image_base64,
            iterations=visual_iterations,
            feedback_history=feedback_history,
            error=None if has_output else "Failed to generate chart"
        )
        
        self._save_session_log(result, f"[Task] {task.title}: {task.description}")
        
        status = "Completed" if has_output else "Failed"
        print(f"\n{'='*60}")
        print(f"Chart Generation {status}")
        if final_output_path:
            print(f"Output: {final_output_path}")
        print(f"{'='*60}\n")
        
        return result
    
    def _save_attempt_mmd(self, mermaid_code: str, attempt_num: int, suffix: str = "") -> None:
        """保存每次嘗試的 mermaid 代碼"""
        if not self._session_id:
            return
        session_dir = self.log_dir / self._session_id
        filename = f"attempt_{attempt_num}{suffix}.mmd"
        with open(session_dir / filename, "w", encoding="utf-8") as f:
            f.write(mermaid_code)
    
    def _save_final_files(self, mermaid_code: str, image_path: str) -> None:
        """保存 final.mmd 和 final.png 到 session_dir"""
        if not self._session_id:
            return
        session_dir = self.log_dir / self._session_id
        
        # 保存 final.mmd
        with open(session_dir / "final.mmd", "w", encoding="utf-8") as f:
            f.write(mermaid_code)
        
        # 複製 final.png
        source = Path(image_path)
        if source.exists():
            shutil.copy2(source, session_dir / f"final{source.suffix}")
    
    def _copy_to_output(self, image_path: str, mermaid_code: str, output_name: Optional[str]) -> Path:
        """複製結果到 output_dir（包含 mmd 和 png）"""
        source = Path(image_path)
        base_name = output_name or "final"
        
        ensure_dir(self.output_dir)
        
        # 複製 png
        png_dest = self.output_dir / f"{base_name}.png"
        shutil.copy2(source, png_dest)
        
        # 保存 mmd
        mmd_dest = self.output_dir / f"{base_name}.mmd"
        with open(mmd_dest, "w", encoding="utf-8") as f:
            f.write(mermaid_code)
        
        print(f"  v Saved: {png_dest}")
        print(f"  v Saved: {mmd_dest}")
        return png_dest
    
    def _save_session_log(self, result: ChartResult, user_request: str):
        """保存 session 紀錄"""
        if not self._session_id:
            return
        
        session_dir = self.log_dir / self._session_id
        log_data = {
            "session_id": self._session_id,
            "timestamp": datetime.now().isoformat(),
            "user_request": user_request,
            "success": result.success,
            "iterations": result.iterations,
            "tpa": result.tpa.to_dict() if result.tpa else None,
            "structure": result.structure.to_dict() if result.structure else None,
            "mermaid_code": result.mermaid_code.code if result.mermaid_code else None,
            "feedback_history": [
                {"is_approved": f.is_approved, "type": f.feedback_type.value, "issues": f.issues}
                for f in result.feedback_history
            ],
            "error": result.error
        }
        
        with open(session_dir / "session.json", "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    def _extract_error_message(self, error: str) -> str:
        """提取關鍵錯誤資訊"""
        match = re.search(r'Error:\s*(.+?)(?:\n|$)', error)
        if match:
            return match.group(1).strip()[:100]
        return error.split('\n')[0][:100] or "Unknown error"
    
    def _is_repeated_feedback(self, history: List[VisualFeedback]) -> bool:
        """檢查是否重複反饋"""
        if len(history) < 2:
            return False
        
        last = set(' '.join(history[-1].issues).lower().split())
        prev = set(' '.join(history[-2].issues).lower().split())
        
        if last and prev:
            overlap = len(last & prev) / max(len(last), len(prev))
            return overlap > 0.6
        return False

