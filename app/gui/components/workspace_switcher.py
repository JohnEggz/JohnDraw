import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from app.gui.components.layout_builder import LayoutBuilder
from app.core.state_manager import StateStore
from app.core.action_dispatcher import ActionDispatcher # <--- Import

class WorkspaceSwitcher(QWidget):
    def __init__(self, base_dir, plugin_dir):
        super().__init__()
        self.base_dir = base_dir
        self.plugin_dir = plugin_dir
        self.current_ui = None
        
        # 1. Core Logic Setup
        self.state_store = StateStore() 
        self.dispatcher = ActionDispatcher(self.state_store) # <--- Init Dispatcher

        # Default State
        self.state_store.set("count", 0)
        self.state_store.set("status", "System Ready")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def load_workspace(self, workspace_name):
        if not workspace_name: return
        
        if self.current_ui:
            self.layout.removeWidget(self.current_ui)
            self.current_ui.deleteLater()
            self.current_ui = None

        try:
            builder = LayoutBuilder(
                workspace_name, 
                base_dir=self.base_dir,
                plugin_dir=self.plugin_dir,
                state_store=self.state_store,
                # 2. Pass the Dispatcher Method
                command_handler=self.dispatcher.dispatch 
            )
            self.current_ui = builder.build()
            self.layout.addWidget(self.current_ui)
        except Exception as e:
            self._show_error(workspace_name, str(e))

    def _show_error(self, name, error_msg):
        err = QLabel(f"❌ Error loading '{name}':\n\n{error_msg}")
        err.setStyleSheet("color: #d32f2f; padding: 20px; background: #ffebee; font-family: monospace;")
        err.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.current_ui = err
        self.layout.addWidget(err)
