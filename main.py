"""
Docu-chan - AI Documentation Generator

完整工作流程：
  Phase 1: ProjectAnalyzer - 分析專案結構
  Phase 2: PlannerOrchestrator - 規劃文檔與圖表
  Phase 3: DocWriter + ChartLoop - 生成內容
  Phase 4: Packer - 打包輸出

Usage:
    python main.py <project_path> [options]
    python main.py --chart "<description>"  # 單獨生成圖表
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config, load_config
from agents import (
    ProjectAnalyzer,
    PlannerOrchestrator, ChartPlanner, DocPlanner,
    ChartLoop, DocWriter, DiagramDesigner,
    Packer
)
from models import ChartTask, DocumentTask, PlannerResult
from utils import ensure_dir, write_file, read_file


# ============================================================
# 工作流程控制器
# ============================================================

class DocuChanPipeline:
    """
    Docu-chan 完整工作流程控制器
    
    流程：
    1. Analyzer: 分析專案 -> file_summaries
    2. Planner: 規劃任務 -> ChartPlan + DocPlan
    3. Generator: 執行任務 -> Charts + Documents
    4. Packer: 打包輸出 -> outputs/
    """
    
    def __init__(
        self,
        project_path: str,
        output_dir: Optional[str] = None,
        skip_analysis: bool = False,
        skip_inspection: bool = False,
        verbose: bool = True
    ):
        self.project_path = Path(project_path).resolve()
        self.project_name = self.project_path.name
        self.output_dir = Path(output_dir) if output_dir else config.outputs_dir / "final"
        self.skip_analysis = skip_analysis
        self.skip_inspection = skip_inspection
        self.verbose = verbose
        
        # 工作目錄
        self.work_dir = config.logs_dir / "pipeline" / datetime.now().strftime("%Y%m%d_%H%M%S")
        ensure_dir(self.work_dir)
        
        # 中間結果
        self.file_summaries: Dict[str, str] = {}
        self.planner_result: Optional[PlannerResult] = None
        self.generated_charts: List[Dict[str, Any]] = []
        self.generated_docs: List[Dict[str, Any]] = []
    
    def log(self, message: str, level: str = "INFO"):
        """輸出日誌"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def run(self, user_request: str) -> Dict[str, Any]:
        """
        執行完整工作流程
        
        Args:
            user_request: 使用者需求描述
            
        Returns:
            dict: 執行結果
        """
        self.log(f"Starting Docu-chan pipeline for: {self.project_name}")
        self.log(f"User request: {user_request}")
        
        results = {
            "success": False,
            "project_path": str(self.project_path),
            "user_request": user_request,
            "phases": {},
            "outputs": []
        }
        
        try:
            # Phase 1: 分析專案
            self.log("=" * 50)
            self.log("Phase 1: Analyzing project...")
            phase1_result = self._run_analyzer()
            results["phases"]["analyzer"] = phase1_result
            
            if not phase1_result["success"]:
                self.log("Phase 1 failed!", "ERROR")
                return results
            
            # Phase 2: 規劃任務
            self.log("=" * 50)
            self.log("Phase 2: Planning tasks...")
            phase2_result = self._run_planner(user_request)
            results["phases"]["planner"] = phase2_result
            
            if not phase2_result["success"]:
                self.log("Phase 2 failed!", "ERROR")
                return results
            
            # Phase 3: 生成內容
            self.log("=" * 50)
            self.log("Phase 3: Generating content...")
            phase3_result = self._run_generator()
            results["phases"]["generator"] = phase3_result
            
            # Phase 4: 打包輸出
            self.log("=" * 50)
            self.log("Phase 4: Packaging outputs...")
            phase4_result = self._run_packer()
            results["phases"]["packer"] = phase4_result
            
            results["success"] = True
            results["outputs"] = phase4_result.get("outputs", [])
            
            self.log("=" * 50)
            self.log("Pipeline completed successfully!")
            
        except Exception as e:
            self.log(f"Pipeline error: {e}", "ERROR")
            results["error"] = str(e)
        
        # 保存結果
        self._save_results(results)
        
        return results
    
    def _run_analyzer(self) -> Dict[str, Any]:
        """
        執行 Phase 1: 專案分析
        
        Returns:
            dict: 分析結果
        """
        result = {"success": False, "file_count": 0}
        
        # 快取目錄：logs/cache/{project_name}/
        cache_dir = config.logs_dir / "cache" / self.project_name
        ensure_dir(cache_dir)
        cache_file = cache_dir / "analyzer_report.json"
        
        # 檢查是否有已存在的分析結果
        if self.skip_analysis and cache_file.exists():
            self.log(f"Loading existing analysis report from {cache_file}...")
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    report = json.load(f)
                self.file_summaries = {
                    path: info.get("summary", "")
                    for path, info in report.items()
                }
                result["success"] = True
                result["file_count"] = len(self.file_summaries)
                result["source"] = "cached"
                self.log(f"Loaded {result['file_count']} file summaries from cache")
                return result
            except Exception as e:
                self.log(f"Failed to load cache: {e}", "WARN")
        
        # 執行分析
        try:
            dump_file = str(self.work_dir / "analyzer_dump.json")
            report_file_path = str(self.work_dir / "analyzer_report.json")
            prompt_dir = str(config.prompts_dir / "project_analyzer")
            
            analyzer = ProjectAnalyzer(
                root_dir=str(self.project_path),
                prompt_dir=prompt_dir,
                dump_file=dump_file,
                report_file=report_file_path
            )
            
            self.log(f"Analyzing {len(analyzer.file_nodes)} files...")
            analyzer.start(recovery_run=False)
            
            # 轉換結果
            self.file_summaries = {
                path: info.get("summary", "")
                for path, info in analyzer.report.items()
            }
            
            result["success"] = True
            result["file_count"] = len(self.file_summaries)
            result["source"] = "fresh"
            
            # 保存到快取目錄（logs/cache/{project_name}/）
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(analyzer.report, f, indent=2, ensure_ascii=False)
            
            self.log(f"Analyzed {result['file_count']} files")
            self.log(f"Cache saved to: {cache_file}")
            
        except Exception as e:
            self.log(f"Analyzer error: {e}", "ERROR")
            result["error"] = str(e)
        
        return result
    
    def _run_planner(self, user_request: str) -> Dict[str, Any]:
        """
        執行 Phase 2: 任務規劃
        
        Args:
            user_request: 使用者需求
            
        Returns:
            dict: 規劃結果
        """
        result = {"success": False, "chart_tasks": 0, "doc_tasks": 0}
        
        try:
            orchestrator = PlannerOrchestrator()
            
            self.planner_result = orchestrator.execute(
                file_summaries=self.file_summaries,
                user_request=user_request,
                project_path=str(self.project_path)
            )
            
            # 統計任務數量
            chart_tasks = orchestrator.get_all_charts_needed()
            doc_tasks = orchestrator.get_doc_tasks()
            
            result["chart_tasks"] = len(chart_tasks)
            result["doc_tasks"] = len(doc_tasks)
            result["success"] = True
            
            # 保存規劃結果
            plan_file = self.work_dir / "planner_result.json"
            with open(plan_file, "w", encoding="utf-8") as f:
                json.dump(self.planner_result.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.log(f"Planned {result['chart_tasks']} charts and {result['doc_tasks']} documents")
            
        except Exception as e:
            self.log(f"Planner error: {e}", "ERROR")
            result["error"] = str(e)
        
        return result
    
    def _run_generator(self) -> Dict[str, Any]:
        """
        執行 Phase 3: 內容生成
        
        Returns:
            dict: 生成結果
        """
        result = {
            "success": False,
            "charts_generated": 0,
            "docs_generated": 0,
            "charts": [],
            "docs": []
        }
        
        if not self.planner_result:
            result["error"] = "No planner result available"
            return result
        
        # 生成圖表
        if self.planner_result.chart_plan:
            self.log("Generating charts...")
            chart_results = self._generate_charts(self.planner_result.chart_plan.tasks)
            result["charts_generated"] = len([c for c in chart_results if c.get("success")])
            result["charts"] = chart_results
            self.generated_charts = chart_results
        
        # 生成文檔
        if self.planner_result.doc_plan:
            self.log("Generating documents...")
            doc_results = self._generate_docs(self.planner_result.doc_plan.tasks)
            result["docs_generated"] = len([d for d in doc_results if d.get("success")])
            result["docs"] = doc_results
            self.generated_docs = doc_results
        
        result["success"] = True
        self.log(f"Generated {result['charts_generated']} charts and {result['docs_generated']} documents")
        
        return result
    
    def _generate_charts(self, tasks: List[ChartTask]) -> List[Dict[str, Any]]:
        """
        生成圖表
        
        Designer 會根據 task 的指引自主讀取檔案，收集資訊後設計圖表。
        
        Args:
            tasks: 圖表任務列表
            
        Returns:
            list: 生成結果列表
        """
        results = []
        
        chart_loop = ChartLoop(
            log_dir=str(self.work_dir / "charts"),
            output_dir=str(self.output_dir / "diagrams")
        )
        
        for i, task in enumerate(tasks):
            self.log(f"  Generating chart {i+1}/{len(tasks)}: {task.title}")
            
            try:
                # 使用 ChartLoop 的新模式：傳入 ChartTask
                # ChartLoop 會呼叫 DiagramDesigner.execute_from_task()
                # Designer 會自己讀取檔案來補充資訊
                chart_result = chart_loop.run_from_task(
                    task=task,
                    project_path=str(self.project_path),
                    skip_inspection=self.skip_inspection
                )
                
                results.append({
                    "success": chart_result.success,
                    "title": task.title,
                    "chart_type": task.chart_type.value,
                    "image_path": chart_result.image_path,
                    "iterations": chart_result.iterations,
                    "error": chart_result.error
                })
                
            except Exception as e:
                self.log(f"    Chart generation failed: {e}", "ERROR")
                results.append({
                    "success": False,
                    "title": task.title,
                    "chart_type": task.chart_type.value,
                    "error": str(e)
                })
        
        return results
        
        return results
    
    def _create_chart_request(self, task: ChartTask) -> str:
        """建立給 ChartLoop 的請求字串"""
        parts = [
            f"Create a {task.chart_type.value} diagram.",
            f"Title: {task.title}",
            f"Description: {task.description}"
        ]
        
        if task.context:
            parts.append(f"Context: {task.context[:500]}")
        
        if task.tpa_hints:
            parts.append(f"Hints: {json.dumps(task.tpa_hints)}")
        
        return "\n".join(parts)
    
    def _generate_docs(self, tasks: List[DocumentTask]) -> List[Dict[str, Any]]:
        """
        生成文檔
        
        Args:
            tasks: 文檔任務列表
            
        Returns:
            list: 生成結果列表
        """
        results = []
        
        writer = DocWriter()
        
        for i, task in enumerate(tasks):
            self.log(f"  Generating document {i+1}/{len(tasks)}: {task.title}")
            
            try:
                # 建立 DocPlan 格式的輸入
                from models import DocPlan
                doc_plan = DocPlan(
                    sections=[s.to_dict() for s in task.sections],
                    charts_needed=[],
                    style_guide=task.style_guide
                )
                
                # 執行 DocWriter
                doc_result = writer.execute(doc_plan)
                
                # 保存文檔
                output_path = self.output_dir / "docs" / f"{task.title.replace(' ', '_')}.md"
                ensure_dir(output_path.parent)
                write_file(output_path, doc_result.get("content", ""))
                
                results.append({
                    "success": True,
                    "title": task.title,
                    "doc_type": task.doc_type.value,
                    "output_path": str(output_path),
                    "sections": len(task.sections)
                })
                
            except Exception as e:
                self.log(f"    Document generation failed: {e}", "ERROR")
                results.append({
                    "success": False,
                    "title": task.title,
                    "doc_type": task.doc_type.value,
                    "error": str(e)
                })
        
        return results
    
    def _run_packer(self) -> Dict[str, Any]:
        """
        執行 Phase 4: 打包輸出
        
        Returns:
            dict: 打包結果
        """
        result = {"success": False, "outputs": []}
        
        try:
            # 整合所有輸出
            outputs = []
            
            # 圖表
            for chart in self.generated_charts:
                if chart.get("success") and chart.get("image_path"):
                    outputs.append({
                        "type": "chart",
                        "path": chart["image_path"],
                        "title": chart.get("title", "")
                    })
            
            # 文檔
            for doc in self.generated_docs:
                if doc.get("success") and doc.get("output_path"):
                    outputs.append({
                        "type": "document",
                        "path": doc["output_path"],
                        "title": doc.get("title", "")
                    })
            
            # 建立 README（如果有文檔生成結果）
            readme_path = self._create_readme()
            if readme_path:
                outputs.append({
                    "type": "readme",
                    "path": str(readme_path),
                    "title": "README.md"
                })
            
            result["outputs"] = outputs
            result["success"] = True
            
            self.log(f"Packaged {len(outputs)} outputs")
            
        except Exception as e:
            self.log(f"Packer error: {e}", "ERROR")
            result["error"] = str(e)
        
        return result
    
    def _create_readme(self) -> Optional[Path]:
        """建立最終 README"""
        readme_parts = [
            f"# {self.project_name}",
            "",
            f"*Generated by Docu-chan on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            ""
        ]
        
        # 加入專案摘要
        if self.planner_result and self.planner_result.project_summary:
            readme_parts.extend([
                "## Overview",
                "",
                self.planner_result.project_summary[:1000],
                ""
            ])
        
        # 加入圖表連結
        if self.generated_charts:
            readme_parts.extend([
                "## Diagrams",
                ""
            ])
            for chart in self.generated_charts:
                if chart.get("success") and chart.get("image_path"):
                    title = chart.get("title", "Diagram")
                    path = Path(chart["image_path"]).name
                    readme_parts.append(f"### {title}")
                    readme_parts.append(f"![{title}](diagrams/{path})")
                    readme_parts.append("")
        
        # 加入文檔連結
        if self.generated_docs:
            readme_parts.extend([
                "## Documentation",
                ""
            ])
            for doc in self.generated_docs:
                if doc.get("success") and doc.get("output_path"):
                    title = doc.get("title", "Document")
                    path = Path(doc["output_path"]).name
                    readme_parts.append(f"- [{title}](docs/{path})")
            readme_parts.append("")
        
        # 寫入檔案
        readme_path = self.output_dir / "README.md"
        ensure_dir(readme_path.parent)
        write_file(readme_path, "\n".join(readme_parts))
        
        return readme_path
    
    def _save_results(self, results: Dict[str, Any]):
        """保存執行結果"""
        result_file = self.work_dir / "pipeline_result.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        self.log(f"Results saved to: {result_file}")


# ============================================================
# CLI 入口
# ============================================================

def main():
    """Main entry point for the documentation generator."""
    parser = argparse.ArgumentParser(
        description="Docu-chan - AI Documentation Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 完整工作流程
  python main.py ./my-project --request "Generate README and architecture diagram"
  
  # 使用快取的分析結果
  python main.py ./my-project --request "Generate API docs" --skip-analysis
  
  # 單獨生成圖表
  python main.py --chart "User authentication flow diagram"
  
  # 只執行分析
  python main.py ./my-project --analyze-only
        """
    )
    
    # 位置參數
    parser.add_argument(
        "project_path",
        type=str,
        nargs="?",
        help="Path to the project to analyze"
    )
    
    # 工作流程選項
    parser.add_argument(
        "--request", "-r",
        type=str,
        help="User request for documentation/charts"
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Only run the analyzer phase"
    )
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Skip analysis if cached results exist"
    )
    
    # 單獨圖表模式
    parser.add_argument(
        "--chart",
        type=str,
        help="Generate a single chart from description"
    )
    
    # 輸出選項
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output directory"
    )
    
    # 其他選項
    parser.add_argument(
        "--skip-inspection",
        action="store_true",
        help="Skip visual inspection for charts"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress verbose output"
    )
    
    args = parser.parse_args()
    
    # 顯示標題
    if not args.quiet:
        print("=" * 50)
        print("  Docu-chan v0.4.0")
        print("  AI Documentation Generator")
        print("=" * 50)
    
    # 載入設定
    try:
        load_dotenv()
        load_config()
    except Exception as e:
        print(f"\n[Error] Failed to initialize: {e}")
        print("Please set API_KEY and API_BASE_URL in .env file")
        return 1
    
    # 單獨圖表模式
    if args.chart:
        print(f"\n[Chart Mode] Generating chart...")
        print(f"Request: {args.chart}")
        
        chart_loop = ChartLoop(
            log_dir=str(config.chart.log_dir),
            output_dir=args.output or str(config.chart.output_dir)
        )
        
        result = chart_loop.run(
            args.chart,
            skip_inspection=args.skip_inspection
        )
        
        if result.success:
            print(f"\n✓ Chart saved to: {result.image_path}")
            print(f"  Diagram type: {result.mermaid_code.diagram_type if result.mermaid_code else 'unknown'}")
            print(f"  Iterations: {result.iterations}")
        else:
            print(f"\n✗ Failed: {result.error}")
        
        return 0 if result.success else 1
    
    # 需要專案路徑
    if not args.project_path:
        parser.print_help()
        print("\nError: project_path is required for full pipeline mode")
        return 1
    
    # 驗證專案路徑
    project_path = Path(args.project_path).resolve()
    if not project_path.exists():
        print(f"\nError: Project path does not exist: {project_path}")
        return 1
    
    # 只執行分析
    if args.analyze_only:
        print(f"\n[Analyze Mode] Analyzing project: {project_path}")
        
        pipeline = DocuChanPipeline(
            project_path=str(project_path),
            output_dir=args.output,
            verbose=not args.quiet
        )
        
        result = pipeline._run_analyzer()
        
        if result["success"]:
            cache_path = config.logs_dir / "cache" / project_path.name / "analyzer_report.json"
            print(f"\n✓ Analysis complete!")
            print(f"  Files analyzed: {result['file_count']}")
            print(f"  Cache saved to: {cache_path}")
        else:
            print(f"\n✗ Analysis failed: {result.get('error', 'Unknown error')}")
        
        return 0 if result["success"] else 1
    
    # 完整工作流程
    if not args.request:
        # 預設請求
        args.request = "Generate comprehensive documentation including README, architecture diagram, and API documentation"
    
    print(f"\n[Full Pipeline Mode]")
    print(f"Project: {project_path}")
    print(f"Request: {args.request}")
    print()
    
    pipeline = DocuChanPipeline(
        project_path=str(project_path),
        output_dir=args.output,
        skip_analysis=args.skip_analysis,
        skip_inspection=args.skip_inspection,
        verbose=not args.quiet
    )
    
    result = pipeline.run(args.request)
    
    if result["success"]:
        print("\n" + "=" * 50)
        print("✓ Pipeline completed successfully!")
        print("=" * 50)
        print("\nOutputs:")
        for output in result.get("outputs", []):
            print(f"  - [{output['type']}] {output['path']}")
    else:
        print("\n" + "=" * 50)
        print("✗ Pipeline failed!")
        print("=" * 50)
        if "error" in result:
            print(f"Error: {result['error']}")
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
