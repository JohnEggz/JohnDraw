import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from app.gui.components.layout_builder import LayoutBuilder
from app.core.state_manager import StateStore # <--- Import

class WorkspaceSwitcher(QWidget):
    def __init__(self, base_dir, plugin_dir):
        super().__init__()
        self.base_dir = base_dir
        self.plugin_dir = plugin_dir
        self.current_ui = None
        
        # Initialize the Central State Store
        self.state_store = StateStore() 
        # Set some default values
        self.state_store.set("app_version", "1.0.0")
        self.state_store.set("status", "Ready")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def handle_api_command(self, cmd_obj):
        """
        Handles commands from the UI.
        """
        print(f"⚡ EXEC: {cmd_obj.name} | Args: {cmd_obj.args} | Kwargs: {cmd_obj.kwargs}")

        # --- FEATURE: State Management Command ---
        # Command: state set --key=status --value="Processing..."
        if cmd_obj.name == "state":
            if "set" in cmd_obj.args:
                key = cmd_obj.kwargs.get("key")
                val = cmd_obj.kwargs.get("value")
                if key and val:
                    print(f"   -> Updating State: {key} = {val}")
                    self.state_store.set(key, val)
        
        # Example: Mocking other commands
        elif cmd_obj.name == "canvas":
            self.state_store.set("status", f"Canvas Action: {cmd_obj.args}")

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
                state_store=self.state_store, # <--- Pass the store
                command_handler=self.handle_api_command 
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
