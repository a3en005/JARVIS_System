import cv2
import numpy as np
import pyautogui
import os
import pytesseract
import time
from datetime import datetime

class VisionSystem:
    def __init__(self, manager):
        self.manager = manager
        self.temp_dir = "core/temp_vision"
        # Path to your Tesseract executable
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def capture_screen(self):
        """Takes a high-res screenshot and returns the file path."""
        screenshot = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        timestamp = datetime.now().strftime("%H%M%S")
        file_path = os.path.join(self.temp_dir, f"intel_{timestamp}.png")
        cv2.imwrite(file_path, frame)
        return file_path

    def read_screen(self):
        """Captures the screen and extracts text using OCR."""
        file_path = self.capture_screen()
        img = cv2.imread(file_path)
        
        # Pre-processing for better OCR accuracy
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Using adaptive thresholding to handle different UI themes (Light/Dark)
        processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY, 11, 2)
        
        # Page Segmentation Mode 3: Fully automatic page segmentation, but no OSD.
        custom_config = r'--oem 3 --psm 3'
        text_data = pytesseract.image_to_string(processed, config=custom_config)
        
        return text_data.strip()

    def cleanup_temp(self, max_age_seconds=300):
        """Removes temporary vision files older than 5 minutes."""
        current_time = time.time()
        for filename in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, filename)
            if os.path.isfile(file_path):
                if os.stat(file_path).st_mtime < (current_time - max_age_seconds):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Cleanup Error: {e}")