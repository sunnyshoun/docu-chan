from pathlib import Path
import sys
from agents.analyzer.file_node import FileInfo
from agents.base_agent import BaseAgent

LINE_READ = 100

class CodeAnalyzer(BaseAgent):
    parent_dir: Path

    def __init__(self, root_dir: str|Path):
        super().__init__("CodeAnalyzer")
        _root = Path(root_dir)
        self.parent_dir = _root.parent

    def find_dependencies(self, target: FileInfo)->str:
        res = self.chat(
            [
                {
                    "role": "system",
                    "content": (self.prompt_dir/"find_dependencies.md").read_text()
                },
                {
                    "role": "user",
                    "content": f"Analyze \"{target.relative_to(self.parent_dir).as_posix()}\":\n" + target.read_text_line(LINE_READ)
                }
            ]
        )
        if not res.content:
            self.log(3, f"find_logics has no content: {target}")
            return ""
        return res.content

    def find_logics(self, target: FileInfo):
        file_path = target.relative_to(self.parent_dir).as_posix()
        src = target.read_text_line(LINE_READ)
        res = self.chat(
            [
                {
                    "role": "system",
                    "content": (self.prompt_dir/"find_logics.md").read_text()
                },
                {
                    "role": "user",
                    "content": f"Analyze \"{file_path}\":\n{src}"
                }
            ]
        )
        if not res.content:
            self.log(3, f"find_logics has no content: {target}")
            return ""
        return res.content

if __name__ == "__main__":
    al = CodeAnalyzer(sys.argv[1])
    c = al.find_logics(FileInfo(sys.argv[2]))
    print(c)
