"""
Chain of Agents (CoA) 工具模組

實作 Google 提出的 CoA 架構，用於處理長文本。
CoA 使用多個 Worker Agent 處理不同片段，再由 Manager 整合結果。

架構說明：
1. Worker: 處理單一檔案/片段，產生 local summary 和 communication unit
2. Manager: 整合所有 Worker 的 communication units，產生最終結果
3. 支援 sequential 和 parallel 兩種處理模式
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import asyncio


@dataclass
class CoAChunk:
    """CoA 處理的單一片段"""
    chunk_id: int
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_file: str = ""
    

@dataclass
class WorkerOutput:
    """Worker 處理結果"""
    worker_id: int
    chunk_id: int
    local_summary: str
    communication_unit: str
    source_file: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "chunk_id": self.chunk_id,
            "local_summary": self.local_summary,
            "communication_unit": self.communication_unit,
            "source_file": self.source_file,
            "metadata": self.metadata
        }


@dataclass
class ManagerOutput:
    """Manager 整合結果"""
    final_summary: str
    aggregated_insights: List[Dict[str, Any]]
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "final_summary": self.final_summary,
            "aggregated_insights": self.aggregated_insights,
            "recommendations": self.recommendations,
            "metadata": self.metadata
        }


class CoAProcessor:
    """
    Chain of Agents 處理器
    
    用法：
    ```python
    processor = CoAProcessor(
        worker_fn=my_worker_function,
        manager_fn=my_manager_function
    )
    result = await processor.process(chunks)
    ```
    """
    
    def __init__(
        self,
        worker_fn: Callable[[CoAChunk, int, Optional[str]], WorkerOutput],
        manager_fn: Callable[[List[WorkerOutput]], ManagerOutput],
        max_workers: int = 5,
        sequential: bool = True
    ):
        """
        初始化 CoA 處理器
        
        Args:
            worker_fn: Worker 處理函數，接收 (chunk, worker_id, prev_comm_unit)
            manager_fn: Manager 整合函數，接收所有 WorkerOutputs
            max_workers: 最大並行 Worker 數量
            sequential: 是否順序處理（用於需要前文關聯的情況）
        """
        self.worker_fn = worker_fn
        self.manager_fn = manager_fn
        self.max_workers = max_workers
        self.sequential = sequential
    
    def process(self, chunks: List[CoAChunk]) -> ManagerOutput:
        """
        同步處理多個片段
        
        Args:
            chunks: 待處理片段列表
            
        Returns:
            ManagerOutput: 整合後的結果
        """
        if self.sequential:
            worker_outputs = self._process_sequential(chunks)
        else:
            worker_outputs = self._process_parallel(chunks)
        
        return self.manager_fn(worker_outputs)
    
    async def process_async(self, chunks: List[CoAChunk]) -> ManagerOutput:
        """
        非同步處理多個片段
        
        Args:
            chunks: 待處理片段列表
            
        Returns:
            ManagerOutput: 整合後的結果
        """
        if self.sequential:
            worker_outputs = await self._process_sequential_async(chunks)
        else:
            worker_outputs = await self._process_parallel_async(chunks)
        
        return self.manager_fn(worker_outputs)
    
    def _process_sequential(self, chunks: List[CoAChunk]) -> List[WorkerOutput]:
        """順序處理 - 前一個 Worker 的 communication unit 傳遞給下一個"""
        outputs: List[WorkerOutput] = []
        prev_comm_unit: Optional[str] = None
        
        for i, chunk in enumerate(chunks):
            output = self.worker_fn(chunk, i, prev_comm_unit)
            outputs.append(output)
            prev_comm_unit = output.communication_unit
        
        return outputs
    
    def _process_parallel(self, chunks: List[CoAChunk]) -> List[WorkerOutput]:
        """並行處理 - 無前文關聯"""
        outputs: List[WorkerOutput] = []
        
        for i, chunk in enumerate(chunks):
            output = self.worker_fn(chunk, i, None)
            outputs.append(output)
        
        return outputs
    
    async def _process_sequential_async(
        self, 
        chunks: List[CoAChunk]
    ) -> List[WorkerOutput]:
        """非同步順序處理"""
        outputs: List[WorkerOutput] = []
        prev_comm_unit: Optional[str] = None
        
        for i, chunk in enumerate(chunks):
            # 如果 worker_fn 是 async
            if asyncio.iscoroutinefunction(self.worker_fn):
                output = await self.worker_fn(chunk, i, prev_comm_unit)
            else:
                output = self.worker_fn(chunk, i, prev_comm_unit)
            outputs.append(output)
            prev_comm_unit = output.communication_unit
        
        return outputs
    
    async def _process_parallel_async(
        self, 
        chunks: List[CoAChunk]
    ) -> List[WorkerOutput]:
        """非同步並行處理"""
        if asyncio.iscoroutinefunction(self.worker_fn):
            tasks = [
                self.worker_fn(chunk, i, None)
                for i, chunk in enumerate(chunks)
            ]
            return await asyncio.gather(*tasks)
        else:
            return self._process_parallel(chunks)


def create_file_chunks(
    file_summaries: Dict[str, str],
    file_contents: Optional[Dict[str, str]] = None,
    entry_points: Optional[List[str]] = None
) -> List[CoAChunk]:
    """
    從檔案摘要建立 CoA 片段
    
    Args:
        file_summaries: 檔案路徑 -> 摘要 的映射
        file_contents: 檔案路徑 -> 完整內容 的映射（可選）
        entry_points: 入口檔案列表（這些會排在前面）
        
    Returns:
        List[CoAChunk]: 排序後的片段列表
    """
    chunks: List[CoAChunk] = []
    processed: set = set()
    chunk_id = 0
    
    # 先處理 entry points
    if entry_points:
        for entry in entry_points:
            if entry in file_summaries:
                content = file_contents.get(entry, "") if file_contents else ""
                chunks.append(CoAChunk(
                    chunk_id=chunk_id,
                    content=f"[Summary]\n{file_summaries[entry]}\n\n[Content]\n{content}",
                    metadata={"is_entry_point": True},
                    source_file=entry
                ))
                processed.add(entry)
                chunk_id += 1
    
    # 處理其餘檔案
    for file_path, summary in file_summaries.items():
        if file_path not in processed:
            content = file_contents.get(file_path, "") if file_contents else ""
            chunks.append(CoAChunk(
                chunk_id=chunk_id,
                content=f"[Summary]\n{summary}\n\n[Content]\n{content}",
                metadata={"is_entry_point": False},
                source_file=file_path
            ))
            chunk_id += 1
    
    return chunks


def aggregate_worker_outputs(outputs: List[WorkerOutput]) -> str:
    """
    將多個 Worker 輸出聚合成單一文本
    
    Args:
        outputs: Worker 輸出列表
        
    Returns:
        str: 聚合後的文本
    """
    parts = []
    
    for output in outputs:
        part = f"## {output.source_file or f'Chunk {output.chunk_id}'}\n"
        part += f"### Summary\n{output.local_summary}\n"
        part += f"### Key Insights\n{output.communication_unit}\n"
        parts.append(part)
    
    return "\n---\n".join(parts)
