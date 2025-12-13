# widgets/preview.py
from PyQt6.QtWidgets import QFrame, QSizePolicy
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QRectF

class FramePreviewWidget(QFrame):
    """
    Displays a read-only vector preview.
    Modes: 'fit_width' (Left Panel), 'fit_height' (Right Panel)
    """
    clicked = pyqtSignal(int)

    def __init__(self, frame_data, mode='fit_width'):
        super().__init__()
        self.frame_data = frame_data
        self.mode = mode
        
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(1)
        
        if self.mode == 'fit_width':
            self.setMinimumHeight(50) 
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.GlobalColor.white)
        self.setPalette(p)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.frame_data.index)

    def update_geometry_from_content(self):
        """ Resizes widget height based on aspect ratio (for Left Panel) """
        if not self.frame_data.paths or self.mode != 'fit_width':
            return

        total_rect = self.get_content_rect()
        if total_rect.isEmpty(): return

        aspect_ratio = total_rect.height() / total_rect.width()
        available_width = self.width() - 10 
        new_height = int(available_width * aspect_ratio) + 20
        
        self.setMinimumHeight(new_height)
        self.setMaximumHeight(new_height)

    def get_content_rect(self):
        if not self.frame_data.paths:
            return QRectF()
        
        rect = self.frame_data.paths[0].boundingRect()
        for path in self.frame_data.paths:
            rect = rect.united(path.boundingRect())
        return rect

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.frame_data or not self.frame_data.paths:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 
                             f"Line {self.frame_data.index + 1}\n(Empty)")
            return

        content_rect = self.get_content_rect()
        if content_rect.width() == 0 or content_rect.height() == 0:
            return

        margin = 10
        w_avail = self.width() - (margin * 2)
        h_avail = self.height() - (margin * 2)
        scale = 1.0

        if self.mode == 'fit_width':
            scale = w_avail / content_rect.width()
        elif self.mode == 'fit_height':
            scale = h_avail / content_rect.height()

        painter.save()
        painter.translate(margin, margin)
        painter.scale(scale, scale)
        painter.translate(-content_rect.left(), -content_rect.top())

        pen = QPen(QColor("black"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        pen.setWidthF(2.0 / scale) 
        painter.setPen(pen)

        for path in self.frame_data.paths:
            painter.drawPath(path)
            
        painter.restore()
        
        painter.setPen(QColor("blue"))
        painter.drawText(10, 20, f"#{self.frame_data.index + 1}")
