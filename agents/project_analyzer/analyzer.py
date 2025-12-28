"""
Project Analyzer - Phase 1 Agent

分析專案檔案並產生摘要。
"""
import json
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from config.settings import get_config
from agents.base import BaseAgent
from agents.prompts import load_prompt
from agents.project_analyzer.picture_analyzer import PictureAnalyzer
from utils import file_utils
from tools import get_tools, execute
from tools.file_ops import set_project_root, get_reports, clear_reports


class ProjectAnalyzer(BaseAgent):
    """專案分析器 - 分析每個檔案並產生摘要"""
    
    def __init__(self, root_dir: str, prompt_dir: str, dump_file: str, report_file: str) -> None:
        super().__init__(
            name="ProjectAnalyzer",
            model=get_config().models.code_reader
        )
        
        self.root_dir = Path(root_dir).resolve()
        self.dump_file = dump_file
        self.report_file = report_file
        self.dumps = []
        self.report = {}
        
        # 設定 tools 的專案根目錄
        set_project_root(str(self.root_dir))
        
        # 初始化圖片分析器
        self.pic_analyzer = PictureAnalyzer(
            base=str(self.root_dir.parent),
            prompt_file=Path(prompt_dir) / "image_reader.json"
        )
        
        # 建立檔案樹
        file_tree = file_utils.build_file_tree(str(self.root_dir))
        if not file_tree:
            raise FileNotFoundError(f"Cannot build file tree for: {root_dir}")
        
        self.file_nodes = file_tree.to_list()
        
        # 載入 prompt
        prompt_data = load_prompt("project_analyzer/project_analyzer")
        file_list = "\n".join([
            f"- {node.relative_to(str(self.root_dir.parent))}" 
            for node in self.file_nodes
        ])
        
        self.system_prompt = prompt_data["system_prompt"] + "\n\n" + file_list
        self.user_template = prompt_data["user_prompt_template"]
        
        # 取得 tool definitions
        self.tool_definitions = get_tools("read_file", "report_summary", "get_image_description")
    
    def execute(self, project_path: str, **kwargs) -> Dict[str, Any]:
        """執行分析（透過 start 方法）"""
        self.start()
        return {"report": self.report}
    
    def start(self, max_retries: int = 3):
        """開始分析所有檔案"""
        clear_reports()
        
        for node in self.file_nodes:
            file_path = node.relative_to(str(self.root_dir.parent))
            
            # 跳過已分析的檔案
            if file_path in self.report:
                print(f"[skip] \"{file_path}\"")
                continue
            
            print(f"[analyze] \"{file_path}\"")
            
            # 初始化對話
            self.messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.user_template.format(file_path=file_path)}
            ]
            
            # 呼叫 LLM
            reported = False
            retry_count = 0
            
            while not reported:
                self.dumps.append({
                    "type": "request",
                    "time": str(datetime.now()),
                    "file": file_path
                })
                
                try:
                    response = self.chat_raw([], tools=self.tool_definitions, keep_history=True)
                except Exception as e:
                    retry_count += 1
                    print(f"  [error] {e}")
                    
                    if retry_count >= max_retries:
                        print(f"  [failed] Max retries reached, skipping...")
                        self.report[file_path] = {
                            "is_important": False,
                            "summary": f"[Analysis failed: {e}]"
                        }
                        break
                    
                    print(f"  [retry] {retry_count}/{max_retries}")
                    continue
                
                self.dumps.append({
                    "type": "response",
                    "time": str(datetime.now()),
                    "content": response.model_dump() if hasattr(response, 'model_dump') else str(response)
                })
                
                # 處理 tool calls
                tool_calls = response.get("message", {}).get("tool_calls")
                if not tool_calls:
                    break
                
                reported = self._handle_tool_calls(tool_calls, file_path)
            
            # 儲存進度
            self._save_progress()
        
        # 從 tools 收集報告
        self.report.update(get_reports())
        self._save_progress()
        print("[done] Analysis complete")
    
    def _handle_tool_calls(self, tool_calls: list, current_file: str) -> bool:
        """處理 tool calls，回傳是否已回報摘要"""
        reported = False
        
        for tool in tool_calls:
            tool_name = tool["function"]["name"]
            arguments = tool["function"]["arguments"]
            
            print(f"  [tool] {tool_name}")
            
            if tool_name == "report_summary":
                reported = True
                # 直接儲存到 report
                self.report[arguments.get("path", current_file)] = {
                    "is_important": arguments.get("is_important", False),
                    "summary": arguments.get("summary", "")
                }
                self.add_tool_result(tool_name, "Reported successfully")
            elif tool_name == "get_image_description":
                # 使用 PictureAnalyzer 分析圖片
                try:
                    image_path = arguments.get("image_path", "")
                    result = self.pic_analyzer.get_image_description(image_path)
                    self.add_tool_result(tool_name, result)
                except Exception as e:
                    self.add_tool_result(tool_name, f"Error: {e}")
            else:
                # 執行 tool
                try:
                    result = execute(tool_name, **arguments)
                    self.add_tool_result(tool_name, str(result) if result else "OK")
                except Exception as e:
                    self.add_tool_result(tool_name, f"Error: {e}")
        
        return reported
    
    def _save_progress(self):
        """儲存分析進度"""
        file_utils.write_file(self.dump_file, json.dumps(self.dumps, indent=2))
        file_utils.write_file(self.report_file, json.dumps(self.report, indent=2))