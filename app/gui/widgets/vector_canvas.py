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
        self.margin_px = 76 

    def set_state_store(self, store):
        self.store = store
        self.store.set("active_canvas_ref", self)
        
        existing_data = self.store.get("canvas_data")
        if existing_data:
            self.data_slots = existing_data
            
        saved_index = self.store.get("active_line")
        if saved_index is not None:
            self.active_index = int(saved_index)

        # Only recenter on initial load/reload
        self.recenter_view()
            
        self.update() 
        self.publish_state()

    # --- NEW: CLI Command Handler ---
    def move_canvas(self, x=0, y=0, animate=False):
        """
        Adjusts the offset by x/y.
        Called by the ActionDispatcher via a direct method call or property.
        """
        # In a real app, you might tween this value if animate=True
        new_x = self.offset.x() + int(x)
        new_y = self.offset.y() + int(y)
        self.offset = QPoint(new_x, new_y)
        self.update()
        # We don't necessarily save offset to store on every frame of animation
        # but for single moves, we can.
        if self.store:
            self.store.set("canvas_offset", (self.offset.x(), self.offset.y()))

    def publish_state(self):
        if self.store:
            current_data = self.data_slots.get(self.active_index, [])
            self.store.set("current_strokes", list(current_data))
            self.store.set("canvas_data", self.data_slots)

    def setActiveLine(self, index):
        try:
            self.active_index = int(index)
            # Re-center when switching context
            self.recenter_view()
            self.update()
            self.publish_state()
        except ValueError:
            pass
            
    def recenter_view(self):
        center_y = int(self.height() / 2)
        
        active_strokes = self.data_slots.get(self.active_index, [])
        
        if not active_strokes:
            max_x = 0
        else:
            max_x = float('-inf')
            found_points = False
            for stroke in active_strokes:
                for p in stroke:
                    found_points = True
                    if p.x() > max_x: max_x = p.x()
            if not found_points: max_x = 0
        
        target_x = self.width() - self.margin_px - max_x
        self.offset = QPoint(int(target_x), center_y)

    def resizeEvent(self, event):
        # Optional: Decide if resize should snap or just keep relative offset
        self.recenter_view()
        super().resizeEvent(event)

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
            # Note: No recenter_view() here anymore!
            self.update()
            self.publish_state()

    def _draw_grid(self, painter):
        painter.setPen(QPen(QColor("#e0e0e0"), 1))
        
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
        painter.translate(self.offset)
        self._draw_grid(painter)

        left_bound = -self.offset.x()
        right_bound = -self.offset.x() + self.width()
        
        red_pen = QPen(Qt.GlobalColor.red, 2)
        painter.setPen(red_pen)
        painter.drawLine(int(left_bound), 0, int(right_bound), 0)

        black_pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(black_pen)

        active_strokes = self.data_slots.get(self.active_index, [])
        for stroke in active_strokes:
            if len(stroke) > 1:
                painter.drawPolyline(stroke)

        if len(self.current_stroke) > 1:
            painter.drawPolyline(self.current_stroke)
