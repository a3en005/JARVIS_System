import logging
logging.basicConfig(filename='debug.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logging.debug('Application started')

import subprocess
import time
import sys
import os
import psutil
import winshell
from win32com.client import Dispatch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from jarvis import ApplicationManager

def check_stark_shortcut():
    """Ensures the J.A.R.V.I.S. shortcut exists on the desktop for quick access."""
    try:
        desktop = winshell.desktop()
        path = os.path.join(desktop, "J.A.R.V.I.S..lnk")
        
        if not os.path.exists(path):
            print("🛠️ Shortcut missing. Rebuilding Stark Interface link...")
            target_dir = os.path.dirname(os.path.abspath(__file__))
            target_script = os.path.join(target_dir, "main.py")
            # Use pythonw.exe to prevent a console window from popping up behind the HUD
            python_exe = sys.executable.replace("python.exe", "pythonw.exe")
            icon_path = os.path.join(target_dir, "gui", "assets", "jarvis.ico")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortcut(path)
            shortcut.TargetPath = python_exe
            shortcut.Arguments = f'"{target_script}"'
            shortcut.WorkingDirectory = target_dir
            shortcut.Description = "Stark Industries Neural Interface"
            if os.path.exists(icon_path):
                shortcut.IconLocation = icon_path
            shortcut.save()
            print("✅ Shortcut restored to desktop.")
    except Exception as e:
        print(f"⚠️ Shortcut check skipped: {e}")

def main():
    # --- STAGE 0: CRITICAL ATTRIBUTES ---
    # This MUST happen before QApplication is instantiated to fix the OpenGL error
    QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL)
    
    print("\n--- INITIALIZING J.A.R.V.I.S. ---")
    
    # 1. Integrated Shortcut Check
    check_stark_shortcut()

    # 2. Start the Local API Engine (Llama 1B / Ollama Bridge)
    try:
        engine_proc = subprocess.Popen(
            [sys.executable, "local_engine.py"], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        print("⚡ J.A.R.V.I.S. Neural Engine warming up...")
    except Exception as e:
        print(f"❌ Failed to start Engine: {e}")
        sys.exit(1)

    # 3. Performance Optimization: Priority Elevation
    try:
        p = psutil.Process(os.getpid())
        if sys.platform == 'win32':
            p.priority_class = psutil.HIGH_PRIORITY_CLASS
            print("💎 Process priority set to HIGH (Optimization for 2GB VRAM).")
    except Exception:
        pass

    # 4. Initialize the PyQt5 App
    app = QApplication(sys.argv)
    app.setApplicationName("J.A.R.V.I.S. Assistant")

    # 5. Neural Sync Wait
    # Giving the local_engine 5 seconds to load the model into VRAM
    time.sleep(5) 
    
    try:
        manager = ApplicationManager()
        # 6. Launch the HUD
        manager.run()
    except Exception as e:
        print(f"❌ Application Manager failed to initialize: {e}")
        engine_proc.terminate()
        sys.exit(1)

    # 7. Execute App and handle Safe Shutdown
    exit_code = app.exec_()
    
    print("\n🛑 Shutting down protocols...")
    engine_proc.terminate()
    try:
        engine_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        engine_proc.kill()
        
    print("Workshop offline. Sleep well, sir.")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()