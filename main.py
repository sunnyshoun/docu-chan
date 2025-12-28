"""
Docu-chan - AI Documentation Generator

Usage:
    python main.py <project_path> [--request "..."]
    python main.py --chart "description"
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config, load_config
from agents import ProjectAnalyzer, PlannerOrchestrator, ChartLoop, DocWriter
from models import ChartTask, DocumentTask
from utils.file_utils import ensure_dir, write_file


def create_session_id() -> str:
    """建立 session ID (timestamp)"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def log(message: str, level: str = "INFO"):
    """輸出日誌"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


# ============================================================
# Phase Functions
# ============================================================

def run_analyzer(project_path: Path, session_dir: Path) -> dict[str, str]:
    """
    Phase 1: 分析專案
    
    Returns:
        file_summaries: {path: summary}
    """
    log("Phase 1: Analyzing project...")
    
    phase_dir = session_dir / "phase1"
    ensure_dir(phase_dir)
    
    analyzer = ProjectAnalyzer(
        root_dir=str(project_path),
        prompt_dir=str(config.prompts_dir / "project_analyzer"),
        dump_file=str(phase_dir / "dump.json"),
        report_file=str(phase_dir / "report.json")
    )
    
    log(f"  Analyzing {len(analyzer.file_nodes)} files...")
    analyzer.start()
    
    file_summaries = {
        path: info.get("summary", "")
        for path, info in analyzer.report.items()
    }
    
    log(f"  Analyzed {len(file_summaries)} files")
    return file_summaries


def run_planner(file_summaries: dict, user_request: str, project_path: Path, session_dir: Path):
    """
    Phase 2: 規劃任務
    
    Returns:
        PlannerResult
    """
    log("Phase 2: Planning tasks...")
    
    phase_dir = session_dir / "phase2"
    ensure_dir(phase_dir)
    
    orchestrator = PlannerOrchestrator()
    result = orchestrator.execute(
        file_summaries=file_summaries,
        user_request=user_request,
        project_path=str(project_path)
    )
    
    # 保存規劃結果
    with open(phase_dir / "plan.json", "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
    
    chart_count = len(orchestrator.get_all_charts_needed())
    doc_count = len(orchestrator.get_doc_tasks())
    log(f"  Planned {chart_count} charts, {doc_count} documents")
    
    return result


def run_generator(planner_result, project_path: Path, session_dir: Path) -> tuple[list, list]:
    """
    Phase 3: 生成內容
    
    Returns:
        (generated_charts, generated_docs)
    """
    log("Phase 3: Generating content...")
    
    phase_dir = session_dir / "phase3"
    ensure_dir(phase_dir)
    
    generated_charts = []
    generated_docs = []
    
    # 生成圖表
    if planner_result.chart_plan:
        chart_loop = ChartLoop(
            log_dir=str(phase_dir / "charts"),
            output_dir=str(config.outputs_dir / "charts")
        )
        
        for i, task in enumerate(planner_result.chart_plan.tasks):
            log(f"  [{i+1}] Generating chart: {task.title}")
            try:
                result = chart_loop.run_from_task(task=task, project_path=str(project_path))
                generated_charts.append({
                    "success": result.success,
                    "title": task.title,
                    "path": result.image_path,
                    "error": result.error
                })
            except Exception as e:
                log(f"      Failed: {e}", "ERROR")
                generated_charts.append({"success": False, "title": task.title, "error": str(e)})
    
    # 生成文檔
    if planner_result.doc_plan:
        writer = DocWriter(project_path=str(project_path))
        
        for i, task in enumerate(planner_result.doc_plan.tasks):
            log(f"  [{i+1}] Generating document: {task.title}")
            try:
                result = writer.execute_from_task(task=task, project_path=str(project_path))
                
                # 保存到 outputs/docs/
                output_path = config.outputs_dir / "docs" / f"{task.title.replace(' ', '_')}.md"
                ensure_dir(output_path.parent)
                write_file(output_path, result.get("content", ""))
                
                generated_docs.append({
                    "success": True,
                    "title": task.title,
                    "path": str(output_path)
                })
            except Exception as e:
                log(f"      Failed: {e}", "ERROR")
                generated_docs.append({"success": False, "title": task.title, "error": str(e)})
    
    log(f"  Generated {len([c for c in generated_charts if c.get('success')])} charts, "
        f"{len([d for d in generated_docs if d.get('success')])} documents")
    
    return generated_charts, generated_docs


def run_packer(generated_charts: list, generated_docs: list, project_name: str, session_dir: Path):
    """
    Phase 4: 打包輸出
    """
    log("Phase 4: Packaging outputs...")
    
    phase_dir = session_dir / "phase4"
    ensure_dir(phase_dir)
    
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
    
    readme_path = config.outputs_dir / "README.md"
    write_file(readme_path, "\n".join(readme_lines))
    
    # 保存摘要
    summary = {
        "charts": generated_charts,
        "docs": generated_docs,
        "readme": str(readme_path)
    }
    with open(phase_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    log(f"  README saved to: {readme_path}")


# ============================================================
# Main Pipeline
# ============================================================

def run_pipeline(project_path: Path, user_request: str):
    """執行完整 pipeline"""
    session_id = create_session_id()
    session_dir = config.logs_dir / session_id
    ensure_dir(session_dir)
    
    log(f"Session: {session_id}")
    log(f"Project: {project_path}")
    log(f"Request: {user_request}")
    log("=" * 50)
    
    try:
        # Phase 1
        file_summaries = run_analyzer(project_path, session_dir)
        
        # Phase 2
        planner_result = run_planner(file_summaries, user_request, project_path, session_dir)
        
        # Phase 3
        charts, docs = run_generator(planner_result, project_path, session_dir)
        
        # Phase 4
        run_packer(charts, docs, project_path.name, session_dir)
        
        log("=" * 50)
        log("Pipeline completed successfully!")
        
        # 顯示輸出
        print("\nOutputs:")
        print(f"  - README: {config.outputs_dir / 'README.md'}")
        for c in charts:
            if c.get("success"):
                print(f"  - Chart: {c['path']}")
        for d in docs:
            if d.get("success"):
                print(f"  - Doc: {d['path']}")
        
        return True
        
    except Exception as e:
        log(f"Pipeline failed: {e}", "ERROR")
        return False


def run_chart_only(description: str):
    """單獨生成圖表"""
    log("Chart-only mode")
    log(f"Request: {description}")
    
    session_id = create_session_id()
    session_dir = config.logs_dir / session_id
    ensure_dir(session_dir)
    
    chart_loop = ChartLoop(
        log_dir=str(session_dir / "chart"),
        output_dir=str(config.outputs_dir / "charts")
    )
    
    result = chart_loop.run(description)
    
    if result.success:
        log(f"Chart saved to: {result.image_path}")
        return True
    else:
        log(f"Failed: {result.error}", "ERROR")
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
        print("  Docu-chan v0.5.0")
        print("=" * 50)
    
    # Chart-only mode
    if args.chart:
        success = run_chart_only(args.chart)
        return 0 if success else 1
    
    # Full pipeline
    if not args.project_path:
        parser.print_help()
        return 1
    
    project_path = Path(args.project_path).resolve()
    if not project_path.exists():
        print(f"Error: Path not found: {project_path}")
        return 1
    
    request = args.request or "Generate README and architecture documentation"
    
    success = run_pipeline(project_path, request)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
