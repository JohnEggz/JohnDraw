from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QScrollArea, QFrame, QLabel
from PyQt6.QtGui import QPainter, QPen, QColor, QMouseEvent
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from functools import partial

def main():
    return LinesList()

class LineButton(QFrame):
    clicked = pyqtSignal()

    def __init__(self, index):
        super().__init__()
        self.index = index
        self.strokes = []
        self.is_active = False
        
        self.setFixedSize(160, 120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Simple styling
        self.default_style = """
            LineButton { 
                background-color: #ffffff; 
                border: 1px solid #ddd; 
                border-radius: 8px; 
            }
        """
        self.active_style = """
            LineButton { 
                background-color: #e3f2fd; 
                border: 2px solid #2196F3; 
                border-radius: 8px; 
            }
        """
        self.setStyleSheet(self.default_style)

        # Layout for Text Label
        self.layout = QVBoxLayout(self)
        self.label = QLabel(f"Line {index + 1}")
        self.label.setStyleSheet("background: transparent; color: #555; font-weight: bold;")
        self.layout.addWidget(self.label)
        self.layout.addStretch() # Push label to top

    def set_active(self, active: bool):
        self.is_active = active
        self.setStyleSheet(self.active_style if active else self.default_style)
        self.label.setStyleSheet(f"background: transparent; color: {'#2196F3' if active else '#555'}; font-weight: bold;")

    def set_strokes(self, strokes):
        self.strokes = strokes
        self.update() # Trigger repaint

    def mousePressEvent(self, event: QMouseEvent):
        self.clicked.emit()

    def paintEvent(self, event):
        # 1. Draw standard frame/background
        super().paintEvent(event)
        
        # 2. Draw Mini Preview
        if not self.strokes:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate Bounds
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        
        for stroke in self.strokes:
            for p in stroke:
                if p.x() < min_x: min_x = p.x()
                if p.x() > max_x: max_x = p.x()
                if p.y() < min_y: min_y = p.y()
                if p.y() > max_y: max_y = p.y()

        # Scaling Logic
        content_w = max_x - min_x
        content_h = max_y - min_y
        if content_w <= 0 or content_h <= 0: return # Single point

        # We draw in the bottom area (padding 10px from sides, 30px from top)
        draw_rect = self.rect().adjusted(10, 30, -10, -10)
        
        scale_x = draw_rect.width() / content_w
        scale_y = draw_rect.height() / content_h
        scale = min(scale_x, scale_y)

        # Center
        scaled_w = content_w * scale
        scaled_h = content_h * scale
        offset_x = draw_rect.left() + (draw_rect.width() - scaled_w) / 2
        offset_y = draw_rect.top() + (draw_rect.height() - scaled_h) / 2

        painter.translate(offset_x, offset_y)
        painter.scale(scale, scale)
        painter.translate(-min_x, -min_y)

        # Draw
        pen = QPen(Qt.GlobalColor.black, 2.0 / scale) # Maintain constant visual width
        painter.setPen(pen)
        
        for stroke in self.strokes:
            if len(stroke) > 1:
                painter.drawPolyline(stroke)


class LinesList(QWidget):
    def __init__(self):
        super().__init__()
        self.store = None
        self.buttons = {} # { index: LineButton }
        self.next_id = 0
        self.current_active = 0

        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)

        # Add Button
        self.btn_add = QPushButton("+ New Line")
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.btn_add.clicked.connect(self.add_line)
        self.main_layout.addWidget(self.btn_add)

        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        self.main_layout.addWidget(self.scroll)

        # Container
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.container_layout.setSpacing(10)
        self.scroll.setWidget(self.container)

        self.add_line()

    def set_state_store(self, store):
        self.store = store
        self.store.subscribe("canvas_data", self.on_canvas_data_update)
        self.on_line_click(0)

    def on_canvas_data_update(self, all_data):
        """
        Called when VectorCanvas pushes new data.
        all_data = { 0: [...], 1: [...] }
        """
        if not isinstance(all_data, dict): return
        
        for index, strokes in all_data.items():
            if index in self.buttons:
                self.buttons[index].set_strokes(strokes)

    def add_line(self):
        line_id = self.next_id
        self.next_id += 1

        btn = LineButton(line_id)
        btn.clicked.connect(partial(self.on_line_click, line_id))
        
        self.container_layout.addWidget(btn)
        self.buttons[line_id] = btn
        self.on_line_click(line_id)

    def on_line_click(self, line_id):
        if self.store:
            self.store.set("active_line", line_id)
        self.update_visuals(line_id)

    def setActiveLine(self, index):
        try:
            self.update_visuals(int(index))
        except: pass

    def update_visuals(self, active_id):
        self.current_active = active_id
        for lid, btn in self.buttons.items():
            btn.set_active(lid == active_id)
