"""Code Executor - 使用 mermaid-cli (mmdc) 本地渲染 Mermaid 代碼"""
import base64
import subprocess
import tempfile
import uuid
import shutil
from typing import Optional
from pathlib import Path
from dataclasses import dataclass

from utils.file_utils import ensure_dir


@dataclass
class RenderResult:
    """渲染結果"""
    success: bool
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    error: Optional[str] = None


class CodeExecutor:
    """Mermaid 代碼執行器 (需要: npm install -g @mermaid-js/mermaid-cli)"""
    
    DEFAULT_TIMEOUT = 60
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT
    ):
        self.output_dir = Path(output_dir) if output_dir else Path(tempfile.gettempdir()) / "mermaid_charts"
        self.timeout = timeout
        self._mmdc_path: Optional[str] = None
        ensure_dir(self.output_dir)
    
    def _find_mmdc(self) -> str:
        """尋找 mmdc 執行檔"""
        if self._mmdc_path:
            return self._mmdc_path
        
        # 嘗試直接呼叫
        mmdc = shutil.which("mmdc")
        if mmdc:
            self._mmdc_path = mmdc
            return mmdc
        
        # Windows: 嘗試 npx
        mmdc = shutil.which("mmdc.cmd")
        if mmdc:
            self._mmdc_path = mmdc
            return mmdc
        
        raise FileNotFoundError(
            "mmdc not found. Please install: npm install -g @mermaid-js/mermaid-cli"
        )
    
    def render(
        self,
        mermaid_code: str,
        output_name: Optional[str] = None,
        format: str = "png"
    ) -> RenderResult:
        """渲染 Mermaid 代碼為圖片"""
        if output_name is None:
            output_name = f"chart_{uuid.uuid4().hex[:8]}"
        
        output_path = self.output_dir / f"{output_name}.{format}"
        ensure_dir(output_path.parent)
        
        # 建立暫存 .mmd 檔案
        temp_mmd = self.output_dir / f"_temp_{uuid.uuid4().hex[:8]}.mmd"
        
        try:
            # 寫入 Mermaid 代碼
            with open(temp_mmd, "w", encoding="utf-8") as f:
                f.write('%%{init: {"flowchart": {"defaultRenderer": "elk"}} }%%\n')
                f.write(mermaid_code)
            
            # 呼叫 mmdc
            mmdc = self._find_mmdc()
            cmd = [
                mmdc,
                "-i", str(temp_mmd),
                "-o", str(output_path),
                "-b", "transparent",
                "-s", "4"  # 放大 4 倍提高解析度
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                return RenderResult(success=False, error=f"mmdc failed: {error_msg}")
            
            if not output_path.exists():
                return RenderResult(success=False, error="Output file not created")
            
            # 讀取並編碼為 base64
            with open(output_path, "rb") as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            
            return RenderResult(
                success=True,
                image_path=str(output_path),
                image_base64=image_base64
            )
            
        except FileNotFoundError as e:
            return RenderResult(success=False, error=str(e))
        except subprocess.TimeoutExpired:
            return RenderResult(success=False, error=f"Render timeout ({self.timeout}s)")
        except Exception as e:
            return RenderResult(success=False, error=str(e))
        # finally:
        #     # 清理暫存檔
        #     if temp_mmd.exists():
        #         temp_mmd.unlink()
    
    def render_svg(self, mermaid_code: str, output_name: Optional[str] = None) -> RenderResult:
        """渲染為 SVG 格式"""
        return self.render(mermaid_code, output_name, format="svg")
    
    def render_png(self, mermaid_code: str, output_name: Optional[str] = None) -> RenderResult:
        """渲染為 PNG 格式"""
        return self.render(mermaid_code, output_name, format="png")
    
    @staticmethod
    def check_installation() -> bool:
        """檢查 mermaid-cli 是否已安裝"""
        return shutil.which("mmdc") is not None or shutil.which("mmdc.cmd") is not None
