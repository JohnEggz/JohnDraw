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
        
        self.data_slots = {i: [] for i in range(5)}
        self.active_index = 0
        self.current_stroke = []
        self.store = None # Will be injected

    def set_state_store(self, store):
        self.store = store
        # Publish initial empty state
        self.publish_state()

    def publish_state(self):
        """Pushes current strokes to the central store for the Preview widget"""
        if self.store:
            current_data = self.data_slots.get(self.active_index, [])
            # We copy the list to ensure the update triggers even if ref is same
            self.store.set("current_strokes", list(current_data))

    def setActiveLine(self, index):
        try:
            idx = int(index)
            if 0 <= idx <= 4:
                self.active_index = idx
                self.update()
                self.publish_state() # Update preview when switching pages
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
            self.data_slots[self.active_index].append(self.current_stroke)
            self.current_stroke = []
            self.update()
            self.publish_state() # Update preview after drawing

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(pen)

        active_strokes = self.data_slots.get(self.active_index, [])
        for stroke in active_strokes:
            if len(stroke) > 1:
                painter.drawPolyline(stroke)

        if len(self.current_stroke) > 1:
            painter.drawPolyline(self.current_stroke)
