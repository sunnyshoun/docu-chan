"""
Chart Planner - 圖表規劃器

負責：
1. 分析專案結構和依賴關係
2. 根據使用者需求規劃需要生成的圖表
3. 使用 CoA 架構處理長文本
4. 與 DiagramDesigner 協作，提供圖表設計的上下文資訊
"""
import json
from typing import Any, Dict, List, Optional

from config.settings import get_config
from agents.base import BaseAgent
from models import (
    ChartPlan, ChartTask, ChartType,
    CodeSummary, TPAAnalysis
)
from utils.coa_utils import (
    CoAProcessor, CoAChunk, WorkerOutput, ManagerOutput,
    create_file_chunks, aggregate_worker_outputs
)
from tools import get_tools, execute
from tools.file_ops import set_project_root


class ChartPlanner(BaseAgent):
    """
    圖表規劃器
    
    流程：
    1. 接收專案分析結果 (file summaries)
    2. 使用 CoA 架構分析各檔案，理解專案結構
    3. 根據使用者請求，規劃需要生成的圖表
    4. 輸出 ChartPlan 傳遞給 DiagramDesigner
    
    與 DiagramDesigner 的整合：
    - ChartPlanner 負責「規劃什麼圖表」和「提供專案上下文」
    - DiagramDesigner 負責「設計圖表結構」(TPA 分析 + 結構設計)
    - ChartPlanner 的輸出會作為 DiagramDesigner 的輸入
    """
    
    PROMPT_WORKER = "doc_planner/chart_worker"
    PROMPT_MANAGER = "doc_planner/chart_manager"
    PROMPT_PLAN = "doc_planner/chart_plan"
    
    def __init__(
        self,
        model: Optional[str] = None,
        worker_model: Optional[str] = None,
        use_tools: bool = True
    ):
        config = get_config()
        super().__init__(
            name="ChartPlanner",
            model=model or config.models.doc_planner,
            think=True
        )
        self.worker_model = worker_model or config.models.code_reader
        self.use_tools = use_tools
        self._dependency_graph: Dict[str, List[str]] = {}
        self._project_context: str = ""
    
    def execute(
        self,
        file_summaries: Dict[str, str],
        user_request: str,
        project_path: str,
        entry_points: Optional[List[str]] = None,
        **kwargs
    ) -> ChartPlan:
        """
        執行圖表規劃
        
        Args:
            file_summaries: 檔案路徑 -> 摘要 的映射
            user_request: 使用者的圖表需求描述
            project_path: 專案根目錄路徑
            entry_points: 入口點檔案列表 (可選，會自動檢測)
            
        Returns:
            ChartPlan: 圖表規劃結果
        """
        self.log(f"Planning charts for: {user_request[:100]}...")
        
        # Step 1: 找出入口點
        if not entry_points:
            entry_result = find_entry_points(project_path)
            if entry_result["success"] and entry_result["entry_points"]:
                entry_points = [e["full_path"] for e in entry_result["entry_points"][:3]]
        
        self.log(f"Entry points: {entry_points}")
        
        # Step 2: 建立依賴圖
        dep_result = build_dependency_graph(file_summaries, project_path)
        if dep_result["success"]:
            self._dependency_graph = dep_result["graph"]
        
        # Step 3: 使用 CoA 處理檔案摘要
        project_context = self._process_with_coa(
            file_summaries,
            entry_points or [],
            project_path
        )
        self._project_context = project_context
        
        # Step 4: 規劃圖表
        chart_plan = self._plan_charts(
            user_request,
            project_context,
            file_summaries
        )
        
        return chart_plan
    
    def _process_with_coa(
        self,
        file_summaries: Dict[str, str],
        entry_points: List[str],
        project_path: str
    ) -> str:
        """
        使用 CoA 架構處理檔案摘要
        
        Args:
            file_summaries: 檔案摘要
            entry_points: 入口點
            project_path: 專案路徑
            
        Returns:
            str: 整合後的專案上下文
        """
        # 建立 chunks
        chunks = create_file_chunks(file_summaries, None, entry_points)
        
        if not chunks:
            return "No files to analyze."
        
        # 定義 worker 函數
        def worker_fn(
            chunk: CoAChunk,
            worker_id: int,
            prev_comm: Optional[str]
        ) -> WorkerOutput:
            return self._worker_process(chunk, worker_id, prev_comm)
        
        # 定義 manager 函數
        def manager_fn(outputs: List[WorkerOutput]) -> ManagerOutput:
            return self._manager_aggregate(outputs)
        
        # 執行 CoA
        processor = CoAProcessor(
            worker_fn=worker_fn,
            manager_fn=manager_fn,
            sequential=True  # 順序處理以保持依賴關係
        )
        
        result = processor.process(chunks)
        return result.final_summary
    
    def _worker_process(
        self,
        chunk: CoAChunk,
        worker_id: int,
        prev_comm: Optional[str]
    ) -> WorkerOutput:
        """
        Worker 處理單一檔案
        
        Args:
            chunk: 待處理的片段
            worker_id: Worker ID
            prev_comm: 前一個 Worker 的 communication unit
            
        Returns:
            WorkerOutput: 處理結果
        """
        # 建立 prompt 變數
        context = f"Previous context: {prev_comm}" if prev_comm else "This is the first file."
        
        variables = {
            "file_path": chunk.source_file,
            "file_content": chunk.content,
            "previous_context": context,
            "is_entry_point": chunk.metadata.get("is_entry_point", False)
        }
        
        # 如果需要更多資訊，使用 tools
        additional_info = ""
        if self.use_tools and chunk.source_file:
            # 分析依賴
            deps = analyze_file_dependencies(chunk.source_file)
            if deps["success"]:
                additional_info += f"\nDependencies: {deps.get('local_imports', [])}"
            
            # 取得結構
            structure = get_file_structure(chunk.source_file)
            if structure["success"]:
                classes = [c["name"] for c in structure.get("classes", [])]
                functions = [f["name"] for f in structure.get("functions", [])]
                additional_info += f"\nClasses: {classes}\nFunctions: {functions}"
        
        variables["additional_info"] = additional_info
        
        # 呼叫 LLM
        try:
            response = self.chat(
                prompt_name=self.PROMPT_WORKER,
                variables=variables,
                keep_history=False
            )
            
            result = self.parse_json(response.message.content)
            
            return WorkerOutput(
                worker_id=worker_id,
                chunk_id=chunk.chunk_id,
                local_summary=result.get("summary", ""),
                communication_unit=result.get("key_points", ""),
                source_file=chunk.source_file,
                metadata={
                    "chart_hints": result.get("chart_hints", []),
                    "dependencies": result.get("dependencies", [])
                }
            )
            
        except Exception as e:
            self.log(f"Worker {worker_id} error: {e}")
            return WorkerOutput(
                worker_id=worker_id,
                chunk_id=chunk.chunk_id,
                local_summary=f"Error processing: {chunk.source_file}",
                communication_unit="",
                source_file=chunk.source_file
            )
    
    def _manager_aggregate(self, outputs: List[WorkerOutput]) -> ManagerOutput:
        """
        Manager 整合所有 Worker 輸出
        
        Args:
            outputs: Worker 輸出列表
            
        Returns:
            ManagerOutput: 整合結果
        """
        # 聚合所有輸出
        aggregated = aggregate_worker_outputs(outputs)
        
        # 收集圖表建議
        chart_hints = []
        for output in outputs:
            hints = output.metadata.get("chart_hints", [])
            chart_hints.extend(hints)
        
        variables = {
            "aggregated_summaries": aggregated,
            "dependency_graph": json.dumps(self._dependency_graph, indent=2),
            "chart_hints": chart_hints
        }
        
        try:
            response = self.chat(
                prompt_name=self.PROMPT_MANAGER,
                variables=variables,
                keep_history=False
            )
            
            result = self.parse_json(response.message.content)
            
            return ManagerOutput(
                final_summary=result.get("project_summary", aggregated),
                aggregated_insights=[{
                    "file": o.source_file,
                    "summary": o.local_summary
                } for o in outputs],
                recommendations=result.get("recommended_charts", []),
                metadata={"chart_hints": chart_hints}
            )
            
        except Exception as e:
            self.log(f"Manager error: {e}")
            return ManagerOutput(
                final_summary=aggregated,
                aggregated_insights=[{
                    "file": o.source_file,
                    "summary": o.local_summary
                } for o in outputs],
                recommendations=[]
            )
    
    def _plan_charts(
        self,
        user_request: str,
        project_context: str,
        file_summaries: Dict[str, str]
    ) -> ChartPlan:
        """
        根據使用者請求規劃圖表
        
        Args:
            user_request: 使用者請求
            project_context: 專案上下文
            file_summaries: 檔案摘要
            
        Returns:
            ChartPlan: 圖表規劃
        """
        variables = {
            "user_request": user_request,
            "project_context": project_context,
            "dependency_graph": json.dumps(self._dependency_graph, indent=2),
            "file_list": list(file_summaries.keys())
        }
        
        try:
            response = self.chat(
                prompt_name=self.PROMPT_PLAN,
                variables=variables,
                keep_history=False
            )
            
            result = self.parse_json(response.message.content)
            
            # 解析圖表任務
            tasks = []
            for task_data in result.get("charts", []):
                task = ChartTask.from_dict(task_data)
                tasks.append(task)
            
            return ChartPlan(
                tasks=tasks,
                project_context=project_context,
                dependency_graph=self._dependency_graph,
                execution_order=list(range(len(tasks)))
            )
            
        except Exception as e:
            self.log(f"Planning error: {e}")
            # 回傳預設規劃
            return ChartPlan(
                tasks=[
                    ChartTask(
                        chart_type=ChartType.FLOWCHART,
                        title="Project Overview",
                        description=user_request,
                        target_files=list(file_summaries.keys())[:5],
                        context=project_context
                    )
                ],
                project_context=project_context,
                dependency_graph=self._dependency_graph
            )
    
    def create_designer_input(self, task: ChartTask) -> str:
        """
        為 DiagramDesigner 建立輸入
        
        整合 ChartPlanner 的規劃結果，轉換為 DiagramDesigner 可用的格式
        
        Args:
            task: 圖表任務
            
        Returns:
            str: 給 DiagramDesigner 的使用者請求
        """
        request_parts = [
            f"Create a {task.chart_type.value} diagram.",
            f"Title: {task.title}",
            f"Description: {task.description}",
        ]
        
        if task.context:
            request_parts.append(f"Context: {task.context}")
        
        if task.target_files:
            request_parts.append(f"Relevant files: {', '.join(task.target_files[:5])}")
        
        if task.tpa_hints:
            request_parts.append(f"Design hints: {json.dumps(task.tpa_hints)}")
        
        return "\n".join(request_parts)
    
    @property
    def dependency_graph(self) -> Dict[str, List[str]]:
        """取得依賴圖"""
        return self._dependency_graph
    
    @property
    def project_context(self) -> str:
        """取得專案上下文"""
        return self._project_context
