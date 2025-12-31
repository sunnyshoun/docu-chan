from pathlib import Path
import sys
from agents.analyzer.code_analyzer import CodeAnalyzer
from agents.analyzer.file_node import FileInfo
from agents.base_agent import BaseAgent


class ProjectAnalyzer(BaseAgent):
    parent_dir: Path
    file_list: list[FileInfo]
    code_analyzer: CodeAnalyzer
    report: dict[str, str] = {}
    def __init__(self, project_dir: str | Path):
        super().__init__("ProjectAnalyzer")
        _root = Path(project_dir)
        self.file_list = FileInfo.build_file_list(_root)
        self.code_analyzer = CodeAnalyzer(_root)
        self.parent_dir = _root.parent

    def dumps_report(self) -> str:
        d = "# impression\n"
        d += self.report.get("impression", "Err: no content") + "\n"
        for f in self.file_list:
            key = f.relative_to(self.parent_dir).as_posix()
            if not key in self.report:
                continue
            d += f"# {key}\n{self.report[key]}\n"

        return d

    def run(self):
        self.report["impression"] = self.impression()
        print(self.report["impression"])
        Path("dumps.md").write_text(self.dumps_report(), encoding="utf-8")
        
        for f in self.file_list:
            r = ""
            if f.is_dir:
                continue
            elif f.is_image:
                r += self.read_image(f) + "\n"
            elif f.is_text:
                r += self.code_analyzer.find_dependencies(f) + "\n"
                r += self.code_analyzer.find_logics(f) + "\n"
            else:
                r = f"Unexpected file: {f}\n"
            self.report[f.relative_to(self.parent_dir).as_posix()] = r
            Path("dumps.md").write_text(self.dumps_report(), encoding="utf-8")
            
    
    def impression(self) -> str:
        files_str = ""
        for f in self.file_list:
            files_str += f"{"DIR: " if f.is_dir else "FILE:"} {f.relative_to(self.parent_dir)}, type:{f.file_type}\n"
        imp = self.chat(
            [
                {
                    "role": "user",
                    "content": (self.prompt_dir/"impression.md").read_text().format(files_str)
                }
            ]
        )
        if not imp.content:
            self.log(3, f"impression has no content")
            return ""
        return imp.content

    def read_image(self, image: FileInfo) -> str:
        res = self.chat(
            [
                {
                    "role": "system",
                    "content": (self.prompt_dir/"read_image.md").read_text()
                },
                {
                    "role": "user",
                    "content": f"Analyze \"{image.relative_to(self.parent_dir).as_posix()}\"",
                    "images": [image.read_base64()]
                }
            ]
        )
        if not res.content:
            self.log(3, f"read_image has no content: {image}")
            return ""
        return res.content
    
if __name__ == "__main__":
    al = ProjectAnalyzer(sys.argv[1])
    c = al.run()
    print(c)
