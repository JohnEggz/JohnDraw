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
        
        self.data_slots = {} 
        self.active_index = 0
        self.current_stroke = []
        self.store = None

    def set_state_store(self, store):
        self.store = store
        
        # --- NEW: Restore State on Load ---
        # 1. Check for existing drawings
        existing_data = self.store.get("canvas_data")
        if existing_data:
            # We copy it so we don't accidentally mutate the store directly 
            # without calling .set() (though in Python dicts are ref, so it's subtle)
            self.data_slots = existing_data
            
        # 2. Check for active line index
        saved_index = self.store.get("active_line")
        if saved_index is not None:
            self.active_index = int(saved_index)
            
        self.update() # Force repaint with loaded data
        self.publish_state() # Ensure other widgets (like previews) get the data

    def publish_state(self):
        if self.store:
            current_data = self.data_slots.get(self.active_index, [])
            self.store.set("current_strokes", list(current_data))
            self.store.set("canvas_data", self.data_slots) # Save full dict

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
            self.data_slots.setdefault(self.active_index, []).append(self.current_stroke)
            self.current_stroke = []
            self.update()
            self.publish_state()

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
