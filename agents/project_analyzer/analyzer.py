"""
Project Analyzer - Phase 1 Agent

"""
import json
import sys
import chardet
from datetime import datetime
from pathlib import Path
from config import config
from agents.base import BaseAgent
from agents.project_analyzer.picture_analyzer import PictureAnalyzer
from agents.project_analyzer.tool_docs import TOOL_DOCS
from utils import file_utils


class ProjectAnalyzer(BaseAgent):
    root_parent: str
    file_nodes: list[file_utils.FileNode]
    system_prompt: str
    user_prompt_base: str
    pic_analyzer: PictureAnalyzer
    dumps = []
    report = {}
    dump_file: str
    report_file: str
    _implements = {}

    @classmethod
    def execute(cls, project_path: str, **kwargs) -> None:
        pa = ProjectAnalyzer(
            root_dir=project_path,
            prompt_dir=config.prompts_dir/"project_analyzer",
            dump_file=Path(__file__).parent/"dump.json",
            report_file=Path(__file__).parent/"report.json"
        )
        retry_limit = kwargs.get("retry_limit") or 5
        for i in range(retry_limit):
            print(f"Retry: {i}" if i > 0 else "")
            try:
                pa.start(i>0)
                while not pa.report_done():
                    print("Trying get missed file(s)")
                    pa.start(True)
                print("All report generated")
            except KeyboardInterrupt:
                print("KeyboardInterrupt")
                return
            except:
                pass
    
    def _check_implement(self):
        for f in TOOL_DOCS:
            if not self._implements.get(f):
                raise NotImplementedError(f"function \"{f}\" has not been implemented")

    def __init__(self, root_dir:str, prompt_dir: str|Path, dump_file: str|Path, report_file: str|Path) -> None:
        super().__init__(
            name="ProjectAnalyzer",
            model=config.models.code_reader
        )
        self.dump_file = Path(dump_file).as_posix()
        self.report_file = Path(report_file).as_posix()
        self.root_parent = Path(root_dir).parent.as_posix()
        _file_tree = file_utils.build_file_tree(Path(root_dir).as_posix())
        if not _file_tree:
            raise FileNotFoundError("no file tree built")
        
        self.file_nodes = _file_tree.to_list()
        files = "\n".join([f"{node.relative_to(self.root_parent)}: {node}" for node in self.file_nodes])

        self.pic_analyzer = PictureAnalyzer(self.root_parent, Path(prompt_dir) / "picture.md")

        self.system_prompt = file_utils.read_file(Path(prompt_dir) / "system.md") + files
        self.user_prompt_base = file_utils.read_file(Path(prompt_dir) / "user.md")

        self._implements = {
            "read_file": self.read_file,
            "get_image_description": self.pic_analyzer.get_image_description,
            "report_summary": self.report_summary
        }

    def _get_file(self, path: str):
        abs_path = Path(path)
        if not abs_path.is_absolute():
            abs_path = Path(self.root_parent).joinpath(path)
        print(f"path: {path}, open: {abs_path}")
        raw_data = b""
        try:
            raw_data = abs_path.read_bytes()
            return raw_data.decode('utf-8')
        except FileNotFoundError:
            return "error: no such file"
        except UnicodeDecodeError:
            pass

        result = chardet.detect(raw_data)
        detected_encoding = result['encoding']
        confidence = result['confidence']
        
        if detected_encoding and confidence > 0.7:
            try:
                print(f"偵測到編碼: {detected_encoding} (信心度: {confidence})")
                return raw_data.decode(detected_encoding)
            except UnicodeDecodeError:
                pass
        
        print("警告：無法精確識別編碼。")
        return f"error: undetermined encode\nforced-binary-replace>>>>>\n" + str(raw_data)

    def read_file(self, file_path: str, n: int, **kwargs) -> str:
        text = self._get_file(file_path)
        if len(text) == 0:
            return "error: no text found"
        
        lines = [f"{line:.200s}{('...'+str(len(line)-200)+' more') if len(line)>200 else ''}".strip() for line in text.splitlines() if line.strip()]
    
        if n > 0:
            return "\n".join(lines[:n])
        else:
            return "\n".join(lines)
    
    def report_summary(self, path: str, is_important: bool, summary: str, **kwargs) -> None:
        self.report[path] = {"is_important": is_important, "summary": summary}

    def init_messages(self, node: file_utils.FileNode):
        return [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": f"<filepath>{node.relative_to(self.root_parent)}</filepath><objective>{self.user_prompt_base}</objective>"
            }
        ]
    
    def tools_call(self, tool_calls: list):
        reported = False
        for tool in tool_calls:
            tool_name = tool["function"]["name"]
            arguments = tool['function']['arguments']
            if tool_name == "report_summary":
                reported = True
            if tool_name in TOOL_DOCS:
                print(f"call: {tool_name} with {arguments}")
                self.add_tool_result(tool_name, self._implements[tool_name](**arguments))
            else:
                print(f"unknown tool: {tool_name}")
        return reported
    
    def load_report(self):
        if not Path(self.report_file).exists():
            return
        self.report = json.loads(file_utils.read_file(self.report_file))
        
    def report_done(self) -> bool:
        self.load_report()
        for node in self.file_nodes:
            if node.relative_to(self.root_parent) in self.report:
                return False
        return True
    
    def start(self, recovery_run = False):
        if recovery_run:
            self.load_report()
            print("recovery")
        self._check_implement()
        for node in self.file_nodes:
            if node.relative_to(self.root_parent) in self.report:
                print(f"continue: {node.path}")
                continue
            REPORTED = False
            self.messages = self.init_messages(node)
            while not REPORTED:
                print(f"thinking: {node.path}")
                self.dumps.append({"type":"request", "time":str(datetime.now()),"content":self.messages})
                response = self.chat_raw([], tools=[tool[1] for tool in TOOL_DOCS.items()], keep_history=True)
                self.dumps.append({"type":"response", "time":str(datetime.now()),"content":response.model_dump()})
                tool_calls = response["message"].get("tool_calls", None)
                if tool_calls is None:
                    break
                REPORTED = self.tools_call(tool_calls)
            
            file_utils.write_file(self.dump_file, json.dumps(self.dumps, indent=2))
            file_utils.write_file(self.report_file, json.dumps(self.report, indent=2))

        print("done")



if __name__ == "__main__":
    # ===================================
    root_dir = sys.argv[1]
    # ===================================
    ProjectAnalyzer.execute(root_dir)