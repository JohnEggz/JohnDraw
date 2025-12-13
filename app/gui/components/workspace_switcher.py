import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from app.core.router import CommandRouter
from app.gui.components.layout_builder import LayoutBuilder

class WorkspaceSwitcher(QWidget):
    def __init__(self, base_dir, plugin_dir):
        super().__init__()
        self.base_dir = base_dir
        self.plugin_dir = plugin_dir
        self.current_ui = None
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def handle_api_command(self, cmd_obj):
        """
        Application Logic (Controller)
        """
        print(f"⚡ EXEC: {cmd_obj.name}")
        print(f"   Args:   {cmd_obj.args}")
        print(f"   Kwargs: {cmd_obj.kwargs}")

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
                command_handler=CommandRouter.process
            )
            self.current_ui = builder.build()
            self.layout.addWidget(self.current_ui)
        except Exception as e:
            self._show_error(workspace_name, str(e))

    def _show_error(self, name, error_msg):
        err_widget = QLabel(f"❌ Error loading '{name}':\n\n{error_msg}")
        err_widget.setStyleSheet("color: #d32f2f; padding: 20px; background: #ffebee; font-family: monospace;")
        err_widget.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.current_ui = err_widget
        self.layout.addWidget(err_widget)
