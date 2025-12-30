"""
Project Analyzer - File Analyzer Worker

Worker Agent 用於分析單一檔案
"""
import json
import asyncio
from typing import Dict, List, Optional
from pathlib import Path

from config.agents import AgentName
from agents.base import BaseAgent
from agents.prompts import load_prompt
from agents.project_analyzer.models import FileInfo, FileAnalysisResult
from agents.project_analyzer.scanner import FileScanner
from agents.project_analyzer.image_worker import ImageWorker


# Worker 預設 timeout（秒）
WORKER_TIMEOUT = 120

# 檔案讀取每次行數
LINES_PER_READ = 100

# 最大讀取次數
MAX_READ_ROUNDS = 3


class FileAnalyzerWorker(BaseAgent):
    """
    Worker Agent - 分析單一檔案
    
    設計原則：
    - 先讀取前 LINES_PER_READ 行掃描
    - 若 LLM 需要更多內容，可請求讀取下一段
    - 最多讀取 MAX_READ_ROUNDS 輪
    - 產生簡短 1-2 句總結
    """
    
    PROMPT_NAME = "project_analyzer/file_worker"

    def __init__(self, root_dir: Path, image_worker: Optional[ImageWorker] = None):
        super().__init__(
            agent_name=AgentName.FILE_WORKER,
            display_name="FileWorker"
        )
        self.root_dir = root_dir
        self.image_worker = image_worker
        self._file_cache: Dict[str, List[str]] = {}
        
        # 載入 prompt
        prompt_data = load_prompt(self.PROMPT_NAME)
        self._system_prompt = prompt_data["system_prompt"]
        self._user_template = prompt_data.get("user_prompt_template", "")
    
    async def analyze(
        self,
        file_info: FileInfo,
        context: str = "",
        timeout: float = WORKER_TIMEOUT
    ) -> FileAnalysisResult:
        """分析單一檔案（帶 timeout）"""
        self.logger.debug(f"[FileWorker] 開始分析: {file_info.path} (timeout={timeout}s)")
        
        try:
            result = await asyncio.wait_for(
                self._analyze_internal(file_info, context),
                timeout=timeout
            )
            self.logger.debug(f"[FileWorker] 完成分析: {file_info.path} -> important={result.is_important}")
            return result
        except asyncio.TimeoutError:
            self.logger.warning(f"[FileWorker] Timeout: {file_info.path} (超過 {timeout}s)")
            return FileAnalysisResult(
                file_path=file_info.path,
                is_important=False,
                summary=f"[Analysis timeout after {timeout}s]",
                error="timeout"
            )
        except Exception as e:
            self.logger.error(f"[FileWorker] Error: {file_info.path} - {e}")
            return FileAnalysisResult(
                file_path=file_info.path,
                is_important=False,
                summary=f"[Analysis error: {e}]",
                error=str(e)
            )
    
    async def _analyze_internal(self, file_info: FileInfo, context: str) -> FileAnalysisResult:
        """內部分析邏輯"""
        ext = file_info.extension.lower()
        
        # 處理二進制檔案
        if ext in FileScanner.BINARY_EXTENSIONS:
            return self._analyze_binary_file(file_info)
        
        # 處理圖片
        if ext in FileScanner.IMAGE_EXTENSIONS:
            return await self._analyze_image(file_info)
        
        # 讀取並分析檔案
        try:
            return await self._analyze_with_progressive_read(file_info)
        except Exception as e:
            return FileAnalysisResult(
                file_path=file_info.path,
                is_important=False,
                summary=f"[Unable to read: {e}]",
                error=str(e)
            )
    
    def _analyze_binary_file(self, file_info: FileInfo) -> FileAnalysisResult:
        """分析二進制檔案"""
        ext = file_info.extension.lower()
        name = file_info.abs_path.name
        
        binary_types = {
            '.mid': 'MIDI music file',
            '.midi': 'MIDI music file',
            '.mp3': 'MP3 audio file',
            '.wav': 'WAV audio file',
            '.ogg': 'OGG audio file',
            '.mp4': 'MP4 video file',
            '.pdf': 'PDF document',
            '.zip': 'ZIP archive',
            '.exe': 'Windows executable',
            '.dll': 'Windows dynamic library',
            '.so': 'Shared object library',
            '.db': 'Database file',
        }
        
        file_type = binary_types.get(ext, 'Binary file')
        return FileAnalysisResult(
            file_path=file_info.path,
            is_important=False,
            summary=f"{file_type}: {name}"
        )
    
    async def _analyze_image(self, file_info: FileInfo) -> FileAnalysisResult:
        """分析圖片檔案"""
        if self.image_worker:
            try:
                response = await self.image_worker.get_image_description(str(file_info.abs_path))
                
                if response and not response.startswith("error"):
                    result = self._parse_image_response(response)
                    if result:
                        summary = f"Image ({result.get('type', 'Unknown')}): {result.get('summary', '')}"
                        return FileAnalysisResult(
                            file_path=file_info.path,
                            is_important=result.get('is_important', False),
                            summary=summary
                        )
                    return FileAnalysisResult(
                        file_path=file_info.path,
                        is_important=False,
                        summary=f"Image: {response}"
                    )
            except Exception as e:
                self.logger.warning(f"[FileWorker] 圖片分析失敗: {file_info.path} - {e}")
        
        return FileAnalysisResult(
            file_path=file_info.path,
            is_important=False,
            summary=f"Image file: {file_info.abs_path.name}"
        )
    
    def _parse_image_response(self, response: str) -> Optional[Dict]:
        """解析 image_reader 的 JSON 回應"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return None
    
    async def _analyze_with_progressive_read(self, file_info: FileInfo) -> FileAnalysisResult:
        """漸進式讀取並分析檔案"""
        file_path = file_info.abs_path
        
        # 讀取檔案內容
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                raw_lines = f.readlines()
        except Exception as e:
            return FileAnalysisResult(
                file_path=file_info.path,
                is_important=False,
                summary=f"[Read error: {e}]",
                error=str(e)
            )
        lines = []
        for line in raw_lines:
            if len(line.strip()) == 0:
                continue
            lines.append(line.strip())
        
        total_lines = len(lines)
        current_line = 0
        content_parts = []
        
        for round_num in range(MAX_READ_ROUNDS):
            end_line = min(current_line + LINES_PER_READ, total_lines)
            chunk = ''.join(lines[current_line:end_line])
            content_parts.append(chunk)
            
            if end_line >= total_lines:
                break
            
            current_line = end_line
        
        full_content = ''.join(content_parts)
        
        # 建立 prompt_suffix
        if end_line >= total_lines:
            prompt_suffix = "\n<EOF>"  # 已讀取完整檔案
        else:
            prompt_suffix = f"\n[Showing lines 1-{end_line} of {total_lines}...]"
        
        # 呼叫 LLM 分析
        user_prompt = self._user_template.format(
            file_path=file_info.path,
            content=full_content[:8000],
            prompt_suffix=prompt_suffix
        )
        
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_raw_async(messages, format="json", keep_history=False, options={'temperature': 0.3,'num_ctx': 2048})
        
        # 解析 JSON，失敗時重試
        result = await self._parse_json_with_retry(
            response.message.content or "",
            messages,
            max_retries=2
        )
        
        if result is None:
            # 解析失敗，使用原始回應作為 summary
            return FileAnalysisResult(
                file_path=file_info.path,
                is_important=False,
                summary=response.message.content[:200] if response.message.content else "",
                error="JSON parse failed"
            )
        
        return FileAnalysisResult(
            file_path=file_info.path,
            is_important=result.get("is_important", False),
            summary=result.get("summary", ""),
            dependencies=result.get("dependencies", []),
            key_elements=result.get("key_elements", [])
        )
    
    async def _parse_json_with_retry(
        self,
        text: str,
        messages: list,
        max_retries: int = 2
    ):
        """
        解析 JSON，失敗時請 LLM 重新回答
        
        Returns:
            解析後的 dict，或 None 如果失敗
        """
        current_text = text
        
        for attempt in range(max_retries + 1):
            try:
                return self.parse_json(current_text)
            except json.JSONDecodeError as e:
                if attempt >= max_retries:
                    self.logger.warning(f"[FileWorker] JSON 解析失敗 (max retries reached): {e}")
                    return None
                
                self.logger.debug(f"[FileWorker] JSON 解析失敗 (attempt {attempt + 1}), 請求重試...")
                
                # 請 LLM 重新回答
                fix_messages = messages + [
                    {"role": "assistant", "content": current_text},
                    {
                        "role": "user",
                        "content": f"Your response is not valid JSON. Error: {e}\n\nRespond with ONLY valid JSON in this format:\n{{\"summary\": \"...\", \"is_important\": true/false, \"dependencies\": [], \"key_elements\": []}}"
                    }
                ]
                
                try:
                    response = await self.chat_raw_async(
                        fix_messages,
                        format="json",
                        keep_history=False,
                        options={'temperature': 0.2,'num_ctx': 2048}
                    )
                    current_text = response.message.content or ""
                except Exception as retry_error:
                    self.logger.warning(f"[FileWorker] 重試請求失敗: {retry_error}")
                    return None
        
        return None
