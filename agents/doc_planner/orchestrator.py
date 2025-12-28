"""
Planner Orchestrator - 規劃協調器

負責：
1. 協調 ChartPlanner 和 DocPlanner
2. 解析使用者請求，分配給適當的 Planner
3. 處理多個文件/圖表請求
4. 整合規劃結果，傳遞給下游 Generator
"""
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from config.settings import get_config
from agents.base import BaseAgent
from models import (
    ChartPlan, EnhancedDocPlan, PlannerResult,
    ChartTask, DocumentTask, ChartType, DocumentType
)
from .chart_planner import ChartPlanner
from .planner import DocPlanner


class RequestType:
    """請求類型"""
    CHART = "chart"
    DOCUMENT = "document"
    MIXED = "mixed"


class PlannerOrchestrator(BaseAgent):
    """
    規劃協調器
    
    整合 ChartPlanner 和 DocPlanner，處理使用者的複合請求
    
    使用流程：
    1. 解析使用者請求，識別需要的圖表和文件
    2. 將請求分配給 ChartPlanner 和 DocPlanner
    3. 整合規劃結果
    4. 輸出 PlannerResult 供下游使用
    
    Example:
        ```python
        orchestrator = PlannerOrchestrator()
        result = orchestrator.execute(
            file_summaries={"main.py": "..."},
            user_request="生成專案架構圖和 README 文件",
            project_path="/path/to/project"
        )
        ```
    """
    
    PROMPT_PARSE_REQUEST = "doc_planner/parse_request"
    
    def __init__(
        self,
        model: Optional[str] = None,
        chart_planner: Optional[ChartPlanner] = None,
        doc_planner: Optional[DocPlanner] = None
    ):
        config = get_config()
        super().__init__(
            name="PlannerOrchestrator",
            model=model or config.models.doc_planner,
            think=False
        )
        self.chart_planner = chart_planner or ChartPlanner()
        self.doc_planner = doc_planner or DocPlanner()
        self._last_result: Optional[PlannerResult] = None
    
    def execute(
        self,
        file_summaries: Dict[str, str],
        user_request: str,
        project_path: str,
        entry_points: Optional[List[str]] = None,
        **kwargs
    ) -> PlannerResult:
        """
        執行規劃協調
        
        Args:
            file_summaries: 檔案路徑 -> 摘要 的映射
            user_request: 使用者請求（可能包含多個需求）
            project_path: 專案根目錄路徑
            entry_points: 入口點檔案列表
            
        Returns:
            PlannerResult: 整合後的規劃結果
        """
        self.log(f"Orchestrating planning for: {user_request[:100]}...")
        
        # Step 1: 解析使用者請求
        parsed = self._parse_request(user_request)
        request_type = parsed["type"]
        chart_requests = parsed.get("chart_requests", [])
        doc_requests = parsed.get("doc_requests", [])
        
        self.log(f"Request type: {request_type}")
        self.log(f"Chart requests: {len(chart_requests)}")
        self.log(f"Doc requests: {len(doc_requests)}")
        
        # Step 2: 執行規劃
        chart_plan = None
        doc_plan = None
        
        if request_type in [RequestType.CHART, RequestType.MIXED]:
            if chart_requests:
                # 為每個圖表請求執行 ChartPlanner
                chart_request = "\n".join(chart_requests)
                chart_plan = self.chart_planner.execute(
                    file_summaries=file_summaries,
                    user_request=chart_request,
                    project_path=project_path,
                    entry_points=entry_points
                )
        
        if request_type in [RequestType.DOCUMENT, RequestType.MIXED]:
            if doc_requests:
                # 為每個文件請求執行 DocPlanner
                doc_request = "\n".join(doc_requests)
                doc_plan = self.doc_planner.execute(
                    file_summaries=file_summaries,
                    user_request=doc_request,
                    project_path=project_path,
                    entry_points=entry_points
                )
        
        # Step 3: 整合結果
        result = PlannerResult(
            chart_plan=chart_plan,
            doc_plan=doc_plan,
            project_summary=self._get_project_summary(),
            entry_points=entry_points or [],
            file_summaries=file_summaries
        )
        
        self._last_result = result
        return result
    
    def _parse_request(self, user_request: str) -> Dict[str, Any]:
        """
        解析使用者請求，識別圖表和文件需求
        
        Args:
            user_request: 使用者請求
            
        Returns:
            dict: 包含 type, chart_requests, doc_requests
        """
        # 圖表關鍵字
        chart_keywords = [
            'flowchart', 'flow chart', '流程圖',
            'sequence diagram', '時序圖', '序列圖',
            'class diagram', '類別圖', '類圖',
            'architecture diagram', '架構圖',
            'er diagram', 'erd', 'entity relationship',
            'state diagram', '狀態圖',
            'mindmap', 'mind map', '心智圖',
            'api diagram', 'api 圖', '接口圖',
            'chart', 'diagram', '圖表', '圖'
        ]
        
        # 文件關鍵字
        doc_keywords = [
            'readme', 'documentation', 'document', '文檔', '文件',
            'api doc', 'api documentation', 'api 說明', 'api文檔',
            'guide', 'tutorial', '指南', '教程',
            'changelog', '更新日誌',
            'installation', 'setup', '安裝', '設置',
            'component doc', '組件說明', '模組說明',
            'developer guide', '開發者指南'
        ]
        
        user_lower = user_request.lower()
        
        has_chart = any(kw in user_lower for kw in chart_keywords)
        has_doc = any(kw in user_lower for kw in doc_keywords)
        
        # 使用 LLM 更精確地解析
        try:
            response = self.chat(
                prompt_name=self.PROMPT_PARSE_REQUEST,
                variables={"user_request": user_request},
                keep_history=False
            )
            
            result = self.parse_json(response.message.content)
            
            chart_requests = result.get("chart_requests", [])
            doc_requests = result.get("doc_requests", [])
            
            if chart_requests and doc_requests:
                request_type = RequestType.MIXED
            elif chart_requests:
                request_type = RequestType.CHART
            elif doc_requests:
                request_type = RequestType.DOCUMENT
            else:
                # 預設根據關鍵字判斷
                if has_chart and has_doc:
                    request_type = RequestType.MIXED
                elif has_chart:
                    request_type = RequestType.CHART
                else:
                    request_type = RequestType.DOCUMENT
                
                chart_requests = [user_request] if has_chart else []
                doc_requests = [user_request] if has_doc or not has_chart else []
            
            return {
                "type": request_type,
                "chart_requests": chart_requests,
                "doc_requests": doc_requests
            }
            
        except Exception as e:
            self.log(f"Parse error: {e}, using fallback")
            
            # Fallback 解析
            if has_chart and has_doc:
                return {
                    "type": RequestType.MIXED,
                    "chart_requests": [user_request],
                    "doc_requests": [user_request]
                }
            elif has_chart:
                return {
                    "type": RequestType.CHART,
                    "chart_requests": [user_request],
                    "doc_requests": []
                }
            else:
                return {
                    "type": RequestType.DOCUMENT,
                    "chart_requests": [],
                    "doc_requests": [user_request]
                }
    
    def _get_project_summary(self) -> str:
        """取得專案摘要"""
        # 優先使用 DocPlanner 的摘要（通常更詳細）
        if self.doc_planner.project_context:
            return self.doc_planner.project_context
        elif self.chart_planner.project_context:
            return self.chart_planner.project_context
        return ""
    
    def get_chart_tasks(self) -> List[ChartTask]:
        """取得所有圖表任務"""
        if self._last_result and self._last_result.chart_plan:
            return self._last_result.chart_plan.tasks
        return []
    
    def get_doc_tasks(self) -> List[DocumentTask]:
        """取得所有文件任務"""
        if self._last_result and self._last_result.doc_plan:
            return self._last_result.doc_plan.tasks
        return []
    
    def get_all_charts_needed(self) -> List[ChartTask]:
        """取得所有需要的圖表（包含文件中嵌入的）"""
        charts = []
        
        # 從 ChartPlan 取得
        if self._last_result and self._last_result.chart_plan:
            charts.extend(self._last_result.chart_plan.tasks)
        
        # 從 DocPlan 取得（文件中需要的圖表）
        if self._last_result and self._last_result.doc_plan:
            charts.extend(self._last_result.doc_plan.charts_needed)
        
        return charts
    
    def create_execution_plan(self) -> List[Dict[str, Any]]:
        """
        建立執行計畫
        
        回傳依優先序排列的任務列表
        
        Returns:
            List[dict]: 執行計畫，每項包含 type, task, dependencies
        """
        execution_plan = []
        
        # 先執行圖表任務（因為文件可能需要嵌入圖表）
        chart_tasks = self.get_all_charts_needed()
        for i, task in enumerate(chart_tasks):
            execution_plan.append({
                "type": "chart",
                "task": task.to_dict(),
                "task_id": f"chart_{i}",
                "priority": task.priority,
                "dependencies": []
            })
        
        # 再執行文件任務
        doc_tasks = self.get_doc_tasks()
        for i, task in enumerate(doc_tasks):
            # 文件可能依賴圖表
            dependencies = [f"chart_{j}" for j in range(len(chart_tasks))]
            
            execution_plan.append({
                "type": "document",
                "task": task.to_dict(),
                "task_id": f"doc_{i}",
                "priority": task.priority,
                "dependencies": dependencies
            })
        
        # 按優先級排序
        execution_plan.sort(key=lambda x: x["priority"], reverse=True)
        
        return execution_plan
    
    @property
    def last_result(self) -> Optional[PlannerResult]:
        """取得最後的規劃結果"""
        return self._last_result
