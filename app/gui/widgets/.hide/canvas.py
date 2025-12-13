# widgets/canvas.py
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QPainterPath, QColor, QInputDevice
from PyQt6.QtCore import Qt

class Canvas(QWidget):
    def __init__(self):
        super().__init__()
        self.paths = [] 
        self.current_path = None
        
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.GlobalColor.white)
        self.setPalette(p)

    def set_paths(self, new_paths):
        """ Replaces current paths with a list from FrameData """
        self.paths = list(new_paths) 
        self.update()
    
    def get_paths(self):
        """ Returns the current list of paths for saving """
        return self.paths

    def mousePressEvent(self, event):
        # Ignore Touchscreen (Finger)
        if event.device().type() == QInputDevice.DeviceType.TouchScreen: return
        
        if event.button() == Qt.MouseButton.LeftButton:
            self.current_path = QPainterPath()
            self.current_path.moveTo(event.position())
            self.paths.append(self.current_path)
            self.update()

    def mouseMoveEvent(self, event):
        if event.device().type() == QInputDevice.DeviceType.TouchScreen: return
        
        if self.current_path and (event.buttons() & Qt.MouseButton.LeftButton):
            self.current_path.lineTo(event.position())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.device().type() == QInputDevice.DeviceType.TouchScreen: return
        
        if event.button() == Qt.MouseButton.LeftButton:
            self.current_path = None
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Grid (40px)
        pen = QPen(QColor(240, 240, 240), 1)
        painter.setPen(pen)
        for x in range(0, self.width(), 40): 
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 40): 
            painter.drawLine(0, y, self.width(), y)

        # Draw Paths (Black, 2px)
        pen = QPen(QColor("black"), 2, Qt.PenStyle.SolidLine, 
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        for path in self.paths: 
            painter.drawPath(path)
        
        if self.current_path: 
            painter.drawPath(self.current_path)
