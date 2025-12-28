from pathlib import Path
import sys
from agents.base import BaseAgent
from config import config

class PictureAnalyzer(BaseAgent):
    prompt: str
    base: Path
    def __init__(self, base: str | Path, prompt_file: str | Path):
        super().__init__("PictureAnalyzer", config.models.image_reader)
        self.prompt = Path(prompt_file).read_text()
        self.base = Path(base)

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
                        "content": self.prompt
                    },
                    {
                        'role': 'user',
                        'content': f"This is a picture at \"{image_path}\", analyze this image and generate a structured technical analysis report.",
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