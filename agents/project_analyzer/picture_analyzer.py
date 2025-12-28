from pathlib import Path
import sys
from agents.base import BaseAgent
from agents.prompts import load_prompt
from config import config

class PictureAnalyzer(BaseAgent):
    base: Path
    system_prompt: str
    user_template: str
    
    def __init__(self, base: str | Path, prompt_file: str | Path | None = None):
        super().__init__("PictureAnalyzer", config.models.image_reader)
        self.base = Path(base)
        
        # 載入 prompt（支援 JSON 或舊的 .md 格式）
        if prompt_file and Path(prompt_file).suffix == ".json":
            prompt_data = load_prompt("project_analyzer/image_reader")
            self.system_prompt = prompt_data["system_prompt"]
            self.user_template = prompt_data["user_prompt_template"]
        elif prompt_file and Path(prompt_file).exists():
            # 相容舊的 .md 格式
            self.system_prompt = Path(prompt_file).read_text()
            self.user_template = "Analyze this image at \"{image_path}\""
        else:
            # 預設使用 JSON prompt
            prompt_data = load_prompt("project_analyzer/image_reader")
            self.system_prompt = prompt_data["system_prompt"]
            self.user_template = prompt_data["user_prompt_template"]

    def get_image_description(self, image_path: str, **kwargs) -> str:
        """
        使用視覺模型分析圖片並生成詳細描述
        """
        abs_path = Path(image_path)
        if not abs_path.is_absolute():
            abs_path = Path(self.base).joinpath(image_path)

        try:
            img_data = Path(abs_path).read_bytes()
        except FileNotFoundError as e:
            return "error: no such file"
        
        try:
            response = self.chat_raw(
                [
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        'role': 'user',
                        'content': self.user_template.format(image_path=image_path),
                        'images': [img_data]
                    }
                ],
                keep_history=False
            )
        except Exception as e:
            return str(e)
        
        return response['message']['content']
    
if __name__ == "__main__":
    pa = PictureAnalyzer(".", "prompts/project_analyzer/picture.md")
    print("load", sys.argv[1])
    print(pa.get_image_description(sys.argv[1]))
    print("done")