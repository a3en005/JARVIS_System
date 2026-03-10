import pyttsx3
import threading

class VoiceEngine:
    def __init__(self):
        self.engine = pyttsx3.init('sapi5')
        self.engine.setProperty('rate', 185)    # Speed: 185 is perfect for "Natural but Fast"
        self.engine.setProperty('volume', 1.0)  # Full volume
        
        # Select the voice (0 = Male/David, 1 = Female/Zira)
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[0].id) 

    def speak(self, text):
        """Runs speech in a separate thread so the UI doesn't freeze."""
        def run():
            self.engine.say(text)
            self.engine.runAndWait()
        
        thread = threading.Thread(target=run)
        thread.start()