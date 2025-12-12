from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QScrollArea, QLabel, QFrame)
from PyQt6.QtCore import Qt, QPoint

# Import from our modules
from models import FrameData
from widgets.canvas import Canvas
from widgets.preview import FramePreviewWidget
from widgets.toolbox import Toolbox  # <--- NEW IMPORT

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arch Vector Architect")
        self.resize(1200, 800)

        self.frames = [] 
        self.current_frame_index = -1
        self.preview_widgets = [] 

        # --- SETUP UI ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # 1. LEFT PANEL (List)
        left_panel = QWidget()
        left_panel.setFixedWidth(600)
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("<b>LINES</b>"))
        
        self.scroll = QScrollArea()
        self.scroll_container = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_container)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll.setWidget(self.scroll_container)
        self.scroll.setWidgetResizable(True)
        left_layout.addWidget(self.scroll)

        # 2. MIDDLE PANEL (Context)
        middle_panel = QFrame()
        middle_panel.setFixedWidth(250)
        middle_panel.setStyleSheet("background-color: #f0f0f0;")
        middle_layout = QVBoxLayout(middle_panel)
        middle_layout.addWidget(QLabel("<b>Context</b>"))
        middle_layout.addStretch() 

        # 3. RIGHT PANEL (Editor)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0,0,0,0)
        
        # A. Top Preview
        self.top_preview_container = QWidget()
        self.top_preview_container.setFixedHeight(120)
        self.top_preview_layout = QVBoxLayout(self.top_preview_container)
        self.top_preview_layout.setContentsMargins(0,0,0,0)
        self.top_preview_widget = None

        # B. Toolbox (Replaced manual buttons with Toolbox Widget)
        self.toolbox = Toolbox()
        # Connect Signals
        self.toolbox.toolChanged.connect(self.on_tool_changed)
        self.toolbox.colorChanged.connect(self.on_color_changed)
        self.toolbox.newFrameRequested.connect(self.on_new_frame)
        self.toolbox.moveRequested.connect(self.on_move_canvas)

        # C. Canvas
        self.canvas = Canvas()
        
        right_layout.addWidget(QLabel("Previous Line:"))
        right_layout.addWidget(self.top_preview_container)
        right_layout.addWidget(self.toolbox) # Add Toolbox Widget
        right_layout.addWidget(self.canvas, stretch=1) 

        main_layout.addWidget(left_panel)
        main_layout.addWidget(middle_panel)
        main_layout.addWidget(right_panel)

        self.create_frame() 

    # --- ACTION HANDLERS ---
    
    def on_tool_changed(self, tool_name):
        print(f"Window: Set Tool to {tool_name}")
        # TODO: Implement set_tool method in Canvas
        # self.canvas.current_tool = tool_name 

    def on_color_changed(self, color_name):
        print(f"Window: Set Color to {color_name}")
        # TODO: Implement set_color method in Canvas
        # self.canvas.current_color = QColor(color_name)

    def on_new_frame(self, relation):
        print(f"Window: Creating Frame with relation: {relation}")
        # Pass the relation string to the new frame logic if needed
        self.create_frame() 

    def on_move_canvas(self, direction):
        print(f"Window: Move Canvas {direction}")
        # TODO: Implement move/scroll in Canvas
        # e.g., self.canvas.scroll(dx, dy)

    # --- CORE LOGIC ---

    def create_frame(self):
        self.save_current_frame()
        new_index = len(self.frames)
        new_frame = FrameData(new_index)
        self.frames.append(new_frame)
        
        preview = FramePreviewWidget(new_frame, mode='fit_width')
        preview.clicked.connect(self.switch_to_frame)
        self.scroll_layout.addWidget(preview)
        self.preview_widgets.append(preview)
        self.switch_to_frame(new_index)

    def save_current_frame(self):
        if self.current_frame_index >= 0:
            current_frame = self.frames[self.current_frame_index]
            current_frame.paths = list(self.canvas.get_paths())
            widget = self.preview_widgets[self.current_frame_index]
            widget.update_geometry_from_content() 
            widget.update() 

    def switch_to_frame(self, index):
        self.save_current_frame()
        self.current_frame_index = index
        frame = self.frames[index]
        self.canvas.set_paths(frame.paths)

        if self.top_preview_widget:
            self.top_preview_layout.removeWidget(self.top_preview_widget)
            self.top_preview_widget.deleteLater()
            self.top_preview_widget = None

        if index > 0:
            prev_frame = self.frames[index - 1]
            self.top_preview_widget = FramePreviewWidget(prev_frame, mode='fit_height')
            self.top_preview_layout.addWidget(self.top_preview_widget)
        else:
            lbl = QLabel("No Previous Line")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.top_preview_widget = lbl
            self.top_preview_layout.addWidget(lbl)
