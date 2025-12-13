from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import Qt, QPoint

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
        
        # Panning State
        self.offset = QPoint(0, 0)
        self.grid_spacing = 19 

    def set_state_store(self, store):
        self.store = store
        
        existing_data = self.store.get("canvas_data")
        if existing_data:
            self.data_slots = existing_data
            
        saved_index = self.store.get("active_line")
        if saved_index is not None:
            self.active_index = int(saved_index)

        saved_offset = self.store.get("canvas_offset")
        if saved_offset:
            self.offset = QPoint(saved_offset[0], saved_offset[1])
            
        self.update() 
        self.publish_state()

    def publish_state(self):
        if self.store:
            current_data = self.data_slots.get(self.active_index, [])
            self.store.set("current_strokes", list(current_data))
            self.store.set("canvas_data", self.data_slots)
            self.store.set("canvas_offset", (self.offset.x(), self.offset.y()))

    def setActiveLine(self, index):
        try:
            self.active_index = int(index)
            self.update()
            self.publish_state()
        except ValueError:
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            world_pos = event.pos() - self.offset
            self.current_stroke = [world_pos]
            self.update()

    def mouseMoveEvent(self, event):
        if self.current_stroke:
            world_pos = event.pos() - self.offset
            self.current_stroke.append(world_pos)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.current_stroke:
            self.data_slots.setdefault(self.active_index, []).append(self.current_stroke)
            self.current_stroke = []
            self.update()
            self.publish_state()

    def _draw_grid(self, painter):
        # Light blue grid lines
        painter.setPen(QPen(QColor("#e0e0e0"), 1))
        
        # Calculate viewport bounds in World Coordinates
        left = -self.offset.x()
        top = -self.offset.y()
        right = left + self.width()
        bottom = top + self.height()

        first_x = int(left - (left % self.grid_spacing))
        first_y = int(top - (top % self.grid_spacing))

        for x in range(first_x, int(right) + self.grid_spacing, self.grid_spacing):
            painter.drawLine(x, int(top), x, int(bottom))

        for y in range(first_y, int(bottom) + self.grid_spacing, self.grid_spacing):
            painter.drawLine(int(left), y, int(right), y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Apply Transformation
        painter.translate(self.offset)

        # 2. Draw Grid
        self._draw_grid(painter)

        # 3. Draw Axis (Red Horizontal Line at Y=0)
        # We calculate the visible left/right bounds so the line always spans the screen
        left_bound = -self.offset.x()
        right_bound = -self.offset.x() + self.width()
        
        red_pen = QPen(Qt.GlobalColor.red, 2)
        painter.setPen(red_pen)
        painter.drawLine(int(left_bound), 0, int(right_bound), 0)

        # 4. Draw Strokes
        black_pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(black_pen)

        active_strokes = self.data_slots.get(self.active_index, [])
        for stroke in active_strokes:
            if len(stroke) > 1:
                painter.drawPolyline(stroke)

        if len(self.current_stroke) > 1:
            painter.drawPolyline(self.current_stroke)
