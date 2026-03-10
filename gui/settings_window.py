from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
import json
import os


class SettingsWindow(QWidget):
    """JARVIS Settings Configuration Window"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, manager=None):
        super().__init__()
        self.manager = manager
        
        # Window Configuration
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 350)
        
        # Center on screen
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        self.move((screen.width() - self.width()) // 2, 
                  (screen.height() - self.height()) // 2)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Create the settings UI"""
        # Main container with dark background
        self.container = QWidget()
        self.container.setStyleSheet("""
            background-color: rgba(20, 20, 25, 240);
            border: 1px solid #4A90D9;
            border-radius: 12px;
        """)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title
        title = QLabel("⚙️ SYSTEM PREFERENCES")
        title.setStyleSheet("""
            color: #4A90D9;
            font-size: 16px;
            font-weight: bold;
            font-family: 'Segoe UI', sans-serif;
            padding: 5px;
        """)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Separator
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #444444;")
        main_layout.addWidget(separator)
        
        # Wake Key Setting
        wake_layout = QHBoxLayout()
        wake_label = QLabel("Wake Key:")
        wake_label.setStyleSheet("color: #cccccc; font-family: 'Segoe UI', sans-serif;")
        self.wake_input = QLineEdit()
        self.wake_input.setPlaceholderText("e.g., ctrl+alt+space")
        self.wake_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1e;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit:focus {
                border: 1px solid #4A90D9;
            }
        """)
        wake_layout.addWidget(wake_label)
        wake_layout.addWidget(self.wake_input)
        main_layout.addWidget(wake_layout)
        
        # Stop Key Setting
        stop_layout = QHBoxLayout()
        stop_label = QLabel("Stop Key:")
        stop_label.setStyleSheet("color: #cccccc; font-family: 'Segoe UI', sans-serif;")
        self.stop_input = QLineEdit()
        self.stop_input.setPlaceholderText("e.g., ctrl+shift+s")
        self.stop_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1e;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit:focus {
                border: 1px solid #4A90D9;
            }
        """)
        stop_layout.addWidget(stop_label)
        stop_layout.addWidget(self.stop_input)
        main_layout.addWidget(stop_layout)
        
        # Instructions
        instructions = QLabel("Use '+' for combinations:\nctrl+alt+space, alt+shift+h")
        instructions.setStyleSheet("""
            color: #888888;
            font-size: 10px;
            font-family: 'Consolas', monospace;
        """)
        instructions.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(instructions)
        
        # Spacer
        main_layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Save Button
        self.save_btn = QPushButton("SAVE")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(74, 144, 217, 30);
                color: #4A90D9;
                border: 1px solid #4A90D9;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(74, 144, 217, 60);
            }
        """)
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        # Close Button
        self.close_btn = QPushButton("CLOSE")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(200, 60, 60, 30);
                color: #cc6666;
                border: 1px solid #cc6666;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(200, 60, 60, 60);
            }
        """)
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(button_layout)
        
        # Set up container
        container_layout = QVBoxLayout()
        container_layout.addWidget(self.container)
        self.container.setLayout(main_layout)
        self.setLayout(container_layout)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(74, 144, 217, 60))
        shadow.setOffset(0, 0)
        self.container.setGraphicsEffect(shadow)
    
    def load_settings(self):
        """Load current settings from config.json"""
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    config = json.load(f)
                    self.wake_input.setText(config.get("wake_key", "ctrl+alt+space"))
                    self.stop_input.setText(config.get("stop_key", "ctrl+shift+s"))
            else:
                self.wake_input.setText("ctrl+alt+space")
                self.stop_input.setText("ctrl+shift+s")
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to config.json and reload hotkeys"""
        try:
            wake_key = self.wake_input.text().strip()
            stop_key = self.stop_input.text().strip()
            
            if not wake_key or not stop_key:
                self.show_message("⚠️ Please fill in both keys!")
                return
            
            # Load existing config to preserve other fields like 'theme'
            config = {}
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    config = json.load(f)
            
            # Update only the hotkeys
            config["wake_key"] = wake_key
            config["stop_key"] = stop_key
            
            # Ensure theme is set to dark if it wasn't there
            if "theme" not in config:
                config["theme"] = "dark"
            
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)
            
            # Reload hotkeys in the manager
            if self.manager and hasattr(self.manager, 'reload_hotkeys'):
                self.manager.reload_hotkeys()
            
            self.show_message("✅ Settings saved! Hotkeys reloaded.")
            self.settings_changed.emit()
            
        except Exception as e:
            self.show_message(f"❌ Error saving: {e}")
    
    def show_message(self, message):
        """Show a temporary message (could be enhanced with a label)"""
        print(f"[Settings] {message}")
    
    def mousePressEvent(self, event):
        """Enable window dragging"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle window dragging"""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

