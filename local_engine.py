import os
import gc
import logging
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import ollama

# Set up logging with proper handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('neural_engine.log', mode='a')
    ]
)
logger = logging.getLogger("NeuralEngine")
app = FastAPI()

# Shared state (can be expanded for remote control)
class SystemStatus:
    hud_visible = True
    pending_command = None
    ollama_connected = False

status = SystemStatus()

class ChatRequest(BaseModel):
    prompt: str
    model: str = "llama3.2:1b"

class CommandRequest(BaseModel):
    command: str

def check_ollama_connection():
    """Check if Ollama is running and accessible using multiple methods."""
    try:
        # Primary method: Use ollama.list() which is more reliable
        # This will throw an error if Ollama is not running
        ollama.list()
        status.ollama_connected = True
        logger.info("Ollama connection verified successfully")
        return True
    except Exception as e:
        logger.warning(f"Ollama not accessible: {e}")
        status.ollama_connected = False
        return False

def clear_vram():
    """Aggressively flushes GPU memory to prevent OOM errors on 2GB cards."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

# --- REMOTE INTERFACE HTML ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>J.A.R.V.I.S. Neural Link</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #050a0f; color: #00ffff; font-family: 'Segoe UI', sans-serif; display: flex; flex-direction: column; height: 100vh; margin: 0; overflow: hidden; }
        #header { padding: 15px; border-bottom: 1px solid #00ffff33; text-align: center; font-weight: bold; letter-spacing: 3px; background: rgba(0, 255, 255, 0.05); }
        #terminal { flex: 1; overflow-y: auto; padding: 20px; font-family: 'Consolas', monospace; scroll-behavior: smooth; }
        #controls { padding: 10px; display: flex; gap: 10px; justify-content: center; border-top: 1px solid #00ffff22; }
        .btn { background: rgba(0, 255, 255, 0.1); border: 1px solid #00ffff; color: #00ffff; padding: 5px 15px; cursor: pointer; border-radius: 4px; font-size: 12px; }
        .btn:hover { background: #00ffff; color: #000; }
        #input-area { padding: 20px; background: #0a0f14; border-top: 1px solid #00ffff33; }
        input { width: 100%; background: transparent; border: 1px solid #00ffff66; color: white; padding: 12px; border-radius: 8px; outline: none; box-sizing: border-box; }
        input:focus { border-color: #00ffff; box-shadow: 0 0 10px #00ffff44; }
        .bot { color: #00ffff; margin-bottom: 15px; border-left: 2px solid #00ffff; padding-left: 10px; }
        .user { color: #8899aa; margin-bottom: 15px; font-style: italic; }
    </style>
</head>
<body>
    <div id="header">STARK INDUSTRIES REMOTE INTERFACE</div>
    <div id="terminal">
        <div class="bot">J.A.R.V.I.S: Neural link established. Waiting for input, sir.</div>
    </div>
    <div id="controls">
        <button class="btn" onclick="sendCommand('REMOTE_WAKE')">WAKE HUD</button>
        <button class="btn" onclick="sendCommand('REMOTE_KILL')" style="border-color: #ff4444; color: #ff4444;">PURGE SYSTEM</button>
    </div>
    <div id="input-area">
        <input type="text" id="userInput" placeholder="Enter command..." autocomplete="off">
    </div>

    <script>
        const input = document.getElementById('userInput');
        const term = document.getElementById('terminal');

        input.addEventListener('keypress', async (e) => {
            if(e.key === 'Enter' && input.value.trim()) {
                const val = input.value;
                append('user', 'YOU: ' + val);
                input.value = '';
                
                try {
                    const resp = await fetch('/generate', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({prompt: val})
                    });
                    const data = await resp.json();
                    append('bot', 'J.A.R.V.I.S: ' + data.response);
                } catch (err) {
                    append('bot', 'ERROR: Uplink lost.');
                }
            }
        });

        async function sendCommand(cmd) {
            append('user', 'Executing: ' + cmd);
            await fetch('/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt: cmd})
            });
            append('bot', 'J.A.R.V.I.S: Command relayed to core.');
        }

        function append(type, text) {
            const div = document.createElement('div');
            div.className = type;
            div.innerText = text;
            term.appendChild(div);
            term.scrollTop = term.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def remote_interface():
    return HTML_TEMPLATE

@app.get("/health")
async def health():
    """Health check endpoint - also verifies Ollama connection."""
    ollama_status = "connected" if check_ollama_connection() else "disconnected"
    return {
        "status": "online", 
        "integrity": "nominal",
        "ollama": ollama_status
    }

@app.get("/status")
async def get_status():
    """Status endpoint for JARVIS to poll for remote commands."""
    return {
        "status": "online",
        "pending_command": status.pending_command
    }

@app.post("/clear_command")
async def clear_command():
    """Clear the pending command after it's been processed by JARVIS."""
    status.pending_command = None
    return {"status": "cleared"}

@app.post("/generate")
async def generate(request: ChatRequest):
    try:
        clear_vram()
        
        # Handle Remote Control Hooks from the Web UI
        if request.prompt == "REMOTE_WAKE":
            # Set pending command for JARVIS to poll
            status.pending_command = "REMOTE_WAKE"
            return {"response": "Waking up the workstation HUD, sir."}
        
        if request.prompt == "REMOTE_KILL":
            # Set pending command for JARVIS to poll
            status.pending_command = "REMOTE_KILL"
            return {"response": "System purge initiated. Workshop going offline."}

        # Check Ollama connection first
        if not check_ollama_connection():
            return {
                "response": "I apologize, sir. The neural core (Ollama) is not responding. Please ensure Ollama is running on your system.",
                "error": "ollama_not_running"
            }

        # Build options - remove num_gpu if it causes issues
        options = {
            "num_predict": 100,
            "temperature": 0.7
        }
        
        # Only add num_gpu if CUDA is available
        if torch.cuda.is_available():
            options["num_gpu"] = 1

        response = ollama.chat(
            model=request.model, 
            messages=[
                {
                    'role': 'system', 
                    'content': 'You are J.A.R.V.I.S. Tone: Witty, British, Sophisticated. Keep responses brief.'
                },
                {'role': 'user', 'content': request.prompt}
            ],
            options=options
        )
        
        return {"response": response['message']['content']}
    
    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Inference Error: {str(e)}")
        
        # Provide more helpful error messages
        if "connection" in error_msg or "refused" in error_msg:
            detail = "Neural core unreachable. Is Ollama running?"
        elif "model" in error_msg:
            detail = f"Model '{request.model}' not found. Please pull it first: ollama pull {request.model}"
        else:
            detail = f"Neural processing error: {str(e)}"
        
        raise HTTPException(status_code=500, detail=detail)

if __name__ == "__main__":
    # Changed host to 0.0.0.0 to allow access from other devices on your WiFi
    print("💎 J.A.R.V.I.S. Neural Hub starting on port 8888...")
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="error")