from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import Qt, QPoint

def main():
    return VectorCanvas()

class VectorCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: white;")
        
        # Data structure: A list of lists. 
        # [ [p1, p2, p3], [p1, p2] ] represents 2 separate lines.
        self.strokes = [] 
        self.current_stroke = []

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.current_stroke = [event.pos()]
            self.update() # Trigger repaint

    def mouseMoveEvent(self, event):
        if self.current_stroke:
            self.current_stroke.append(event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.current_stroke:
            self.strokes.append(self.current_stroke)
            self.current_stroke = []
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Setup Pen (Black, 2px width)
        pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(pen)

        # 1. Draw finished strokes
        for stroke in self.strokes:
            if len(stroke) > 1:
                painter.drawPolyline(stroke)

        # 2. Draw currently active stroke
        if len(self.current_stroke) > 1:
            painter.drawPolyline(self.current_stroke)
