from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import Qt, QRectF

def main():
    return PreviewWidget()

class PreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(100, 100)
        self.setStyleSheet("background-color: #f0f0f0; border: 2px dashed #999;")
        self.strokes = []

    def setStrokes(self, data):
        """
        Called automatically when $current_strokes changes.
        """
        # Debug: Check what we are receiving
        # print(f"Preview received type: {type(data)}") 
        
        if isinstance(data, list):
            self.strokes = data
            self.update()
        else:
            print(f"PreviewWidget Error: Expected list, got {type(data)}")

    def get_bounds(self):
        """Calculates the Bounding Box of all points"""
        if not self.strokes:
            return None
        
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        has_points = False

        for stroke in self.strokes:
            for p in stroke:
                has_points = True
                if p.x() < min_x: min_x = p.x()
                if p.x() > max_x: max_x = p.x()
                if p.y() < min_y: min_y = p.y()
                if p.y() > max_y: max_y = p.y()
        
        if not has_points: return None
        
        # Add a tiny padding so lines don't touch edges
        padding = 10
        return QRectF(min_x - padding, min_y - padding, 
                      (max_x - min_x) + padding*2, (max_y - min_y) + padding*2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Background
        painter.fillRect(self.rect(), QColor("#f0f0f0"))

        if not self.strokes:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No Data")
            return

        bounds = self.get_bounds()
        if not bounds: return

        # 2. Calculate Scaling to Fit "Perfectly"
        # We want to map 'bounds' to 'self.rect()' keeping aspect ratio
        
        widget_w = self.width()
        widget_h = self.height()
        
        scale_x = widget_w / bounds.width() if bounds.width() > 0 else 1
        scale_y = widget_h / bounds.height() if bounds.height() > 0 else 1
        
        # Use the smaller scale to ensure it fits entirely
        scale = min(scale_x, scale_y)
        
        # Center the result
        scaled_w = bounds.width() * scale
        scaled_h = bounds.height() * scale
        offset_x = (widget_w - scaled_w) / 2
        offset_y = (widget_h - scaled_h) / 2

        # 3. Apply Transformations
        painter.translate(offset_x, offset_y)
        painter.scale(scale, scale)
        painter.translate(-bounds.x(), -bounds.y()) # Move origin to top-left of drawing

        # 4. Draw
        # Use a cosmetic pen (width 0) or fixed width relative to scale?
        # A width of 2 might look huge if scaled up. 
        # Let's use 2.0 / scale so it always looks like 2px on screen.
        pen_width = 2.0 / scale if scale > 0 else 2
        pen = QPen(Qt.GlobalColor.black, pen_width)
        painter.setPen(pen)

        for stroke in self.strokes:
            if len(stroke) > 1:
                painter.drawPolyline(stroke)
