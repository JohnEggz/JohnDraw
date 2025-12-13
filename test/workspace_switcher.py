from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from test.layout_builder import JsonUiBuilder

class WorkspaceSwitcher(QWidget):
    def __init__(self, base_dir="workspaces"):
        super().__init__()
        self.base_dir = base_dir
        self.current_ui = None
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

    # --- The API Handler ---
    def handle_api_command(self, cmd_obj):
        """
        Receives a Command object from command_parser.py
        """
        print(f"⚡ EXEC: {cmd_obj.name}")
        print(f"   Args:   {cmd_obj.args}")
        print(f"   Kwargs: {cmd_obj.kwargs}")
        print(f"   Flags:  {cmd_obj.flags}")

        if cmd_obj.name == "canvas":
            if "move" in cmd_obj.args:
                x = int(cmd_obj.kwargs.get("x", 0))
                y = int(cmd_obj.kwargs.get("y", 0))
                print(f"   -> Moving canvas by X={x}, Y={y}")
                if "animate" in cmd_obj.flags:
                    print("   -> (Animation Enabled)")

    def load_workspace(self, workspace_name):
        if not workspace_name: return
        if self.current_ui:
            self.layout.removeWidget(self.current_ui)
            self.current_ui.deleteLater()
            self.current_ui = None

        try:
            # Pass the handler here
            builder = JsonUiBuilder(
                workspace_name, 
                base_dir=self.base_dir,
                command_handler=self.handle_api_command 
            )
            self.current_ui = builder.build()
            self.layout.addWidget(self.current_ui)
        except Exception as e:
            self._show_error(workspace_name, str(e))

    def _show_error(self, name, error_msg):
        # (Same as previous implementation)
        err_widget = QLabel(f"❌ Error loading '{name}':\n\n{error_msg}")
        err_widget.setStyleSheet("color: #d32f2f; padding: 20px; background: #ffebee;")
        self.current_ui = err_widget
        self.layout.addWidget(err_widget)
