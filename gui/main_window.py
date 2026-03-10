from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, 
                             QLabel, QMenu, QGraphicsDropShadowEffect, QApplication, QScrollArea, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QTimer
from PyQt5.QtGui import QMovie, QColor, QCursor
import psutil


class MainWindow(QWidget):
    """JARVIS Main Conversation Interface"""
    command_submitted = pyqtSignal(str)

    def __init__(self, manager=None):
        super().__init__() 
        self.manager = manager 
        self.old_pos = None
        
        # 1. Window Configuration - Larger conversational interface
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setWindowTitle("J.A.R.V.I.S. - Neural Interface")
        self.setFixedSize(500, 600)
        
        # Position: Center Right
        self.move(1300, 200) 

        # 2. Main Container Widget (for styling/transparency)
        self.container = QWidget(self)
        self.container.setObjectName("MainContainer")
        self.container.setStyleSheet("""
            QWidget#MainContainer {
                background-color: rgba(20, 20, 25, 230);
                border: 1px solid #4A90D9;
                border-radius: 15px;
            }
        """)
        
        # 3. Layouts
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self.container)

        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(12)
        
        # Header with Arc Reactor
        header_layout = QHBoxLayout()
        
        # Arc Reactor Glow
        self.core_label = QLabel(self)
        self.movie = QMovie("gui/assets/jarvis_glow.gif") 
        self.core_label.setMovie(self.movie)
        self.core_label.setFixedSize(80, 80)
        self.core_label.setScaledContents(True)
        header_layout.addWidget(self.core_label)
        self.movie.start()
        
        # Title
        title_layout = QVBoxLayout()
        title_label = QLabel("J.A.R.V.I.S.")
        title_label.setStyleSheet("""
            color: #4A90D9; font-size: 26px; font-weight: bold; 
            font-family: 'Segoe UI', sans-serif;
            letter-spacing: 2px;
        """)
        status_label = QLabel("NEURAL INTERFACE: OPTIMAL")
        status_label.setStyleSheet("""
            color: #5CACE2; font-size: 10px; font-weight: bold;
            font-family: 'Segoe UI', sans-serif;
            text-transform: uppercase;
        """)
        title_layout.addWidget(title_label)
        title_layout.addWidget(status_label)
        title_layout.addStretch()
        header_layout.addLayout(title_layout)
        
        self.main_layout.addLayout(header_layout)
        
        # Separator
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #444444;")
        self.main_layout.addWidget(sep)
        
        # 3. Chat History Area (Scrollable)
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: 1px solid rgba(74, 144, 217, 40);
                border-radius: 12px;
            }
            QScrollBar:vertical {
                background: rgba(20, 20, 25, 100);
                width: 6px;
                border-radius: 3px;
                margin: 0px 2px 0px 2px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4A90D9, stop:1 #2D5A8F);
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.chat_widget = QWidget()
        self.chat_widget.setStyleSheet("background-color: transparent;")
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setSpacing(12)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_layout.addStretch()
        self.chat_widget.setLayout(self.chat_layout)
        self.chat_scroll.setWidget(self.chat_widget)
        
        self.main_layout.addWidget(self.chat_scroll, 1)
        
        # 4. Input Area
        input_container = QWidget()
        input_container.setStyleSheet("""
            background-color: rgba(40, 40, 45, 200);
            border: 1px solid #4A90D944;
            border-radius: 12px;
            padding: 2px;
        """)
        input_layout = QVBoxLayout()
        input_layout.setContentsMargins(12, 6, 12, 6)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Awaiting command, sir...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: transparent; 
                color: #FFFFFF; 
                padding: 10px; 
                border: none;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
        """)
        self.input_field.setFocus()
        
        # Pulsing shadow effect
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(15)
        self.shadow_effect.setColor(QColor(74, 144, 217, 80))
        self.shadow_effect.setOffset(0, 0)
        self.container.setGraphicsEffect(self.shadow_effect)
        
        self.input_field.returnPressed.connect(self.submit_command)
        input_layout.addWidget(self.input_field)
        input_container.setLayout(input_layout)
        self.main_layout.addWidget(input_container)
        
        # 5. Quick Action Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        self.mic_btn = self._create_button("🎤 Listen", self.toggle_voice_input)
        self.settings_btn = self._create_button("⚙️ Settings", self.open_settings)
        self.help_btn = self._create_button("❓ Help", self.toggle_help)
        
        buttons_layout.addWidget(self.mic_btn)
        buttons_layout.addWidget(self.settings_btn)
        buttons_layout.addWidget(self.help_btn)
        buttons_layout.addStretch()
        
        self.main_layout.addLayout(buttons_layout)

        # 6. Animation
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(400)
        
        # 7. System Monitor
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_system_stats)
        self.stats_timer.start(5000)
        
        # Initial greeting
        self.add_message("J.A.R.V.I.S.", "Good evening, sir. How may I assist you?", is_jarvis=True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = None

    def _create_button(self, text, callback):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                color: #4A90D9;
                font-size: 11px;
                background-color: rgba(74, 144, 217, 10);
                border: 1px solid #4A90D955;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: rgba(74, 144, 217, 30);
            }
        """)
        btn.clicked.connect(callback)
        return btn

    def add_message(self, sender, message, is_jarvis=False):
        """Add a message to the chat history"""
        msg_widget = QWidget()
        msg_layout = QVBoxLayout()
        msg_layout.setContentsMargins(5, 5, 5, 5)
        
        # Sender name
        sender_label = QLabel(f"{'🤖' if is_jarvis else '👤'} {sender}")
        sender_label.setStyleSheet(f"""
            color: {'#4A90D9' if is_jarvis else '#88aacc'};
            font-size: 11px; font-weight: bold;
            font-family: 'Segoe UI', sans-serif;
        """)
        msg_layout.addWidget(sender_label)
        
        # Message content
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        
        if is_jarvis:
            # JARVIS Bubble: Premium dark blue glass effect
            bubble_style = """
                color: #B0D4FF;
                font-size: 13px;
                padding: 12px;
                background-color: rgba(74, 144, 217, 15);
                border: 1px solid rgba(74, 144, 217, 40);
                border-left: 3px solid #4A90D9;
                border-bottom-right-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom-left-radius: 2px;
                font-family: 'Segoe UI', sans-serif;
            """
        else:
            # User Bubble: Subtle dark gray effect
            bubble_style = """
                color: #FFFFFF;
                font-size: 13px;
                padding: 12px;
                background-color: rgba(60, 60, 70, 40);
                border: 1px solid rgba(255, 255, 255, 15);
                border-left: 3px solid #888888;
                border-bottom-right-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom-left-radius: 2px;
                font-family: 'Segoe UI', sans-serif;
            """
            
        msg_label.setStyleSheet(bubble_style)
        msg_layout.addWidget(msg_label)
        
        msg_widget.setLayout(msg_layout)
        
        # Insert before the stretch
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, msg_widget)
        
        # Auto-scroll to bottom using lambda to pass the value
        scroll_bar = self.chat_scroll.verticalScrollBar()
        QTimer.singleShot(50, lambda: scroll_bar.setValue(scroll_bar.maximum()))

    def toggle_voice_input(self):
        """Toggle voice input mode"""
        if self.manager and hasattr(self.manager, 'voice'):
            self.add_message("System", "Voice input activated. Speak now...", is_jarvis=True)
            self.manager.voice.speak("Voice input is not yet implemented. Please type your request.")

    def open_settings(self):
        """Open settings window"""
        if self.manager:
            self.manager.open_settings()

    def toggle_help(self):
        """Show help information"""
        help_text = """
<b>J.A.R.V.I.S. Task List:</b><br>
<ul>
<li><b>Open Settings / Preferences:</b> Adjust system parameters.</li>
<li><b>Help / Show Instructions:</b> Display this list of commands.</li>
<li><b>Read Screen / Analyze Chart:</b> Perform OCR on the screen.</li>
<li><b>Launch [app name]:</b> Open a desktop application.</li>
<li><b>Search For [query]:</b> Perform a web search.</li>
<li><b>Open URL [url]:</b> Open a web page.</li>
</ul>
Or just chat with me naturally!
        """.strip()
        self.add_message("J.A.R.V.I.S.", help_text, is_jarvis=True)

    def update_system_stats(self):
        """Monitor system load"""
        mem_usage = psutil.virtual_memory().percent 
        if mem_usage > 80:
            self.shadow_effect.setColor(QColor(255, 80, 0, 200))
        else:
            self.shadow_effect.setColor(QColor(74, 144, 217, 150))

    def display_response(self, text):
        """Display JARVIS response in chat"""
        self.add_message("J.A.R.V.I.S.", text, is_jarvis=True)

    def force_wake(self):
        """Bring window to front"""
        self.show()
        self.raise_()
        self.activateWindow()
        self.input_field.setFocus()
        self.enterEvent(None)

    def fade_to(self, opacity):
        self.fade_anim.stop()
        self.fade_anim.setEndValue(opacity)
        self.fade_anim.start()

    def submit_command(self):
        """Handle user input submission"""
        text = self.input_field.text().strip()
        if text:
            self.add_message("You", text, is_jarvis=False)
            self.input_field.clear()
            self.command_submitted.emit(text)
            self.input_field.setFocus()

    def trigger_purge_visual(self):
        """Emergency shutdown visual"""
        self.show()
        self.setWindowOpacity(1.0)
        self.chat_layout.insertWidget(0, QLabel("!!! CRITICAL: SYSTEM PURGE INITIATED !!!"))

    def enterEvent(self, event):
        if self.input_field.hasFocus():
            return
        self.fade_to(1.0)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    def leaveEvent(self, event):
        if not self.input_field.hasFocus():
            self.fade_to(0.85)

    def contextMenuEvent(self, event):
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.context_menu = QMenu(self)
        self.context_menu.setStyleSheet("""
            background-color: #2d2d2d; color: white; 
            border: 1px solid #444444;
        """)
        
        self.set_act = self.context_menu.addAction("System Preferences")
        self.help_act = self.context_menu.addAction("Toggle Protocols")
        self.exit_act = self.context_menu.addAction("Kill Process")

        action = self.context_menu.exec_(self.mapToGlobal(event.pos()))
        if action == self.set_act: 
            self.open_settings()
        elif action == self.help_act: 
            self.toggle_help()
        elif action == self.exit_act: 
            if self.manager:
                self.manager.terminate_session()
        self.leaveEvent(None)
