import os
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton, QFrame
from app.gui.components.workspace_switcher import WorkspaceSwitcher

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App Core")
        self.resize(1000, 700)

        # --- Resolve Paths Relative to this file ---
        # Current file is in app/gui/
        base_gui_path = os.path.dirname(__file__)
        self.workspaces_path = os.path.join(base_gui_path, "workspaces")
        self.widgets_path = os.path.join(base_gui_path, "widgets")

        # --- Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Toolbar ---
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Workspace:"))
        
        self.combo = QComboBox()
        self.combo.setMinimumWidth(200)
        self.combo.currentTextChanged.connect(self.on_combo_change)
        toolbar.addWidget(self.combo)
        
        btn_reload = QPushButton("Reload")
        btn_reload.clicked.connect(lambda: self.on_combo_change(self.combo.currentText()))
        toolbar.addWidget(btn_reload)
        toolbar.addStretch()
        
        main_layout.addLayout(toolbar)
        main_layout.addWidget(self._create_divider())

        # --- Switcher ---
        self.switcher = WorkspaceSwitcher(
            base_dir=self.workspaces_path,
            plugin_dir=self.widgets_path
        )
        main_layout.addWidget(self.switcher, stretch=1)

        self.scan_workspaces()

    def _create_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def scan_workspaces(self):
        if not os.path.exists(self.workspaces_path):
            os.makedirs(self.workspaces_path)
            
        files = os.listdir(self.workspaces_path)
        workspaces = set()
        
        for f in files:
            name, ext = os.path.splitext(f)
            # Ignore directories like 'defaults'
            if os.path.isdir(os.path.join(self.workspaces_path, f)):
                continue
            if ext in ['.json', '.toml']:
                workspaces.add(name)
            
        sorted_ws = sorted(list(workspaces))
        
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(sorted_ws)
        self.combo.blockSignals(False)

        if sorted_ws:
            self.on_combo_change(sorted_ws[0])

    def on_combo_change(self, text):
        self.switcher.load_workspace(text)
