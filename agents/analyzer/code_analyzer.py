import logging
from pathlib import Path
import sys
from agents.analyzer.file_node import FileInfo
from agents.base_agent import BaseAgent

LINE_READ = 100

class CodeAnalyzer(BaseAgent):
    parent_dir: Path
    impression: str

    def __init__(self, root_dir: str|Path):
        super().__init__("CodeAnalyzer")
        _root = Path(root_dir)
        self.parent_dir = _root.parent

    def find_dependencies(self, target: FileInfo)->str:
        res = self.chat(
            [
                {
                    "role": "user",
                    "content": self.impression
                },
                {
                    "role": "system",
                    "content": (self.prompt_dir/"find_dependencies.md").read_text()
                },
                {
                    "role": "user",
                    "content": f"Analyze \"{target.relative_to(self.parent_dir).as_posix()}\":\n" + target.read_text_line(LINE_READ)
                }
            ]
        )
        if not res.content:
            self.log(3, f"find_logics has no content: {target}")
            return ""
        return res.content

    def find_logics(self, target: FileInfo):
        file_path = target.relative_to(self.parent_dir).as_posix()
        src = target.read_text_line(LINE_READ)
        res = self.chat(
            [
                {
                    "role": "user",
                    "content": f"Project Impression:\n{self.impression}"
                },
                {
                    "role": "system",
                    "content": (self.prompt_dir/"find_logics.md").read_text()
                },
                {
                    "role": "user",
                    "content": f"Analyze \"{file_path}\":\n{src}"
                }
            ]
        )
        if not res.content:
            self.log(3, f"find_logics has no content: {target}")
            return ""
        return res.content

if __name__ == "__main__":
    logging.basicConfig(filename='.log', level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
    al = CodeAnalyzer(sys.argv[1])
    al.impression = """
    ### **Project Overview: PIC18 Player**

**Core Purpose:**
A hardware-software project for a **PICA18 microcontroller-based MIDI player with LED visualizations**, likely for embedded systems or educational purposes.

---

### **1. Repository Structure & Components**
- **Main Components:**
  - **`MidiPlayer`**: MIDI playback system for PIC18 MCUs (contains `.c`, `.h`, conversion scripts).
  - **`LEDScreen`**: LED display visualization system (Python scripts + C firmware, includes image processing).
  - **`assets`**: MIDI/MP4 files (e.g., *Undertale* tracks, *Rolling Girl*, custom MIDI files).

- **Core Files:**
  - **Firmware:** `main.py` (likely Python-based project setup), `main.c` (PIC18 MIDI playback logic).
  - **MIDI Handling:** `convertor.py` (MIDI conversion tool), `.mid` files (audio assets).
  - **LED Visualization:** `pic_extractor.py` (image processing), `main.c` (LED screen rendering), `.png`/`.jpg` frames.
  - **Documentation:** System diagrams, architecture notes, READMEs.

---

### **2. Key Observations**
- **Dual-Focus Architecture:**
  - **Hardware:** PIC18 microcontroller-based MIDI playback with LED visualizations.
  - **Software:** Python scripts for MIDI conversion/image processing, C firmware for real-time rendering.
- **Assets:** Includes MIDI files (8-bit, multi-track) and video assets (*Bad Apple*, *Undertale*).
- **Tools:** `.gitignore`, Python packaging (`pyproject.toml`), version control hints (`.python-version`).
- **Documentation:** Partial documentation (architecture, workflow charts, images).

---
### **3. Confirmed Workflow**
1. **MIDI Playback:** Convert MIDI files to PIC18-compatible format (via `convertor.py`).
2. **LED Rendering:** Extract frames from videos/images (`pic_extractor.py`) → render on LED matrix (via `main.c`).
3. **Integration:** Python scripts preprocess assets; C firmware handles real-time playback/visualization.

---
### **4. Likely Use Cases**
- **Educational Project:** Teaching embedded systems/MIDI/LED programming.
- **Retro/Artistic:** Playback of chiptune or pixel-art visuals (e.g., *Undertale*, *Bad Apple*).
- **Customizable:** Supports user-provided MIDI files and visuals.

---
**Next Steps (if expanding):**
- Clarify hardware specifications (LED matrix type, PIC18 model).
- Review `convertor.py`/`pic_extractor.py` for asset conversion logic.
- Check `README.md` for setup/usage instructions.
"""
    c = al.find_dependencies(FileInfo(sys.argv[2]))
    print(c)
    c = al.find_logics(FileInfo(sys.argv[2]))
    print(c)
