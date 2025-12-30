from pathlib import Path
import sys
import asyncio
from agents.base import BaseAgent
from agents.prompts import load_prompt
from config.agents import AgentName


class ImageWorker(BaseAgent):
    """
    圖片分析 Worker - 使用 VLM 分析圖片內容
    
    使用時機：
    - Phase 1 的 CoAProjectAnalyzer 掃描到圖片檔案時
    - 圖片副檔名：.png, .jpg, .jpeg, .gif, .svg, .webp, .bmp, .ico
    
    功能：
    - 分析圖片內容（UI截圖、架構圖、流程圖等）
    - 判斷圖片是否對專案理解重要
    - 輸出結構化描述供 Manager 整合
    """
    base: Path
    system_prompt: str
    user_template: str
    
    def __init__(self, base: str | Path):
        super().__init__(
            agent_name=AgentName.IMAGE_WORKER,
            display_name="ImageWorker"
        )
        self.base = Path(base)
        
        # 載入 prompt
        prompt_data = load_prompt("project_analyzer/image_reader")
        self.system_prompt = prompt_data["system_prompt"]
        self.user_template = prompt_data["user_prompt_template"]

    async def get_image_description(self, image_path: str, **kwargs) -> str:
        """
        使用視覺模型分析圖片並生成詳細描述（非同步）
        
        Args:
            image_path: 圖片路徑（相對或絕對）
            
        Returns:
            str: 圖片描述（JSON 格式或錯誤訊息）
        """
        import time
        abs_path = Path(image_path)
        if not abs_path.is_absolute():
            abs_path = Path(self.base).joinpath(image_path)

        # 確認檔案存在
        if not abs_path.exists():
            self.logger.warning(f"[ImageWorker] 找不到圖片: {image_path}")
            return "error: no such file"
        
        # 使用絕對路徑字串傳遞給 Ollama（根據 SDK 文檔）
        abs_path_str = str(abs_path.resolve())
        self.logger.debug(f"[ImageWorker] 圖片路徑: {abs_path_str}")
        
        try:
            self.logger.debug(f"[ImageWorker] 發送 VLM 請求: {image_path}")
            start_time = time.time()
            
            response = await self.chat_raw_async(
                [
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        'role': 'user',
                        'content': self.user_template.format(image_path=image_path),
                        'images': [abs_path_str]
                    }
                ],
                keep_history=False,
                options={'temperature': 0.3,'num_ctx': 2048}
            )
            
            elapsed = time.time() - start_time
            self.logger.debug(f"[ImageWorker] VLM 回應: {image_path} ({elapsed:.2f}s)")
        except Exception as e:
            self.logger.error(f"[ImageWorker] VLM 錯誤: {image_path} - {e}")
            return str(e)
        
        return response.message.content
    
if __name__ == "__main__":
    worker = ImageWorker(".", "prompts/project_analyzer/image_reader.json")
    print("load", sys.argv[1])
    print(asyncio.run(worker.get_image_description(sys.argv[1])))
    print("done")