# 安裝指南

本文件說明 Docu-chan 的安裝步驟與依賴項目。

## 系統需求

- Python 3.12+
- Node.js 18+ (用於 Mermaid 圖表渲染)
- Git

---

## 1. Python 環境

### 使用 uv (推薦)

```bash
# 安裝 uv
pip install uv

# 建立虛擬環境並安裝依賴
uv sync
```

### 使用 pip

```bash
# 建立虛擬環境
python -m venv .venv

# 啟動虛擬環境
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

---

## 2. Node.js 與 mermaid-cli

Docu-chan 使用 [mermaid-cli](https://github.com/mermaid-js/mermaid-cli) 將 Mermaid 代碼渲染為 PNG/SVG 圖片。

### 2.1 安裝 Node.js

#### Windows

1. 下載安裝程式：https://nodejs.org/
2. 執行安裝程式，使用預設選項
3. 驗證安裝：
   ```powershell
   node --version
   npm --version
   ```

#### macOS

```bash
# 使用 Homebrew
brew install node

# 驗證
node --version
npm --version
```

#### Linux (Ubuntu/Debian)

```bash
# 使用 NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 驗證
node --version
npm --version
```

### 2.2 安裝 mermaid-cli

```bash
# 全域安裝
npm install -g @mermaid-js/mermaid-cli

# 驗證安裝
mmdc --version
```

#### 常見問題

**權限錯誤 (EACCES)**

Windows (以管理員身份執行 PowerShell):
```powershell
npm install -g @mermaid-js/mermaid-cli
```

Linux/macOS:
```bash
sudo npm install -g @mermaid-js/mermaid-cli
# 或修改 npm 全域目錄權限
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
npm install -g @mermaid-js/mermaid-cli
```

**找不到 mmdc 命令**

確認 npm 全域 bin 目錄在 PATH 中：
```bash
# 查看 npm 全域 bin 路徑
npm config get prefix

# Windows: 通常是 C:\Users\<用戶名>\AppData\Roaming\npm
# Linux/macOS: 通常是 /usr/local/bin 或 ~/.npm-global/bin
```

---

## 3. 環境變數設定

複製 `.env.example` 並重新命名為 `.env`：

```bash
cp .env.example .env
```

編輯 `.env` 設定 API 金鑰：

```env
API_KEY=your_api_key_here
API_BASE_URL=https://your-llm-api-endpoint.com/v1
```

---

## 4. 驗證安裝

執行以下命令確認所有依賴已正確安裝：

```bash
# 檢查 Python
python --version

# 檢查 mmdc
mmdc --version

# 執行程式
python main.py --help
```

---

## 快速開始

```bash
# 生成圖表
python main.py --chart "User login authentication flow"

# 指定輸出目錄
python main.py --chart "System architecture" -o ./my_diagrams

# 跳過視覺檢查（加快速度）
python main.py --chart "Database ER diagram" --skip-inspection
```
