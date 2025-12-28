"""
Doc Planner - 文檔規劃器

負責：
1. 分析專案結構和依賴關係
2. 根據使用者需求規劃需要生成的文件
3. 使用 CoA 架構處理長文本
4. 輸出 EnhancedDocPlan 傳遞給 DocWriter
"""
import json
from typing import Any, Dict, List, Optional

from config.settings import get_config
from agents.base import BaseAgent
from models import (
    EnhancedDocPlan, DocumentTask, DocumentSection, DocumentType,
    ChartTask, ChartType, CodeSummary
)
from utils.coa_utils import (
    CoAProcessor, CoAChunk, WorkerOutput, ManagerOutput,
    create_file_chunks, aggregate_worker_outputs
)
from utils.tools import (
    PLANNER_TOOLS, execute_tool,
    read_file_content, analyze_file_dependencies,
    get_file_structure, find_entry_points,
    build_dependency_graph
)


class DocPlanner(BaseAgent):
    """
    文檔規劃器
    
    流程：
    1. 接收專案分析結果 (file summaries)
    2. 使用 CoA 架構分析各檔案，理解專案結構
    3. 根據使用者請求，規劃需要生成的文件
    4. 識別文件中需要的圖表
    5. 輸出 EnhancedDocPlan 傳遞給 DocWriter
    
    輸出給 DocWriter 的資訊包含：
    - 文件任務列表 (DocumentTask)
    - 每個任務的章節規劃 (DocumentSection)
    - 相關的原始碼檔案參考
    - 風格指南
    - 需要嵌入的圖表列表
    """
    
    PROMPT_WORKER = "doc_planner/doc_worker"
    PROMPT_MANAGER = "doc_planner/doc_manager"
    PROMPT_PLAN = "doc_planner/doc_plan"
    
    def __init__(
        self,
        model: Optional[str] = None,
        worker_model: Optional[str] = None,
        use_tools: bool = True
    ):
        config = get_config()
        super().__init__(
            name="DocPlanner",
            model=model or config.models.doc_planner,
            think=True
        )
        self.worker_model = worker_model or config.models.code_reader
        self.use_tools = use_tools
        self._dependency_graph: Dict[str, List[str]] = {}
        self._project_context: str = ""
        self._file_contents: Dict[str, str] = {}
    
    def execute(
        self,
        file_summaries: Dict[str, str],
        user_request: str,
        project_path: str,
        entry_points: Optional[List[str]] = None,
        **kwargs
    ) -> EnhancedDocPlan:
        """
        執行文檔規劃
        
        Args:
            file_summaries: 檔案路徑 -> 摘要 的映射
            user_request: 使用者的文檔需求描述
            project_path: 專案根目錄路徑
            entry_points: 入口點檔案列表 (可選，會自動檢測)
            
        Returns:
            EnhancedDocPlan: 文檔規劃結果
        """
        self.log(f"Planning documentation for: {user_request[:100]}...")
        
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
        
        # Step 4: 規劃文檔
        doc_plan = self._plan_documentation(
            user_request,
            project_context,
            file_summaries
        )
        
        return doc_plan
    
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
        # 決定哪些檔案需要讀取完整內容
        files_to_read = self._select_files_to_read(
            file_summaries, entry_points, project_path
        )
        
        # 讀取需要的檔案內容
        file_contents: Dict[str, str] = {}
        for file_path in files_to_read:
            result = read_file_content(file_path)
            if result["success"]:
                file_contents[file_path] = result["content"]
                self._file_contents[file_path] = result["content"]
        
        # 建立 chunks
        chunks = create_file_chunks(file_summaries, file_contents, entry_points)
        
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
            sequential=True
        )
        
        result = processor.process(chunks)
        return result.final_summary
    
    def _select_files_to_read(
        self,
        file_summaries: Dict[str, str],
        entry_points: List[str],
        project_path: str
    ) -> List[str]:
        """
        決定要讀取完整內容的檔案
        
        策略：
        1. 入口點檔案
        2. 被多個檔案依賴的檔案
        3. 包含重要關鍵字的檔案（如 API, config 等）
        
        Args:
            file_summaries: 檔案摘要
            entry_points: 入口點
            project_path: 專案路徑
            
        Returns:
            List[str]: 要讀取的檔案路徑列表
        """
        files_to_read = set(entry_points)
        
        # 找出被多次依賴的檔案
        if self._dependency_graph:
            dep_counts: Dict[str, int] = {}
            for deps in self._dependency_graph.values():
                for dep in deps:
                    dep_counts[dep] = dep_counts.get(dep, 0) + 1
            
            # 取前 5 個最常被依賴的
            sorted_deps = sorted(dep_counts.items(), key=lambda x: x[1], reverse=True)
            for dep, _ in sorted_deps[:5]:
                from pathlib import Path
                full_path = Path(project_path) / dep
                if full_path.exists():
                    files_to_read.add(str(full_path))
        
        # 包含重要關鍵字的檔案
        important_keywords = ['api', 'config', 'settings', 'model', 'schema', 'router']
        for file_path in file_summaries.keys():
            for keyword in important_keywords:
                if keyword in file_path.lower():
                    from pathlib import Path
                    full_path = Path(project_path) / file_path
                    if full_path.exists():
                        files_to_read.add(str(full_path))
                    break
        
        return list(files_to_read)[:15]  # 限制最多 15 個
    
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
        context = f"Previous context: {prev_comm}" if prev_comm else "This is the first file."
        
        variables = {
            "file_path": chunk.source_file,
            "file_content": chunk.content,
            "previous_context": context,
            "is_entry_point": chunk.metadata.get("is_entry_point", False)
        }
        
        # 使用 tools 取得更多資訊
        additional_info = ""
        if self.use_tools and chunk.source_file:
            structure = get_file_structure(chunk.source_file)
            if structure["success"]:
                classes = structure.get("classes", [])
                functions = structure.get("functions", [])
                
                if classes:
                    class_info = []
                    for c in classes:
                        methods = [m["name"] for m in c.get("methods", [])]
                        class_info.append(f"{c['name']}: methods={methods}")
                    additional_info += f"\nClasses: {class_info}"
                
                if functions:
                    func_names = [f["name"] for f in functions]
                    additional_info += f"\nFunctions: {func_names}"
        
        variables["additional_info"] = additional_info
        
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
                    "doc_hints": result.get("doc_hints", []),
                    "api_endpoints": result.get("api_endpoints", []),
                    "public_interfaces": result.get("public_interfaces", [])
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
        aggregated = aggregate_worker_outputs(outputs)
        
        # 收集文檔建議和 API 端點
        doc_hints = []
        api_endpoints = []
        public_interfaces = []
        
        for output in outputs:
            doc_hints.extend(output.metadata.get("doc_hints", []))
            api_endpoints.extend(output.metadata.get("api_endpoints", []))
            public_interfaces.extend(output.metadata.get("public_interfaces", []))
        
        variables = {
            "aggregated_summaries": aggregated,
            "dependency_graph": json.dumps(self._dependency_graph, indent=2),
            "doc_hints": doc_hints,
            "api_endpoints": api_endpoints,
            "public_interfaces": public_interfaces
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
                    "summary": o.local_summary,
                    "api_endpoints": o.metadata.get("api_endpoints", [])
                } for o in outputs],
                recommendations=result.get("recommended_docs", []),
                metadata={
                    "doc_hints": doc_hints,
                    "api_endpoints": api_endpoints,
                    "public_interfaces": public_interfaces
                }
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
    
    def _plan_documentation(
        self,
        user_request: str,
        project_context: str,
        file_summaries: Dict[str, str]
    ) -> EnhancedDocPlan:
        """
        根據使用者請求規劃文檔
        
        Args:
            user_request: 使用者請求
            project_context: 專案上下文
            file_summaries: 檔案摘要
            
        Returns:
            EnhancedDocPlan: 文檔規劃
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
            
            # 解析文檔任務
            tasks = []
            for task_data in result.get("documents", []):
                sections = [
                    DocumentSection.from_dict(s)
                    for s in task_data.get("sections", [])
                ]
                
                doc_type_str = task_data.get("doc_type", "readme")
                try:
                    doc_type = DocumentType(doc_type_str.lower())
                except ValueError:
                    doc_type = DocumentType.CUSTOM
                
                task = DocumentTask(
                    doc_type=doc_type,
                    title=task_data.get("title", ""),
                    description=task_data.get("description", ""),
                    sections=sections,
                    target_files=task_data.get("target_files", []),
                    style_guide=task_data.get("style_guide", {}),
                    priority=task_data.get("priority", 1)
                )
                tasks.append(task)
            
            # 解析需要的圖表
            charts_needed = []
            for chart_data in result.get("charts_needed", []):
                chart = ChartTask.from_dict(chart_data)
                charts_needed.append(chart)
            
            return EnhancedDocPlan(
                tasks=tasks,
                project_context=project_context,
                dependency_graph=self._dependency_graph,
                execution_order=list(range(len(tasks))),
                charts_needed=charts_needed
            )
            
        except Exception as e:
            self.log(f"Planning error: {e}")
            # 回傳預設規劃
            return self._create_default_plan(user_request, project_context, file_summaries)
    
    def _create_default_plan(
        self,
        user_request: str,
        project_context: str,
        file_summaries: Dict[str, str]
    ) -> EnhancedDocPlan:
        """
        建立預設文檔規劃
        
        Args:
            user_request: 使用者請求
            project_context: 專案上下文
            file_summaries: 檔案摘要
            
        Returns:
            EnhancedDocPlan: 預設規劃
        """
        # 預設 README 章節
        default_sections = [
            DocumentSection(
                title="Overview",
                description="Project introduction and purpose",
                content_type="overview",
                order=1
            ),
            DocumentSection(
                title="Installation",
                description="How to install and setup the project",
                content_type="installation",
                order=2
            ),
            DocumentSection(
                title="Usage",
                description="How to use the project",
                content_type="usage",
                order=3
            ),
            DocumentSection(
                title="Architecture",
                description="Project structure and architecture",
                content_type="architecture",
                source_files=list(file_summaries.keys())[:5],
                order=4
            )
        ]
        
        default_task = DocumentTask(
            doc_type=DocumentType.README,
            title="README.md",
            description=user_request,
            sections=default_sections,
            target_files=list(file_summaries.keys()),
            priority=1
        )
        
        return EnhancedDocPlan(
            tasks=[default_task],
            project_context=project_context,
            dependency_graph=self._dependency_graph,
            execution_order=[0]
        )
    
    def create_writer_input(self, task: DocumentTask) -> Dict[str, Any]:
        """
        為 DocWriter 建立輸入
        
        整合規劃結果，轉換為 DocWriter 可用的格式
        
        Args:
            task: 文檔任務
            
        Returns:
            dict: 給 DocWriter 的輸入
        """
        # 收集相關檔案內容
        relevant_contents = {}
        for file_path in task.target_files:
            if file_path in self._file_contents:
                relevant_contents[file_path] = self._file_contents[file_path]
        
        return {
            "task": task.to_dict(),
            "project_context": self._project_context,
            "dependency_graph": self._dependency_graph,
            "file_contents": relevant_contents,
            "style_guide": task.style_guide
        }
    
    @property
    def dependency_graph(self) -> Dict[str, List[str]]:
        """取得依賴圖"""
        return self._dependency_graph
    
    @property
    def project_context(self) -> str:
        """取得專案上下文"""
        return self._project_context
    
    @property
    def file_contents(self) -> Dict[str, str]:
        """取得已讀取的檔案內容"""
        return self._file_contents

