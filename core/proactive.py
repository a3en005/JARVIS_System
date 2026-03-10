import os
import time
import threading
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class StarkButler(FileSystemEventHandler):
    def __init__(self, manager):
        self.manager = manager
        self.path = os.path.join(os.path.expanduser('~'), 'Downloads')

    def on_created(self, event):
        """Intelligence Protocol: Scanning new data packets."""
        if not event.is_directory:
            file_name = os.path.basename(event.src_path)
            alert = f"Sir, a new intelligence packet has arrived: {file_name}. Shall I analyze its contents?"
            self.manager.gui.display_response(f"[PROACTIVE]: {alert}")
            self.manager.voice.speak(alert)

class IntegrityMonitor(threading.Thread):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.daemon = True # Closes when the main app closes

    def run(self):
        """Life Support Protocol: Proactive system and health checks."""
        while True:
            # Check every 30 minutes
            time.sleep(1800) 
            
            # 1. System Health Check
            mem = psutil.virtual_memory().percent
            if mem > 90:
                msg = "Sir, system memory is critical. Recommend a 'Clean Sweep' to preserve the 2GB VRAM core."
                self.manager.gui.display_response(f"[STATUS]: {msg}")
                self.manager.voice.speak(msg)
            
            # 2. Humane Wellness Check (Stark Protocol)
            hour = time.localtime().tm_hour
            if 9 <= hour <= 17: # During typical tutoring/work hours
                msg = "Sir, you've been working for quite some time. Might I suggest a brief hydration break?"
                self.manager.gui.display_response(f"[LIFE SUPPORT]: {msg}")
                self.manager.voice.speak(msg)

def start_proactive_monitoring(manager):
    # Start File Watcher
    handler = StarkButler(manager)
    obs = Observer()
    obs.schedule(handler, handler.path, recursive=False)
    obs.start()
    
    # Start System Integrity Monitor
    integrity_thread = IntegrityMonitor(manager)
    integrity_thread.start()
    
    return obs