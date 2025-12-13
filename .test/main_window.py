import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QComboBox, QLabel, QPushButton, QFrame)
from test.workspace_switcher import WorkspaceSwitcher

class DevHarness(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Builder Test Harness")
        self.resize(1000, 700)
        self.base_dir = "test/workspaces"

        # --- Main Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- 1. Dev Toolbar (The UI you wanted moved here) ---
        toolbar = QHBoxLayout()
        
        # Label
        lbl = QLabel("Workspace:")
        lbl.setStyleSheet("font-weight: bold; color: #333;")
        toolbar.addWidget(lbl)
        
        # Dropdown
        self.combo = QComboBox()
        self.combo.setMinimumWidth(200)
        self.combo.currentTextChanged.connect(self.on_combo_change)
        toolbar.addWidget(self.combo)
        
        # Reload Button
        btn_reload = QPushButton("Reload")
        btn_reload.clicked.connect(lambda: self.on_combo_change(self.combo.currentText()))
        toolbar.addWidget(btn_reload)
        
        toolbar.addStretch()
        main_layout.addLayout(toolbar)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        # --- 2. The Switcher (Pure Logic/Display) ---
        self.switcher = WorkspaceSwitcher(base_dir=self.base_dir)
        main_layout.addWidget(self.switcher, stretch=1)

        # --- 3. Initialize ---
        self.scan_workspaces()

    def scan_workspaces(self):
        """Scans directory and populates dropdown"""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            
        files = os.listdir(self.base_dir)
        workspaces = set()
        
        for f in files:
            name, ext = os.path.splitext(f)
            if name == "default" or ext not in ['.json', '.toml']:
                continue
            workspaces.add(name)
            
        sorted_ws = sorted(list(workspaces))
        
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(sorted_ws)
        self.combo.blockSignals(False)

        if sorted_ws:
            self.on_combo_change(sorted_ws[0])

    def on_combo_change(self, text):
        # Pass the command down to the logic component
        self.switcher.load_workspace(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DevHarness()
    window.show()
    sys.exit(app.exec())
