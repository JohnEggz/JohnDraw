from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal
from functools import partial

def main():
    return LinesList()

class LinesList(QWidget):
    # Define distinct signals for TOML to bind to
    select_0 = pyqtSignal()
    select_1 = pyqtSignal()
    select_2 = pyqtSignal()
    select_3 = pyqtSignal()
    select_4 = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.buttons = []
        
        # Map indices to signals
        self.signals = [self.select_0, self.select_1, self.select_2, self.select_3, self.select_4]

        for i in range(5):
            btn = QPushButton(f"Line {i + 1}")
            btn.setCheckable(True)
            btn.clicked.connect(partial(self.on_click, i))
            self.layout.addWidget(btn)
            self.buttons.append(btn)
        
        self.layout.addStretch()

    def on_click(self, index):
        # Emit the specific signal for this index
        self.signals[index].emit()

    def setActiveLine(self, index):
        try:
            idx = int(index)
            for i, btn in enumerate(self.buttons):
                btn.setChecked(i == idx)
                if i == idx:
                    btn.setStyleSheet("background-color: #0078d7; color: white;")
                else:
                    btn.setStyleSheet("")
        except: pass
