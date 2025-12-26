"""
Image utility functions for Doc Generator
"""
import base64
import io
from pathlib import Path
from typing import Union, Optional, Tuple
from PIL import Image


def encode_image_base64(image_path: Union[str, Path]) -> str:
    """
    將圖片編碼為 base64 字串
    
    Args:
        image_path: 圖片路徑
        
    Returns:
        str: base64 編碼的字串
    """
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def decode_image_base64(
    base64_str: str,
    output_path: Optional[Union[str, Path]] = None
) -> bytes:
    """
    將 base64 字串解碼為圖片
    
    Args:
        base64_str: base64 編碼的字串
        output_path: 輸出路徑（可選），若提供則儲存到檔案
        
    Returns:
        bytes: 圖片二進位資料
    """
    image_data = base64.b64decode(base64_str)
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(image_data)
    
    return image_data


def resize_image(
    image_path: Union[str, Path],
    max_size: Tuple[int, int] = (1024, 1024),
    output_path: Optional[Union[str, Path]] = None
) -> Union[str, Path]:
    """
    調整圖片大小
    
    Args:
        image_path: 圖片路徑
        max_size: 最大尺寸 (width, height)
        output_path: 輸出路徑（可選），若無則覆蓋原檔
        
    Returns:
        Union[str, Path]: 輸出圖片路徑
    """
    
    image_path = Path(image_path)
    output_path = Path(output_path) if output_path else image_path
    
    with Image.open(image_path) as img:
        # 計算新尺寸，保持比例
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 確保輸出目錄存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 儲存
        img.save(output_path)
    
    return output_path


def get_image_size(image_path: Union[str, Path]) -> Tuple[int, int]:
    """
    取得圖片尺寸
    
    Args:
        image_path: 圖片路徑
        
    Returns:
        Tuple[int, int]: (width, height)
    """
    
    with Image.open(image_path) as img:
        return img.size


def image_to_base64_data_url(
    image_path: Union[str, Path],
    mime_type: Optional[str] = None
) -> str:
    """
    將圖片轉換為 data URL 格式
    
    Args:
        image_path: 圖片路徑
        mime_type: MIME 類型（可選，自動偵測）
        
    Returns:
        str: data URL 格式的字串
    """
    image_path = Path(image_path)
    
    # 自動偵測 MIME 類型
    if mime_type is None:
        ext = image_path.suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".svg": "image/svg+xml"
        }
        mime_type = mime_map.get(ext, "image/png")
    
    base64_str = encode_image_base64(image_path)
    return f"data:{mime_type};base64,{base64_str}"
