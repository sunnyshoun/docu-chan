import json
import logging
import sys
import random
from pathlib import Path
from agents.analyzer.code_analyzer import CodeAnalyzer
from agents.analyzer.file_node import FileInfo
from agents.analyzer.image_analyzer import ImageAnalyzer
from agents.analyzer.summarize import Summarize
from agents.base_agent import BaseAgent


class ProjectAnalyzer(BaseAgent):
    parent_dir: Path
    file_list: list[FileInfo]
    code_analyzer: CodeAnalyzer
    image_analyzer: ImageAnalyzer
    summarize: Summarize
    impression: str
    dependency_reports: dict[str, str] = {}
    logic_reports: dict[str, str] = {}

    def __init__(self, project_dir: str | Path):
        super().__init__("ProjectAnalyzer")
        _root = Path(project_dir).absolute()
        self.log(2, f"current project: {_root.as_posix()}")
        self.file_list = FileInfo.build_file_list(_root)
        self.code_analyzer = CodeAnalyzer(_root)
        self.image_analyzer = ImageAnalyzer(_root)
        self.summarize = Summarize(_root)
        self.parent_dir = _root.parent

    def dumps_report(self):
        d = "# impression\n"
        d += f"{self.impression}\n"
        for f in self.file_list:
            key = f.relative_to(self.parent_dir).as_posix()
            d += f"# {key}\n"
            if key in self.dependency_reports:
                d += f"{self.dependency_reports[key]}\n"
            if key in self.logic_reports:
                d += f"{self.logic_reports[key]}\n"

        (self.log_dir / "dumps.md").write_text(d, encoding="utf-8")
        (self.log_dir / "file_list.json").write_text(json.dumps([self.impression]+[f.path.as_posix() for f in self.file_list], indent=2), encoding="utf-8")
        (self.log_dir / "dependency_reports.json").write_text(json.dumps(self.dependency_reports, indent=2), encoding="utf-8")
        (self.log_dir / "logic_reports.json").write_text(json.dumps(self.logic_reports, indent=2), encoding="utf-8")

    def load(self):
        file_list = json.loads((self.log_dir / "file_list.json").read_bytes())
        self.impression = file_list[0]
        self.file_list = [FileInfo(f) for f in file_list[1:]]
        self.dependency_reports = json.loads((self.log_dir / "dependency_reports.json").read_bytes())
        self.logic_reports = json.loads((self.log_dir / "logic_reports.json").read_bytes())

    def run(self):
        self.impression = self._pre_analyze()
        self.code_analyzer.impression = self.impression
        self.image_analyzer.impression = self.impression
        for i, f in enumerate(self.file_list):
            print(f"{i}/{len(self.file_list)} {f}")
            key = f.relative_to(self.parent_dir).as_posix()
            self.log(2, f"per file report {key}")
            if f.is_image:
                self.dependency_reports[key] = self.image_analyzer.find_dependencies(f)
                self.logic_reports[key] = self.image_analyzer.find_logics(f)
            elif f.is_text:
                self.dependency_reports[key] = self.code_analyzer.find_dependencies(f)
                self.logic_reports[key] = self.code_analyzer.find_logics(f)
            else:
                print(f"{'='*10}skip{'='*10}\n{f}\n{'='*24}")
        self.dumps_report()
        # dep = self.summarize.sum_reports(self.dependency_reports)
        # flow = self.summarize.sum_reports(self.logic_reports)
        # Path("dep.md").write_text(dep, encoding="utf-8")
        # Path("flow.md").write_text(flow, encoding="utf-8")
    
    def _pre_analyze(self) -> str:
        self.log(2, f"pre analyze")
        files_str = ""
        for f in self.file_list:
            files_str += f"{"DIR: " if f.is_dir else "FILE:"} {f.relative_to(self.parent_dir)}, type:{f.file_type}\n"
        imp = self.chat(
            [
                {
                    "role": "user",
                    "content": (self.prompt_dir/"pre_analyze.md").read_text().format(files_str)
                }
            ]
        )
        if not imp.content:
            self.log(3, f"pre_analyze has no content")
            return ""
        return imp.content
    
if __name__ == "__main__":
    logging.basicConfig(filename='.log', level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
    al = ProjectAnalyzer(sys.argv[1])
    c = al.run()
    print(c)
