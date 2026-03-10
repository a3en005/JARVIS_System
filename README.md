# J.A.R.V.I.S. - Stark Industries Neural Interface

<p align="center">
  <img src="gui/assets/jarvis_glow.gif" alt="J.A.R.V.I.S. Arc Reactor" width="200"/>
</p>

<p align="center">
  <i>"Good evening, sir. Systems online. How may I assist you?"</i>
</p>

---

## Overview

J.A.R.V.I.S. (Just A Rather Very Intelligent System) is a desktop AI assistant inspired by Tony Stark's Jarvis from the Marvel Universe. It features a modern dark-mode GUI, voice synthesis, screen OCR, system automation, and local LLM integration using Ollama.

## Features

### 🎙️ Voice Synthesis
- Natural text-to-speech using pyttsx3
- British, witty personality
- Non-blocking audio for responsive UI

### 👁️ Vision System
- Screen capture functionality
- OCR using Tesseract for reading screen content
- Automatic cleanup of temporary vision files

### ⚡ System Automation
- Launch applications
- Web search and URL opening
- Keyboard simulation
- System lock capability

### 🧠 Neural Core
- Local LLM integration via Ollama
- Uses llama3.2:1b model by default
- Conversation history for context

### 📡 Remote Interface
- Web-based remote control accessible from phone/browser
- Remote wake and shutdown commands

### 🔔 Proactive Monitoring
- File watcher for Downloads folder
- System memory monitoring
- Wellness reminders

## Requirements

### System Requirements
- **OS**: Windows 10/11
- **Python**: 3.9+
- **RAM**: 4GB minimum (8GB recommended)
- **VRAM**: 2GB+ for local LLM (optional)

### External Dependencies
1. **Ollama** - For local LLM inference
   - Download from: https://ollama.com
   - Required model: `ollama pull llama3.2:1b`

2. **Tesseract OCR** - For screen reading
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/JARVIS_System.git
cd JARVIS_System
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Ollama
- Download from https://ollama.com
- Run: `ollama pull llama3.2:1b`

### 5. Run J.A.R.V.I.S.
```bash
python main.py
```

Or use the batch file:
```bash
run_jarvis.bat
```

## Configuration

### Hotkeys
- **Wake Key**: `Ctrl+Alt+Space` - Bring J.A.R.V.I.S. to focus
- **Stop Key**: `Ctrl+Shift+S` - Shutdown J.A.R.V.I.S.

Edit `config.json` to customize:
```json
{
    "wake_key": "ctrl+alt+space",
    "stop_key": "ctrl+shift+s",
    "theme": "dark"
}
```

### Remote Access
J.A.R.V.I.S. runs a web interface on port 8888:
- Access from same PC: http://127.0.0.1:8888
- Access from phone/other device: http://YOUR_PC_IP:8888

## Project Structure

```
JARVIS_System/
├── core/                   # Core systems
│   ├── __init__.py
│   ├── voice.py           # Text-to-speech engine
│   ├── vision.py          # Screen capture & OCR
│   ├── automation.py      # System control
│   └── proactive.py       # Background monitoring
├── gui/                   # GUI components
│   ├── __init__.py
│   ├── main_window.py     # Main chat interface
│   ├── settings_window.py # Settings dialog
│   └── assets/            # Images and icons
│       ├── jarvis_glow.gif
│       └── jarvis.ico
├── ollama/                # Ollama client (bundled)
├── main.py               # Entry point
├── jarvis.py             # Main application logic
├── local_engine.py       # FastAPI server for Ollama
├── config.json           # User configuration
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## Usage

### Commands
- **"Open Settings"** - Open preferences
- **"Help"** - Show available commands
- **"Read Screen"** / **"Analyze Chart"** - OCR screen content
- **"Launch [app]"** - Open an application (notepad, chrome, calc, code)
- **"Search for [query]"** - Web search
- **"Open URL [url]"** - Open a website

### Conversation
Just chat naturally with J.A.R.V.I.S. - it uses the local LLM for responses.

## Troubleshooting

### Ollama Connection Error
- Ensure Ollama is running: `ollama serve`
- Pull the model: `ollama pull llama3.2:1b`

### Tesseract Not Found
- Install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki
- Update path in `core/vision.py` if not using default

### Port 8888 in Use
- Stop any other application using port 8888
- Or modify `local_engine.py` to use a different port

### Missing Dependencies
```bash
pip install -r requirements.txt
```

## License

This project is for educational and personal use. Not affiliated with Marvel or Stark Industries.

---

<p align="center">
  <b>Sir, I've completed all system checks. Ready for your commands.</b>
</p>

