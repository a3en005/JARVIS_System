import os
import sys
import json
import requests
import time
import keyboard
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow
from core.voice import VoiceEngine
from core.automation import SystemController
from core.proactive import start_proactive_monitoring
from core.vision import VisionSystem

class ApplicationManager(QObject):
    request_shutdown = pyqtSignal()

    def __init__(self):
        super().__init__()
        # Local LLM endpoint (Ollama/Llama.cpp)
        self.api_url = "http://127.0.0.1:8888/generate"
        self.status_url = "http://127.0.0.1:8888/status"
        self.clear_url = "http://127.0.0.1:8888/clear_command"
        
        # Conversation memory for context
        self.conversation_history = []
        self.max_history = 10
        
        # 1. Initialize Configuration
        self.load_config()
        
        # 2. Initialize Core Systems
        self.voice = VoiceEngine()
        self.vision = VisionSystem(self)
        self.gui = MainWindow(manager=self)
        
        # 3. Connect HUD & Internal Signals
        self.gui.command_submitted.connect(self.handle_input)
        self.request_shutdown.connect(self.terminate_session)
        
        # 4. Bind Global Intercepts (Hotkeys)
        self.reload_hotkeys()
        
        # 5. Launch Background Services
        self.watcher = start_proactive_monitoring(self)
        
        # 6. Initialize Remote Polling (Checks every 3 seconds)
        self.remote_timer = QTimer()
        self.remote_timer.timeout.connect(self.check_remote_commands)
        self.remote_timer.start(3000) 
        
        self.greet_user()

    def check_remote_commands(self):
        """Pings the local engine to see if a phone/browser sent a command."""
        try:
            response = requests.get(self.status_url, timeout=1)
            if response.status_code == 200:
                data = response.json()
                command = data.get("pending_command")
                
                if command == "REMOTE_WAKE":
                    self.wake_jarvis()
                    self.voice.speak("Remote wake signal confirmed. System active.")
                    requests.post(self.clear_url) 

                elif command == "REMOTE_KILL":
                    requests.post(self.clear_url)
                    self.request_shutdown.emit()
        except Exception:
            pass 

    def load_config(self):
        """Loads user-defined keys or factory defaults."""
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    "wake_key": "ctrl+alt+space",
                    "stop_key": "ctrl+shift+s" 
                }
                with open("config.json", "w") as f:
                    json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Config System Error: {e}")
            self.config = {"wake_key": "ctrl+alt+space", "stop_key": "ctrl+shift+s"}

    def reload_hotkeys(self):
        """Binds global keyboard listeners safely."""
        try:
            keyboard.unhook_all()
            keyboard.add_hotkey(self.config["wake_key"], self.wake_jarvis)
            keyboard.add_hotkey(self.config["stop_key"], lambda: self.request_shutdown.emit())
        except Exception as e:
            print(f"Hotkey Binding Failure: {e}")

    def greet_user(self):
        """Initial system integrity report."""
        hour = time.localtime().tm_hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        msg = f"{greeting}, sir. Systems online. How may I assist you?"
        self.gui.display_response(msg)
        self.voice.speak(msg)

    def wake_jarvis(self):
        """Focuses the HUD via the force_wake method in MainWindow."""
        self.gui.force_wake()

    def open_settings(self):
        """Launches Preference HUD."""
        from gui.settings_window import SettingsWindow
        self.settings_ui = SettingsWindow(self)
        self.settings_ui.show()

    def terminate_session(self):
        """Emergency Shutdown: Visual Purge and Memory Wipe."""
        self.gui.trigger_purge_visual()
        self.voice.speak("System purge initiated. Sleep well, sir.")
        
        if hasattr(self, 'vision'):
            self.vision.cleanup_temp() 
            
        print("🛑 Protocols terminated. Workshop offline.")
        QApplication.processEvents()
        time.sleep(1.5)
        os._exit(0)

    def handle_input(self, text):
        """Stage-based request processing with conversation context."""
        text_upper = text.upper()

        # --- STAGE 0: CORE UI COMMANDS ---
        if any(cmd in text_upper for cmd in ["OPEN SETTINGS", "PREFERENCES"]):
            self.open_settings()
            return

        if any(cmd in text_upper for cmd in ["HELP", "SHOW INSTRUCTIONS"]):
            self.gui.force_wake()
            self.gui.toggle_help()
            self.voice.speak("Protocols active on the HUD.")
            return

        # --- STAGE 1: OPTICAL NERVE (OCR) ---
        if any(trigger in text_upper for trigger in ["READ SCREEN", "ANALYZE CHART", "LOOK AT THIS"]):
            self.gui.display_response("Scanning visual perimeter...")
            screen_intel = self.vision.read_screen()
            if screen_intel:
                text = f"VISIBLE SCREEN DATA: '{screen_intel}'. USER REQUEST: {text}"
            else:
                self.gui.display_response("[!] Optical sensors returned null data.")

        # --- STAGE 2: LOCAL AUTOMATION ---
        cmd_feedback = SystemController.execute(text)
        if cmd_feedback:
            self.gui.display_response(f"[DIRECT ACTION]: {cmd_feedback}")
            self.voice.speak(cmd_feedback)
            self.add_to_history("User", text)
            self.add_to_history("J.A.R.V.I.S.", cmd_feedback)
            return 

        # --- STAGE 3: NEURAL CORE (with conversation context) ---
        model_id = "llama3.2:1b"
        
        # Build conversation context
        context = self.get_conversation_context()
        
        system_instruction = (
            "You are J.A.R.V.I.S. from Marvel Universe. Be professional, witty, British, "
            "and highly capable. Keep responses conversational and brief. "
            "You have access to these commands:\n"
            "- To open apps: LAUNCH_APP: [appname]\n"
            "- To search web: SEARCH_FOR: [query]\n"
            "- To open links: OPEN_URL: [url]\n"
            f"\nConversation history:\n{context}"
        )

        try:
            self.gui.display_response("Consulting neural core...")
            
            # Include conversation history in prompt
            full_prompt = f"{system_instruction}\n\nUser: {text}\nJ.A.R.V.I.S.:"
            
            payload = {"prompt": full_prompt, "model": model_id}
            response = requests.post(self.api_url, json=payload, timeout=60)
            
            if response.status_code == 200:
                ai_reply = response.json().get("response", "")
                
                # Process any actions in the response
                action_feedback = SystemController.execute(ai_reply)
                
                # Display response in chat
                display_msg = f"{ai_reply}"
                if action_feedback:
                    display_msg += f"\n\n[ACTION]: {action_feedback}"
                
                self.gui.display_response(display_msg)
                
                # Extract clean text for voice (remove command tags)
                clean_voice = ai_reply.split("LAUNCH_APP:")[0].split("SEARCH_FOR:")[0].split("OPEN_URL:")[0].strip()
                self.voice.speak(clean_voice if clean_voice else "Action complete, sir.")
                
                # Add to conversation history
                self.add_to_history("User", text)
                self.add_to_history("J.A.R.V.I.S.", ai_reply)
            else:
                self.gui.display_response("❌ Neural core is unresponsive.")
        except Exception as e:
            self.gui.display_response(f"❌ Connection Error: {str(e)}")

    def add_to_history(self, role, message):
        """Add a message to conversation history"""
        self.conversation_history.append({"role": role, "message": message})
        # Keep only last max_history exchanges
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def get_conversation_context(self):
        """Build conversation context string from history"""
        if not self.conversation_history:
            return "No previous conversation."
        
        context_parts = []
        for msg in self.conversation_history:
            context_parts.append(f"{msg['role']}: {msg['message']}")
        return "\n".join(context_parts)

    def run(self):
        """Initializes and displays the HUD."""
        self.gui.show()
        time.sleep(0.1)
        self.gui.raise_()
        self.gui.activateWindow()

