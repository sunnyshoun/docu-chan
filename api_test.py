"""簡單的 Ollama API 測試腳本"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("API_BASE_URL", "http://localhost:11434")
API_KEY = os.getenv("API_KEY", "")

def test_connection():
    """測試 API 連線"""
    url = f"{API_BASE}/api/tags"
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    
    try:
        resp = requests.get(url, headers=headers, timeout=120)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        print(f"✅ 連線成功！可用模型數量: {len(models)}")
        for m in models[:5]:
            print(f"   - {m.get('name', 'unknown')}")
        if len(models) > 5:
            print(f"   ... 還有 {len(models) - 5} 個模型")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ 無法連線到 {API_BASE}")
        return False
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False

def test_generate(model: str = "gemma3:4b"):
    """測試生成功能"""
    url = f"{API_BASE}/api/generate"
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    payload = {
        "model": model,
        "prompt": "Say 'Hello, API test successful!' in one line.",
        "stream": False
    }
    
    try:
        print(f"\n📤 測試生成 (model: {model})...")
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        result = resp.json().get("response", "")
        print(f"📥 回應: {result[:200]}")
        return True
    except Exception as e:
        print(f"❌ 生成失敗: {e}")
        return False

if __name__ == "__main__":
    print(f"🔗 API Base: {API_BASE}\n")
    if test_connection():
        test_generate()
