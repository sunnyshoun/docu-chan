"""
Project Analyzer - Analysis Manager

Manager Agent 用於整合所有 Worker 的分析結果
"""
import json
import asyncio
from typing import Dict, Any, List, Tuple

from config.agents import AgentName
from agents.base import BaseAgent
from agents.prompts import load_prompt
from agents.project_analyzer.models import FileAnalysisResult, ProjectContext


class AnalysisManager(BaseAgent):
    """
    Manager Agent - 整合所有 Worker 的分析結果
    
    職責：
    1. 收集所有 Worker 的結果
    2. 識別跨檔案的關係與依賴
    3. 調整重要性評估（基於全局視角）
    4. 產生最終的專案分析報告
    """
    
    PROMPT_NAME = "project_analyzer/analysis_manager"

    def __init__(self):
        super().__init__(
            agent_name=AgentName.ANALYSIS_MANAGER,
            display_name="AnalysisManager"
        )
        
        # 載入 prompt
        prompt_data = load_prompt(self.PROMPT_NAME)
        self._system_prompt = prompt_data["system_prompt"]
        self._user_template = prompt_data.get("user_prompt_template", "")
    
    async def aggregate(
        self,
        results: List[FileAnalysisResult],
        context: ProjectContext,
        timeout: float = 240
    ) -> Tuple[Dict[str, Dict], Dict[str, Any]]:
        """整合分析結果"""
        try:
            return await asyncio.wait_for(
                self._aggregate_internal(results, context), timeout=timeout
            )
        except asyncio.TimeoutError:
            self.log("Manager aggregation timeout", "warning")
            return self._fallback_aggregate(results), {}
        except Exception as e:
            self.log(f"Manager aggregation error: {e}", "error")
            return self._fallback_aggregate(results), {}
    
    async def _aggregate_internal(
        self, results: List[FileAnalysisResult], context: ProjectContext
    ) -> Tuple[Dict[str, Dict], Dict[str, Any]]:
        """內部整合邏輯"""
        
        summary_text = "#files summary\n"
        for r in results:
            summary_text += f"## {r.file_path}\n"
            summary_text += "this file may " "" if r.is_important else "not " "be important\n"
            summary_text += f"### summary\n{r.summary}\n"
            deps = "\n".join([f'- {dep}' for dep in r.dependencies])
            elements = "\n".join([f'- {dep}' for dep in r.key_elements])
            summary_text += f"### dependencies\n{deps}\n"
            summary_text += f"### elements\n{elements}\n---\n"
        
        user_prompt = self._user_template.format(
            file_tree=context.file_tree_str,
            summary_text=summary_text
        )
        
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await self.chat_raw_async(messages, format="json", keep_history=False, options={'temperature': 0.2,'num_ctx': 64000})
        full_content = response.message.content
        
        manager_result = self.parse_json(full_content)
        metadata = {
            "project_summary": manager_result.get("project_summary", ""),
            "project_type": manager_result.get("project_type", ""),
            "entry_points": manager_result.get("entry_points", []),
            "core_components": manager_result.get("core_components", [])
        }
        print(json.dumps(metadata, indent=2))
        
        detail = await self.chat_raw_async(
            [{"role": "user", "content":"You are a senior engineer, your goal is to compose the whole project form per-file summary."}, {"role": "user", "content": "Consider these files, identify the purpose, then describe every logics, behaviors in detail.\n"+summary_text}],
            format="json", keep_history=False, options={'temperature': 0.2,'num_ctx': 64000}
        )
        if detail.message.content:
            metadata["project_summary"] = detail.message.content
        final_report = {r.file_path: {"is_important": r.is_important, "summary": r.summary} for r in results}
        
        print(json.dumps(metadata, indent=2))
        return final_report, metadata
    
    def _fallback_aggregate(self, results: List[FileAnalysisResult]) -> Dict[str, Dict]:
        """Fallback：直接使用 Worker 結果"""
        return {r.file_path: {"is_important": r.is_important, "summary": r.summary} for r in results}
