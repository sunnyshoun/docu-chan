"""
Docu-chan - AI Documentation Generator

Usage:
    python main.py <project_path> [--request "..."]
    python main.py --chart "description"

簡化架構流程：
- Phase 1: 專案分析 (CoA) → 輸出 report.json
- Phase 2: 任務規劃 (簡化) → 輸出 planner_output.json
- Phase 3: 內容生成 → 輸出 docs/, charts/
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from dotenv import load_dotenv

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config, load_config
from agents import (
    ProjectAnalyzer,
    DocPlanner,
    ChartLoop,
    DocWriter
)
from agents.doc_planner import PlannerOutput, DocTodo, ChartTodo
from utils.file_utils import ensure_dir, write_file, read_file
from utils.logger import setup_logger, get_logger, Operation


def create_session_id() -> str:
    """建立 session ID (timestamp)"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_session_data(session_id: str, from_phase: int) -> Dict[str, Any]:
    """
    載入之前 session 的資料
    
    Args:
        session_id: Session ID (e.g., "20251229_224459")
        from_phase: 要從哪個 phase 開始 (1, 2, 3)
    
    Returns:
        dict: 包含需要的 session 資料
    
    Raises:
        FileNotFoundError: 如果必要的檔案不存在
        ValueError: 如果 session 不存在
    """
    session_dir = config.logs_dir / session_id
    if not session_dir.exists():
        raise ValueError(f"Session not found: {session_id}")
    
    data = {
        "session_dir": session_dir,
        "project_structure": None,
        "planner_output": None
    }
    
    # 如果要從 phase 2 或更後面開始，需要 phase 1 的資料
    if from_phase >= 2:
        report_file = session_dir / "phase1" / "report.json"
        if not report_file.exists():
            raise FileNotFoundError(f"Phase 1 report not found: {report_file}")
        with open(report_file, "r", encoding="utf-8") as f:
            data["project_structure"] = json.load(f)
    
    # 如果要從 phase 3 開始，需要 phase 2 的資料
    if from_phase >= 3:
        planner_file = session_dir / "phase2" / "planner_output.json"
        if not planner_file.exists():
            raise FileNotFoundError(f"Phase 2 planner output not found: {planner_file}")
        with open(planner_file, "r", encoding="utf-8") as f:
            planner_data = json.load(f)
            # 轉換為 PlannerOutput 物件
            doc_todos = [DocTodo.from_dict(t) for t in planner_data.get("doc_todos", [])]
            chart_todos = [ChartTodo.from_dict(t) for t in planner_data.get("chart_todos", [])]
            data["planner_output"] = PlannerOutput(
                doc_todos=doc_todos,
                chart_todos=chart_todos,
                project_summary=planner_data.get("project_summary", "")
            )
    
    return data


# ============================================================
# Phase Functions
# ============================================================

def run_analyzer(project_path: Path, session_dir: Path, max_parallel: int = 5) -> Dict[str, Any]:
    """
    Phase 1: 分析專案（使用 CoA 架構）
    
    Args:
        project_path: 專案路徑
        session_dir: Session 目錄
        max_parallel: 最大平行處理數
    
    Returns:
        project_structure: {
            "files": {path: {"summary": ..., "importance": ..., ...}},
            "metadata": {...}
        }
    
    Output Files:
        - phase1/report.json: 完整分析報告
        - phase1/dump.json: 原始分析資料
    """
    logger = get_logger()
    logger.info("📂 Phase 1: 分析專案...")
    
    phase_dir = session_dir / "phase1"
    ensure_dir(phase_dir)
    
    report_file = phase_dir / "report.json"
    
    # 使用 CoA 架構（Worker + Manager）
    analyzer = ProjectAnalyzer(
        root_dir=str(project_path),
        prompt_dir=str(config.prompts_dir / "project_analyzer"),
        dump_file=str(phase_dir / "dump.json"),
        report_file=str(report_file),
        max_parallel=max_parallel
    )
    
    # 直接開始分析（coa_analyzer 內部會顯示進度 UI 和完成訊息）
    analyzer.start()
    
    # 從檔案讀取報告（確保與儲存的一致）
    with open(report_file, "r", encoding="utf-8") as f:
        report_data = json.load(f)
    
    # 返回完整架構（供 Planner 使用）
    return report_data


def run_planner(project_structure: Dict[str, Any], user_request: str, project_path: Path, session_dir: Path) -> PlannerOutput:
    """
    Phase 2: 任務規劃（簡化版 - 預設只規劃 README + flow_chart）
    
    Args:
        project_structure: Phase 1 產生的架構 JSON (report.json)
        user_request: 使用者請求
        project_path: 專案路徑
        session_dir: Session 目錄
    
    Returns:
        PlannerOutput: 包含 doc_todos 和 chart_todos
    
    Output Files:
        - phase2/planner_output.json: 規劃結果
    """
    logger = get_logger()
    logger.info("📋 Phase 2: 任務規劃...")
    
    phase_dir = session_dir / "phase2"
    ensure_dir(phase_dir)
    
    # 使用 DocPlanner
    planner = DocPlanner()
    output = planner.execute(
        user_request=user_request,
        report=project_structure,
        project_path=str(project_path)
    )
    
    # 儲存規劃結果
    output_file = phase_dir / "planner_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output.to_dict(), f, indent=2, ensure_ascii=False)
    
    logger.info(f"   規劃 {len(output.doc_todos)} 份文件, {len(output.chart_todos)} 張圖表")
    
    return output


def run_generator(
    planner_output: PlannerOutput,
    project_structure: Dict[str, Any],
    project_path: Path,
    session_dir: Path,
    session_id: str
) -> tuple[list, list]:
    """
    Phase 3: 生成內容（整合設計+生成）
    
    Args:
        planner_output: Phase 2 產生的 PlannerOutput
        project_structure: Phase 1 產生的架構 JSON
        project_path: 專案路徑
        session_dir: Session 目錄
        session_id: Session ID
    
    Returns:
        (generated_charts, generated_docs)
    
    Output Files:
        - phase3/results.json: 生成結果摘要
        - outputs/<session_id>/charts/: 最終圖表輸出
        - outputs/<session_id>/docs/: 最終文件輸出
    """
    logger = get_logger()
    logger.info("✏️ Phase 3: 生成內容...")
    
    phase_dir = session_dir / "phase3"
    ensure_dir(phase_dir)
    
    generated_charts = []
    generated_docs = []
    
    # 生成圖表
    if planner_output.chart_todos:
        output_base = config.outputs_dir / session_id
        chart_loop = ChartLoop(
            log_dir=str(phase_dir / "charts"),
            output_dir=str(output_base / "charts")
        )
        
        total = len(planner_output.chart_todos)
        for i, todo in enumerate(planner_output.chart_todos):
            logger.op_progress(Operation.GENERATE, f"[{i+1}/{total}] 圖表: {todo.title}")
            try:
                # 轉換 ChartTodo 為 ChartTask 格式
                from models import ChartTask as ModelChartTask, ChartType
                
                chart_type_str = todo.chart_type.lower()
                try:
                    chart_type = ChartType(chart_type_str)
                except ValueError:
                    chart_type = ChartType.FLOWCHART
                
                model_task = ModelChartTask(
                    chart_type=chart_type,
                    title=todo.title,
                    description=todo.description,
                    instructions=todo.description,
                    suggested_files=todo.suggested_files,
                    suggested_participants=todo.suggested_participants,
                    questions_to_answer=todo.questions
                )
                
                result = chart_loop.run_from_task(task=model_task, project_path=str(project_path))
                generated_charts.append({
                    "success": result.success,
                    "title": todo.title,
                    "path": result.image_path,
                    "error": result.error
                })
                
                if not result.success:
                    logger.warning(f"⚠ 圖表失敗: {todo.title} - {result.error}")
            except Exception as e:
                logger.error(f"❌ 圖表錯誤: {todo.title} - {e}")
                generated_charts.append({"success": False, "title": todo.title, "error": str(e)})
    
    # 生成文檔（使用整合後的 DocWriter）
    if planner_output.doc_todos:
        writer = DocWriter(project_path=str(project_path))
        output_base = config.outputs_dir / session_id
        docs_output_dir = output_base / "docs"
        ensure_dir(docs_output_dir)
        
        total = len(planner_output.doc_todos)
        for i, todo in enumerate(planner_output.doc_todos):
            logger.op_progress(Operation.GENERATE, f"[{i+1}/{total}] 文件: {todo.title}")
            try:
                # 使用整合後的 execute_from_todo
                result = writer.execute_from_todo(
                    todo=todo,
                    report=project_structure,
                    project_path=str(project_path)
                )
                
                doc_filename = f"{todo.title.replace(' ', '_').replace('/', '_')}.md"
                doc_content = result.get("content", "")
                
                # 驗證內容不為空
                if not doc_content or not doc_content.strip():
                    raise ValueError(f"Generated empty content for: {todo.title}")
                
                output_path = docs_output_dir / doc_filename
                write_file(str(output_path), doc_content)
                
                generated_docs.append({
                    "success": True,
                    "title": todo.title,
                    "path": str(output_path)
                })
            except Exception as e:
                logger.error(f"❌ 文件錯誤: {todo.title} - {e}")
                generated_docs.append({"success": False, "title": todo.title, "error": str(e)})
    
    logger.finish_progress()
    
    # 儲存結果
    results = {"charts": generated_charts, "docs": generated_docs}
    with open(phase_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    success_charts = len([c for c in generated_charts if c.get('success')])
    success_docs = len([d for d in generated_docs if d.get('success')])
    logger.info(f"   生成 {success_charts} 張圖表, {success_docs} 份文件")
    
    return generated_charts, generated_docs


def run_packer(generated_charts: list, generated_docs: list, project_name: str, session_dir: Path, session_id: str):
    """
    Phase 4: 打包輸出
    
    Args:
        generated_charts: Phase 3 生成的圖表列表
        generated_docs: Phase 3 生成的文件列表
        project_name: 專案名稱
        session_dir: Session 目錄
        session_id: Session ID
    
    Output Files:
        - phase4/summary.json: 最終摘要
        - outputs/<session_id>/README.md: 生成的 README
    """
    logger = get_logger()
    logger.info("📦 Phase 4: 打包輸出...")
    
    phase_dir = session_dir / "phase4"
    ensure_dir(phase_dir)
    
    logger.op_progress(Operation.PACK, "生成 README...")
    
    # 建立 README
    readme_lines = [
        f"# {project_name}",
        "",
        f"*Generated by Docu-chan on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        ""
    ]
    
    if generated_charts:
        readme_lines.extend(["## Diagrams", ""])
        for chart in generated_charts:
            if chart.get("success") and chart.get("path"):
                name = Path(chart["path"]).name
                readme_lines.append(f"![{chart['title']}](charts/{name})")
                readme_lines.append("")
    
    if generated_docs:
        readme_lines.extend(["## Documentation", ""])
        for doc in generated_docs:
            if doc.get("success") and doc.get("path"):
                name = Path(doc["path"]).name
                readme_lines.append(f"- [{doc['title']}](docs/{name})")
        readme_lines.append("")
    
    readme_path = config.outputs_dir / session_id / "README.md"
    ensure_dir(readme_path.parent)
    write_file(readme_path, "\n".join(readme_lines))
    
    # 保存摘要
    summary = {
        "charts": generated_charts,
        "docs": generated_docs,
        "readme": str(readme_path)
    }
    with open(phase_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.finish_progress()
    logger.info(f"   README: {readme_path}")


# ============================================================
# Main Pipeline
# ============================================================

def run_pipeline(
    project_path: Path,
    user_request: str,
    max_parallel: int = 5,
    resume_session: Optional[str] = None,
    from_phase: int = 1
):
    """執行完整 pipeline（簡化架構）
    
    Args:
        project_path: 專案路徑
        user_request: 使用者請求
        max_parallel: 平行處理數量
        resume_session: 要恢復的 session ID（可選）
        from_phase: 從哪個 phase 開始（1, 2, 3），預設為 1
    
    流程：
    - Phase 1: 專案分析 → report.json
    - Phase 2: 任務規劃 → planner_output.json
    - Phase 3: 內容生成 → docs/, charts/
    - Phase 4: 打包輸出 → README.md
    """
    # 恢復模式或新建 session
    if resume_session:
        session_id = resume_session
        session_dir = config.logs_dir / session_id
        if not session_dir.exists():
            print(f"Error: Session not found: {session_id}")
            return False
    else:
        session_id = create_session_id()
        session_dir = config.logs_dir / session_id
        ensure_dir(session_dir)
    
    # 初始化日誌系統（設定檔案日誌）
    logger = setup_logger(
        log_dir=config.logs_dir,
        session_id=session_id,
        show_thinking=True
    )
    
    logger.info(f"Session: {session_id}")
    logger.info(f"專案: {project_path}")
    logger.info(f"請求: {user_request}")
    if resume_session:
        logger.info(f"恢復模式: 從 Phase {from_phase} 開始")
    logger.info("=" * 50)
    
    try:
        # 載入之前 session 的資料（如果是恢復模式）
        session_data = {}
        if resume_session and from_phase > 1:
            try:
                session_data = load_session_data(session_id, from_phase)
                logger.info(f"✓ 已載入 Session {session_id} 的資料")
            except (FileNotFoundError, ValueError) as e:
                logger.error(f"無法載入 session 資料: {e}")
                return False
        
        # Phase 1: 專案分析
        if from_phase <= 1:
            project_structure = run_analyzer(project_path, session_dir, max_parallel=max_parallel)
        else:
            project_structure = session_data.get("project_structure")
            logger.info("⏭ 跳過 Phase 1（使用已有的分析結果）")
        
        # Phase 2: 任務規劃
        if from_phase <= 2:
            planner_output = run_planner(project_structure, user_request, project_path, session_dir)
        else:
            planner_output = session_data.get("planner_output")
            logger.info("⏭ 跳過 Phase 2（使用已有的規劃結果）")
        
        # 檢查是否有任務
        if not planner_output.doc_todos and not planner_output.chart_todos:
            logger.warning("⚠ Planner 沒有產生任何任務，跳過後續階段")
            return True
        
        # Phase 3: 內容生成（整合設計+生成）
        charts, docs = run_generator(planner_output, project_structure, project_path, session_dir, session_id)
        
        # Phase 4: 打包輸出
        run_packer(charts, docs, project_path.name, session_dir, session_id)
        
        logger.info("=" * 50)
        logger.info("✅ Pipeline 完成!")
        
        # 顯示輸出
        logger = get_logger()
        output_base = config.outputs_dir / session_id
        logger.info("Outputs:")
        logger.info(f"  - README: {output_base / 'README.md'}")
        for c in charts:
            if c.get("success"):
                logger.info(f"  - Chart: {c['path']}")
        for d in docs:
            if d.get("success"):
                logger.info(f"  - Doc: {d['path']}")
        
        return True
        
    except Exception as e:
        import traceback
        logger = get_logger()
        logger.error(f"Pipeline failed: {e}")
        logger.debug(f"Pipeline error traceback:\n{traceback.format_exc()}")
        return False


def run_chart_only(description: str):
    """單獨生成圖表"""
    session_id = create_session_id()
    session_dir = config.logs_dir / session_id
    ensure_dir(session_dir)
    
    # 初始化日誌系統
    logger = setup_logger(
        log_dir=config.logs_dir,
        session_id=session_id,
        show_thinking=True
    )
    
    logger.info("🎨 Chart-only 模式")
    logger.info(f"   請求: {description}")
    
    chart_loop = ChartLoop(
        log_dir=str(session_dir / "chart"),
        output_dir=str(config.outputs_dir / "charts")
    )
    
    logger.op_progress(Operation.GENERATE, "生成圖表中...")
    result = chart_loop.run(description)
    logger.finish_progress()
    
    if result.success:
        logger.info(f"✅ 圖表儲存至: {result.image_path}")
        return True
    else:
        logger.error(f"❌ 失敗: {result.error}")
        return False


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Docu-chan - AI Documentation Generator"
    )
    parser.add_argument("project_path", nargs="?", help="Project path to analyze")
    parser.add_argument("-r", "--request", help="Documentation request")
    parser.add_argument("--chart", help="Generate single chart from description")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")
    parser.add_argument(
        "--parallel", "-p",
        type=int,
        default=5,
        help="Max parallel workers (default: 5, reduce if LLM errors occur)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Worker timeout in seconds (default: 60)"
    )
    parser.add_argument(
        "--resume",
        type=str,
        help="Resume from a previous session ID (e.g., 20251229_224459)"
    )
    parser.add_argument(
        "--from-phase",
        type=int,
        default=1,
        choices=[1, 2, 3],
        help="Start from a specific phase (1, 2, or 3). Requires --resume."
    )
    
    args = parser.parse_args()
    
    # 初始化
    load_dotenv()
    try:
        load_config()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    if not args.quiet:
        print("=" * 50)
        print("  Docu-chan v1.0.0")
        print("=" * 50)
    
    # Chart-only mode
    if args.chart:
        success = run_chart_only(args.chart)
        return 0 if success else 1
    
    # Validate resume arguments
    if args.from_phase > 1 and not args.resume:
        print("Error: --from-phase requires --resume to specify a session ID")
        return 1
    
    # Full pipeline
    if not args.project_path:
        parser.print_help()
        return 1
    
    project_path = Path(args.project_path).resolve()
    if not project_path.exists():
        print(f"Error: Path not found: {project_path}")
        return 1
    
    request = args.request or "Generate README and architecture documentation"
    
    success = run_pipeline(
        project_path,
        request,
        max_parallel=args.parallel,
        resume_session=args.resume,
        from_phase=args.from_phase
    )
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
