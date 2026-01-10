import sys
import logging
from agents.planner import tool_schema, tools
from agents.analyzer.project_analyzer import ProjectAnalyzer
from agents.base_agent import BaseAgent

class DocumentPlanner(BaseAgent):
    impression: str
    user_query: str
    
    def __init__(self, user_query: str, impression: str):
        super().__init__("DocumentPlanner")
        self.user_query = user_query
        self.impression = impression
    
    def run(self):
        self.log(2, f"Starting document planning for query: {self.user_query}")
        
        response = self.chat(
            [
                {
                    "role": "system",
                    "content": (self.prompt_dir/"system_prompt.md").read_text()
                },
                {
                    "role": "user",
                    "content": (self.prompt_dir/"user_prompt.md").read_text().format(self.user_query, self.impression)
                }
            ],
            tools=[tool_schema.save_plan]
        )
        
        plan_dir = self.log_dir / "plans"
        if plan_dir.exists():
            for f in plan_dir.iterdir():
                f.unlink()
            plan_dir.rmdir()
        plan_dir.mkdir()
        
        dump_content = ""
        plan_number = 0
        for tool in response.tool_calls:
            function_name = tool['function']['name']
            arguments = tool['function']['arguments']
            
            if function_name == 'save_plan':
                suggested_name = arguments.get('filename', f"plan{plan_number}.json")
                file_content = arguments.get('contents', '')
                plan_file_path = plan_dir / f"plan{plan_number}.json"
                plan_number += 1
                
                tools.save_plan(
                    plan_file_path.as_posix(), 
                    {
                        "file_name": suggested_name,
                        "contents": file_content
                    }
                )
                dump_content += f"# {suggested_name}\n{file_content}\n\n"
            else:
                self.log(3, f"Unknown tool function: {function_name}")
            
                
        (self.log_dir / "document_plan.md").write_text(dump_content, encoding="utf-8")
        self.log(2, "Document planning completed and saved.")
        
if __name__ == "__main__":
    logging.basicConfig(filename='.log', level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
    al = ProjectAnalyzer("")
    al.load()
    
    dp = DocumentPlanner(sys.argv[1], al.impression)
    dp.run()