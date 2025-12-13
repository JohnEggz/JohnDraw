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
        
        # We no longer pre-fill 5 slots. It grows dynamically.
        self.data_slots = {} 
        self.active_index = 0
        self.current_stroke = []
        self.store = None

    def set_state_store(self, store):
        self.store = store
        self.publish_state()

    def publish_state(self):
        if self.store:
            # Safely get data, defaulting to empty list
            current_data = self.data_slots.get(self.active_index, [])
            self.store.set("current_strokes", list(current_data))

    def setActiveLine(self, index):
        try:
            self.active_index = int(index)
            self.update()
            self.publish_state()
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
            # FIX: Automatically create the list if it doesn't exist yet
            self.data_slots.setdefault(self.active_index, []).append(self.current_stroke)
            
            self.current_stroke = []
            self.update()
            self.publish_state()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(pen)

        # Safely retrieve data
        active_strokes = self.data_slots.get(self.active_index, [])
        for stroke in active_strokes:
            if len(stroke) > 1:
                painter.drawPolyline(stroke)

        if len(self.current_stroke) > 1:
            painter.drawPolyline(self.current_stroke)
