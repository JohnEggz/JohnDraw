from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import Qt

def main():
    return VectorCanvas()

class VectorCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
        # Storage: 5 slots, index 0 to 4. Each holds a list of strokes.
        self.data_slots = {i: [] for i in range(5)}
        self.active_index = 0
        self.current_stroke = []

    # --- Property used by State Binding ---
    def setActiveLine(self, index):
        """
        Called automatically by the Builder when $active_line changes.
        """
        try:
            idx = int(index)
            if 0 <= idx <= 4:
                self.active_index = idx
                self.update() # Redraw the new page
        except ValueError:
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.current_stroke = [event.pos()]
            self.update()

    def mouseMoveEvent(self, event):
        if self.current_stroke:
            self.current_stroke.append(event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.current_stroke:
            # Save to the CURRENT active slot
            self.data_slots[self.active_index].append(self.current_stroke)
            self.current_stroke = []
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Setup Pen
        pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(pen)

        # 1. Retrieve strokes for the ACTIVE page only
        active_strokes = self.data_slots.get(self.active_index, [])

        for stroke in active_strokes:
            if len(stroke) > 1:
                painter.drawPolyline(stroke)

        # 2. Draw currently active stroke
        if len(self.current_stroke) > 1:
            painter.drawPolyline(self.current_stroke)
