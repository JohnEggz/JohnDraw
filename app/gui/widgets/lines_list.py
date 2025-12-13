from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QScrollArea, QFrame
from PyQt6.QtCore import Qt
from functools import partial

def main():
    return LinesList()

class LinesList(QWidget):
    def __init__(self):
        super().__init__()
        # Internal State
        self.store = None
        self.buttons = {} # { index: QPushButton }
        self.next_id = 0
        self.current_active = 0

        # --- Layout Structure ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)

        # 1. Add Button
        self.btn_add = QPushButton("+ New Line")
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.btn_add.clicked.connect(self.add_line)
        self.main_layout.addWidget(self.btn_add)

        # 2. Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.main_layout.addWidget(self.scroll)

        # 3. Container
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.container_layout.setContentsMargins(0,0,0,0)
        self.scroll.setWidget(self.container)

        # Initialize with 1 line
        self.add_line()

    def set_state_store(self, store):
        self.store = store
        # FIX: Changed 'select_line' to 'on_line_click'
        self.on_line_click(0)

    def add_line(self):
        line_id = self.next_id
        self.next_id += 1

        btn = QPushButton(f"Line {line_id + 1}")
        btn.setCheckable(True)
        btn.setStyleSheet("text-align: left; padding: 8px;")
        btn.clicked.connect(partial(self.on_line_click, line_id))
        
        self.container_layout.addWidget(btn)
        self.buttons[line_id] = btn

        # Auto-select the new line
        self.on_line_click(line_id)

    def on_line_click(self, line_id):
        # 1. Update Global State
        if self.store:
            self.store.set("active_line", line_id)
        
        # 2. Update Visuals
        self.update_visuals(line_id)

    # Bound to $active_line in TOML
    def setActiveLine(self, index):
        try:
            idx = int(index)
            self.update_visuals(idx)
        except: pass

    def update_visuals(self, active_id):
        self.current_active = active_id
        for lid, btn in self.buttons.items():
            was_blocked = btn.blockSignals(True)
            is_active = (lid == active_id)
            btn.setChecked(is_active)
            
            if is_active:
                btn.setStyleSheet("text-align: left; padding: 8px; background-color: #0078d7; color: white; border: none;")
            else:
                btn.setStyleSheet("text-align: left; padding: 8px; background-color: #f0f0f0; border: 1px solid #ddd;")
            
            btn.blockSignals(was_blocked)
