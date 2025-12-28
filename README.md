# docu-chan

2025 NCKU "THEORY OF COMPUTATION" final project. An AI-powered agent that automates documentation, README generation, and Mermaid flowcharts.

## Overview

Doc Generator is a multi-phase pipeline for automatically generating comprehensive documentation from code projects using LLM agents.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Doc Generator                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Phase 1: Multi-Modal Understanding                         │
│  ├── ResourceSplitter                                       │
│  ├── CodeReader [gemma3:4b]                                │
│  ├── ImageReader [gemma3:4b + Vision]                      │
│  └── ProjectAnalyzer [gpt-oss:120b]                        │
│                                                             │
│  Phase 2: Documentation Planning                            │
│  └── DocPlanner [gpt-oss:120b]                             │
│                                                             │
│  Phase 3: Visual-Enhanced Generation                        │
│  ├── Text Documentation                                     │
│  │   ├── TechWriter [gpt-oss:20b]                          │
│  │   └── DocReviewer [gpt-oss:20b]                         │
│  └── Chart Generation Loop                                  │
│      ├── DiagramDesigner [gpt-oss:20b]                     │
│      ├── MermaidCoder [gpt-oss:20b]                        │
│      ├── CodeExecutor (Render to PNG)                      │
│      └── VisualInspector [gemma3:4b + Vision]              │
│                                                             │
│  Phase 4: Packaging                                         │
│  └── Publisher [gemma3:4b]                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.12+
- Node.js 18+ (用於 Mermaid 圖表渲染)

### 1. Clone & Setup Python

```bash
# Clone the repository
git clone https://github.com/sunnyshoun/docu-chan.git
cd docu-chan

# 使用 uv (推薦)
pip install uv
uv sync

# 或使用 pip
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Install mermaid-cli

```bash
# 安裝 Node.js: https://nodejs.org/

# 安裝 mermaid-cli (Windows 需以管理員身份執行)
npm install -g @mermaid-js/mermaid-cli

# 驗證安裝
mmdc --version
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env to add your API_KEY
```

詳細安裝說明請參考 [docs/installation.md](docs/installation.md)

## Quick Start

### Chart Generation Demo

```bash
python main.py --chart "Create a login flowchart"
```

### Full Pipeline

```bash
python main.py ./your_project
```

## Project Structure

```
docu-chan/
├── main.py                 # Entry point
├── models.py               # Data models
├── config/                 # Configuration
│   └── settings.py
├── agents/                 # AI Agents (按任務分類)
│   ├── base.py             # Base agent class
│   ├── project_analyzer/   # Phase 1: 專案分析 (待實作)
│   ├── doc_planner/        # Phase 2: 文檔規劃 (待實作)
│   ├── doc_generator/      # Phase 3: 文檔生成
│   │   ├── chart/          # Mermaid 圖表生成
│   │   │   ├── loop.py     # ChartLoop 主控制器
│   │   │   ├── designer.py # TPA 分析與結構設計
│   │   │   ├── coder.py    # Mermaid 代碼生成
│   │   │   ├── executor.py # PNG 渲染 (mermaid-cli)
│   │   │   └── inspector.py# 視覺品質檢查
│   │   └── document/       # 技術文檔撰寫
│   │       └── writer.py
│   └── packer/             # Phase 4: 打包發布 (待實作)
├── prompts/                # JSON prompt templates (按任務分類)
│   ├── project_analyzer/
│   ├── doc_planner/
│   ├── doc_generator/
│   └── packer/
├── utils/                  # Utilities
│   ├── llm_client.py
│   ├── prompt_loader.py
│   ├── file_utils.py
│   └── image_utils.py
├── docs/                   # 說明文件
│   └── installation.md
└── outputs/                # Generated outputs
```

## Features

### ✅ Implemented

- **ProjectAnalyzer**: Reads and summarizes code files and images
- **DocPlanner**: Plans documentation structure
- **DocGenerator**: Writes technical documentation
- **ChartLoop**: Generates Mermaid diagrams with visual QA loop
- **Packer**: Packages final documentation

## Usage Example

```python
from config.settings import load_config
from agents import AgentContext, ChartLoop

# Initialize
config = load_config()
AgentContext.initialize(api_key=config.api_key, base_url=config.api_base_url)

# Create chart
loop = ChartLoop(output_dir="./outputs")
result = loop.run("Create a login flowchart with validation")

if result.success:
    print(f"Chart saved to: {result.image_path}")
```

## Configuration

Environment variables (`.env`):

```
API_KEY=your_api_key_here
API_BASE_URL=https://api-gateway.netdb.csie.ncku.edu.tw
```

## License

GPL License
