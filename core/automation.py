import os
import pyautogui
import webbrowser
import subprocess
import psutil

class SystemController:
    @staticmethod
    def execute(ai_text):
        """Advanced Automated PC Control Protocol."""
        ai_text = ai_text.upper()
        feedback = ""

        # 1. INTERNET BROWSING PROTOCOL
        if "SEARCH_FOR" in ai_text:
            # Usage: "SEARCH_FOR: [query]"
            query = ai_text.split("SEARCH_FOR:")[1].strip()
            url = f"https://www.google.com/search?q={query}"
            webbrowser.open(url)
            return f"Searching the web for '{query}', sir."

        elif "OPEN_URL" in ai_text:
            url = ai_text.split("OPEN_URL:")[1].strip()
            webbrowser.open(url)
            return f"Opening {url} now."

        # 2. APPLICATION CONTROL PROTOCOL
        elif "LAUNCH_APP" in ai_text:
            # Usage: "LAUNCH_APP: [app_name]"
            app_name = ai_text.split("LAUNCH_APP:")[1].strip().lower()
            try:
                # Common app mappings
                apps = {
                    "chrome": "start chrome",
                    "notepad": "notepad.exe",
                    "calc": "calc.exe",
                    "code": "code" # VS Code
                }
                cmd = apps.get(app_name, f"start {app_name}")
                os.system(cmd)
                return f"Initializing {app_name}, sir."
            except Exception as e:
                return f"Unable to launch {app_name}. Error: {str(e)}"

        # 3. DIRECT UI MANIPULATION (The 'Hands' of Jarvis)
        elif "SCROLL_DOWN" in ai_text:
            pyautogui.scroll(-500)
            return "Scrolling down."

        elif "PRESS_KEY" in ai_text:
            key = ai_text.split("PRESS_KEY:")[1].strip().lower()
            pyautogui.press(key)
            return f"Simulating {key} press."

        # 4. STARK SECURITY (Nuke/Lock)
        elif "NUKE_IT" in ai_text or "LOCKDOWN" in ai_text:
            os.system("rundll32.exe user32.dll,LockWorkStation")
            return "System secured. Workshop locked."

        return None