from pathlib import Path
from agents.analyzer.file_node import FileInfo
from agents.base_agent import BaseAgent

class Summarize(BaseAgent):
    parent_dir: Path

    def __init__(self, parent_dir: str | Path):
        super().__init__("Summarize")
        self.parent_dir = Path(parent_dir)

    def sum_reports(self, reports: dict[str, str]) -> str:
        sum = ""
        for f, r in reports.items():
            key = Path(f).relative_to(self.parent_dir).as_posix()
            self.log(2, f"analyze dependencies {key}")
            ret = self.chat(
                [
                    {
                        "role": "system",
                        "content": (Path(self.prompt_dir)/"system_template.md").read_text().format(sum)
                    },
                    {
                        "role": "user",
                        "content": f"# {key}\n# **report**\n{r}"
                    }
                ]
            )
            sum = ret.content or ""
            print(sum)
        return sum
    
    