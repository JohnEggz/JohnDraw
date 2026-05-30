import sys
import json
import os
import tomllib
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QLabel, 
                             QVBoxLayout, QWidget, QHBoxLayout, QLineEdit, 
                             QPushButton, QDialog, QTabWidget, QListWidget, QListWidgetItem, QFormLayout,
                             QGraphicsPixmapItem, QGraphicsItem, QGraphicsPathItem, QComboBox)
from PySide6.QtCore import Qt, QSettings, QEvent, QTimer, QRect, QPointF, QMimeData, QByteArray
from PySide6.QtGui import QColor, QFont, QPixmap, QTransform, QImage, QKeySequence
from john_engine import InfiniteCanvas, Tool, Anchor

class HotkeyManager:
    def __init__(self, toml_path="hotkeys.toml"):
        self.toml_path = toml_path
        self.hotkeys = []
        self.current_chain = ""
        self.load_hotkeys()

    def load_hotkeys(self):
        try:
            with open(self.toml_path, "rb") as f:
                data = tomllib.load(f)
                raw_hotkeys = data.get("hotkeys", [])
                self.hotkeys = []
                for h in raw_hotkeys:
                    if "action" not in h:
                        continue
                    # Bulletproof normalization
                    norm_h = {
                        "action": h["action"],
                        "name": h.get("name", h["action"]),
                        "keys": h.get("keys", []),
                        "trigger": h.get("trigger", "press")
                    }
                    if not isinstance(norm_h["keys"], list):
                        norm_h["keys"] = [norm_h["keys"]]
                    self.hotkeys.append(norm_h)
        except Exception as e:
            print(f"Failed to load hotkeys: {e}")
            self.hotkeys = []

    def handle_key(self, key_name, modifiers):
        # 1. Build the key string for the current event
        current_key = ""
        mod_prefix = ""
        
        has_ctrl = bool(modifiers & Qt.ControlModifier)
        has_alt = bool(modifiers & Qt.AltModifier)
        has_shift = bool(modifiers & Qt.ShiftModifier)
        
        if has_ctrl: mod_prefix += "C-"
        if has_alt: mod_prefix += "A-"
        
        # Shift is handled carefully:
        # If it's a special key like Tab, Shift-Tab is <S-Tab>.
        # If it's a character like 's', Shift-s is 'S'.
        # If it's a modifier combo like <C-S-s>, then include it.
        if has_shift:
            if len(key_name) > 1 or (has_ctrl or has_alt):
                mod_prefix += "S-"

        # Construct the final <...> string if any modifiers or special key
        if mod_prefix or len(key_name) > 1:
            current_key = f"<{mod_prefix}{key_name}>"
        else:
            current_key = key_name

        # Special cases:
        if key_name in ["Ctrl", "Alt", "Shift", "Meta"]:
            return "WAIT_FOR_CHAIN", None

        if key_name == "Esc":
            self.current_chain = ""
            return "escape", "press"

        self.current_chain += current_key
        
        # 2. Match against hotkeys
        # Filter actions that have at least one key starting with the current chain
        matches = [h for h in self.hotkeys if any(k.startswith(self.current_chain) for k in h["keys"])]
        
        # Find if there is an exact match
        exact_match = next((h for h in matches if self.current_chain in h["keys"]), None)
        
        # Check if the current chain is also a prefix for a longer command
        is_partial = any(any(k.startswith(self.current_chain) and k != self.current_chain for k in h["keys"]) for h in matches)
        
        if exact_match and not is_partial:
            action = exact_match["action"]
            trigger = exact_match.get("trigger", "press")
            self.current_chain = ""
            return action, trigger
        elif not matches:
            # No possible matches left, clear it
            self.current_chain = ""
            return None, None
        
        return "WAIT_FOR_CHAIN", None

class HotkeyOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hide()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.bg = QLabel()
        self.bg.setStyleSheet("""
            background-color: rgba(20, 20, 20, 240); 
            color: white; 
            border-radius: 15px; 
            padding: 30px; 
            font-family: 'Monospace'; 
            font-size: 14px;
        """)
        layout.addWidget(self.bg)
        self.refresh_text()

    def refresh_text(self):
        try:
            with open("hotkeys.toml", "rb") as f:
                data = tomllib.load(f)
                hotkeys_data = data.get("hotkeys", [])
        except:
            hotkeys_data = []

        hotkeys_lines = ["--- HOTKEYS ---"]
        for h in hotkeys_data:
            if "action" not in h: continue
            keys = h.get("keys", [])
            if not keys: continue
            if isinstance(keys, str): keys = [keys]
            
            keys_str = ", ".join(keys)
            name = h.get("name", h["action"])
            hotkeys_lines.append(f"{keys_str.ljust(15)} - {name}")
            
        self.bg.setText("\n".join(hotkeys_lines))

    def resizeEvent(self, event): self.setGeometry(self.parent().rect())

class Toast(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: rgba(44, 62, 80, 240); color: white; border-radius: 20px; padding: 10px 25px; font-size: 13px; font-weight: bold;")
        self.adjustSize()
        self.hide()

    def show_message(self, message):
        self.setText(message)
        self.adjustSize()
        if self.parentWidget():
            x = (self.parentWidget().width() - self.width()) // 2
            y = self.parentWidget().height() - self.height() - 60
            self.move(x, y)
        self.show()
        QTimer.singleShot(1500, self.hide)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JohnDraw Settings")
        self.setMinimumSize(500, 450)
        self.settings = QSettings("JohnDrawInc", "JohnDrawPro")
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        
        # General
        general_tab = QWidget()
        g_layout = QVBoxLayout(general_tab)
        g_layout.addWidget(QLabel("Default Save Location:"))
        self.path_edit = QLineEdit(self.settings.value("default_path", os.path.expanduser("~")))
        g_layout.addWidget(self.path_edit)
        
        # Navigation
        nav_tab = QWidget()
        n_layout = QFormLayout(nav_tab)
        self.align_h = QComboBox()
        self.align_h.addItems(["Left", "Right"])
        self.align_h.setCurrentText(self.settings.value("newline_align_h", "Left"))
        self.x_input = QLineEdit(self.settings.value("newline_x", "15%"))
        self.align_v = QComboBox()
        self.align_v.addItems(["Top", "Bottom"])
        self.align_v.setCurrentText(self.settings.value("newline_align_v", "Top"))
        self.y_input = QLineEdit(self.settings.value("newline_y", "20%"))
        n_layout.addRow("H-Align (Screen Wall):", self.align_h)
        n_layout.addRow("X Offset from Wall (% or px):", self.x_input)
        n_layout.addRow("V-Align (Screen Wall):", self.align_v)
        n_layout.addRow("Y Offset from Wall (% or px):", self.y_input)
        
        # Blacklist
        bl_tab = QWidget()
        bl_layout = QVBoxLayout(bl_tab)
        self.bl_list = QListWidget()
        saved_bl = self.settings.value("device_blacklist", "")
        if saved_bl: self.bl_list.addItems(saved_bl.split(","))
        bl_layout.addWidget(self.bl_list)
        
        tabs.addTab(general_tab, "General")
        tabs.addTab(nav_tab, "Navigation")
        tabs.addTab(bl_tab, "Blacklist")
        layout.addWidget(tabs)
        btn_save = QPushButton("Save Settings")
        btn_save.clicked.connect(self.save_settings)
        layout.addWidget(btn_save)

    def save_settings(self):
        self.settings.setValue("default_path", self.path_edit.text())
        self.settings.setValue("newline_align_h", self.align_h.currentText())
        self.settings.setValue("newline_x", self.x_input.text())
        self.settings.setValue("newline_align_v", self.align_v.currentText())
        self.settings.setValue("newline_y", self.y_input.text())
        self.accept()
        if self.parent(): self.parent().apply_configs()

class CommandPalette(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()
        
        # UI components
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.container = QWidget()
        self.container.setStyleSheet("""
            background-color: rgba(25, 25, 25, 240);
            border: 1px solid #444;
            border-radius: 10px;
        """)
        self.container_layout = QVBoxLayout(self.container)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search commands...")
        self.search_input.setStyleSheet("""
            background-color: #333;
            color: white;
            border: 1px solid #555;
            border-radius: 5px;
            padding: 10px;
            font-size: 14px;
        """)
        self.search_input.textChanged.connect(self.filter_commands)
        self.search_input.installEventFilter(self)
        self.container_layout.addWidget(self.search_input)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                color: #ccc;
                font-size: 13px;
                font-family: 'Monospace';
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
                border-radius: 4px;
            }
        """)
        self.container_layout.addWidget(self.list_widget)
        
        self.layout.addWidget(self.container)
        
        self.commands = [] # List of {'id': '...', 'name': '...', 'keys': '...'}
        self.on_select = None

    def show_palette(self, commands, callback):
        self.commands = commands
        self.on_select = callback
        self.search_input.clear()
        self.populate_list(self.commands)
        
        # Center the palette relative to parent
        if self.parent():
            p = self.parent()
            w, h = 550, 450
            # Get parent's global geometry
            pg = p.geometry()
            self.setGeometry(pg.x() + (pg.width() - w)//2, pg.y() + (pg.height() - h)//2, w, h)
            
        self.show()
        self.search_input.setFocus()

    def populate_list(self, items):
        self.list_widget.clear()
        for cmd in items:
            item = QListWidgetItem()
            keys_str = ", ".join(cmd.get('keys', []))
            display_text = f"{cmd['name']:<40} {keys_str:>10}"
            item.setText(display_text)
            item.setData(Qt.UserRole, cmd['action'])
            self.list_widget.addItem(item)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def filter_commands(self, text):
        filtered = [c for c in self.commands if text.lower() in c['name'].lower() or text.lower() in c['action'].lower()]
        self.populate_list(filtered)

    def eventFilter(self, source, event):
        if source is self.search_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                self.hide()
                return True
            elif event.key() in [Qt.Key_Return, Qt.Key_Enter]:
                current = self.list_widget.currentItem()
                if current:
                    action_id = current.data(Qt.UserRole)
                    if self.on_select:
                        self.on_select(action_id)
                    self.hide()
                return True
            elif event.key() == Qt.Key_Up:
                self.list_widget.setCurrentRow(max(0, self.list_widget.currentRow() - 1))
                return True
            elif event.key() == Qt.Key_Down:
                self.list_widget.setCurrentRow(min(self.list_widget.count() - 1, self.list_widget.currentRow() + 1))
                return True
        return super().eventFilter(source, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        elif event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            current = self.list_widget.currentItem()
            if current:
                action_id = current.data(Qt.UserRole)
                if self.on_select:
                    self.on_select(action_id)
                self.hide()
        elif event.key() == Qt.Key_Up:
            self.list_widget.setCurrentRow(max(0, self.list_widget.currentRow() - 1))
        elif event.key() == Qt.Key_Down:
            self.list_widget.setCurrentRow(min(self.list_widget.count() - 1, self.list_widget.currentRow() + 1))
        else:
            super().keyPressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JohnDraw Pro")
        self.resize(1200, 900)
        self.settings = QSettings("JohnDrawInc", "JohnDrawPro")
        self.current_file = None
        self.canvas = InfiniteCanvas()
        self.setCentralWidget(self.canvas)
        self.apply_configs()
        self.tool_label = QLabel(" TOOL: PEN ", self.canvas)
        self.cmd_label = QLabel("", self.canvas)
        self.cmd_label.setStyleSheet("background-color: rgba(0, 0, 0, 150); color: #ccc; font-family: 'Monospace'; padding: 5px; border-top-left-radius: 8px;")
        self.update_tool_ui()
        self.toast = Toast("", self.canvas)
        self.hk_overlay = HotkeyOverlay(self.canvas)
        self.cmd_palette = CommandPalette(self)
        self.hotkey_manager = HotkeyManager()
        self.active_hold_keys = {}
        self.hk_overlay.refresh_text()
        self.canvas.installEventFilter(self)

    def apply_configs(self):
        bl = self.settings.value("device_blacklist", "")
        self.canvas.device_blacklist = [b.strip() for b in bl.split(",") if b.strip()]

    def eventFilter(self, source, event):
        if source is self.canvas:
            if event.type() == QEvent.Resize:
                self.tool_label.move(0, self.canvas.height() - self.tool_label.height())
                self.cmd_label.move(self.canvas.width() - self.cmd_label.width(), self.canvas.height() - self.cmd_label.height())
                self.hk_overlay.setGeometry(self.canvas.rect())
            elif event.type() == QEvent.KeyPress:
                self.keyPressEvent(event)
                return True
            elif event.type() == QEvent.KeyRelease:
                self.keyReleaseEvent(event)
                return True
        return super().eventFilter(source, event)

    def update_tool_ui(self):
        tool = self.canvas.current_tool
        anchor = self.canvas.current_anchor
        zoom = self.canvas.transform().m11()
        color_hex = self.canvas.pen_color.name().upper()
        
        is_shape = tool in [Tool.LINE, Tool.CIRCLE, Tool.RECTANGLE]
        anchor_str = f" [{anchor.name}]" if is_shape else ""
        self.tool_label.setText(f" {tool.value}{anchor_str} | {color_hex} | {zoom:.1f}x ")
        
        self.tool_label.setStyleSheet(f"background-color: #333; color: white; font-weight: bold; padding: 8px; border-top-right-radius: 10px;")
        self.tool_label.adjustSize()
        self.tool_label.move(0, self.canvas.height() - self.tool_label.height())
        self.cmd_label.adjustSize()
        self.cmd_label.move(self.canvas.width() - self.cmd_label.width(), self.canvas.height() - self.cmd_label.height())

    def _parse_val(self, val_str, total):
        if val_str.endswith('%'):
            try: return (float(val_str[:-1]) / 100.0) * total
            except: return 0
        try: return float(val_str)
        except: return 0

    def get_screen_anchor(self):
        w, h = self.width(), self.height()
        x_raw = self.settings.value("newline_x", "15%")
        y_raw = self.settings.value("newline_y", "20%")
        h_align = self.settings.value("newline_align_h", "Left")
        v_align = self.settings.value("newline_align_v", "Top")
        tx = self._parse_val(x_raw, w)
        if h_align == "Right": tx = w - tx
        ty = self._parse_val(y_raw, h)
        if v_align == "Bottom": ty = h - ty
        return tx, ty

    def align_camera(self, scene_x, scene_y):
        tx, ty = self.get_screen_anchor()
        self.canvas.centerOn(scene_x, scene_y)
        dx = tx - (self.canvas.viewport().width() / 2)
        dy = ty - (self.canvas.viewport().height() / 2)
        self.canvas.horizontalScrollBar().setValue(self.canvas.horizontalScrollBar().value() - dx)
        self.canvas.verticalScrollBar().setValue(self.canvas.verticalScrollBar().value() - dy)

    def go_home(self):
        self.align_camera(0, 0)

    def go_to_newline_point(self):
        items = self.canvas.scene.items()
        max_y = 0
        if items:
            valid_items = [it for it in items if not isinstance(it, QGraphicsPathItem) or it.path().elementCount() > 0]
            if valid_items:
                max_y = max(it.sceneBoundingRect().bottom() for it in valid_items if it != self.canvas.lasso_path_item)
        self.align_camera(0, max_y + 40)

    def copy_selection(self):
        selected = self.canvas.scene.selectedItems()
        if not selected:
            self.toast.show_message("Nothing selected to copy")
            return
            
        # 1. Internal JSON format
        data = self.canvas.serialize(items=selected)
        json_bytes = json.dumps(data).encode('utf-8')
        
        # 2. Bitmap format
        img = self.canvas.render_items_to_image(selected)
        
        mime = QMimeData()
        mime.setData("application/x-johndraw", QByteArray(json_bytes))
        mime.setImageData(img)
        
        QApplication.clipboard().setMimeData(mime)
        self.toast.show_message(f"Copied {len(selected)} items")

    def paste_clipboard(self):
        mime = QApplication.clipboard().mimeData()
        
        if mime.hasFormat("application/x-johndraw"):
            self.canvas.save_history()
            json_bytes = mime.data("application/x-johndraw").data()
            data = json.loads(json_bytes.decode('utf-8'))
            new_items = self.canvas.add_serialized_data(data)
            
            self.canvas.scene.clearSelection()
            for it in new_items: it.setSelected(True)
            self.toast.show_message(f"Pasted {len(new_items)} items")
            self.update_tool_ui()
            return

        img = QApplication.clipboard().image()
        if not img.isNull():
            self.canvas.save_history()
            pixmap = QPixmap.fromImage(img)
            item = QGraphicsPixmapItem(pixmap)
            item.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
            
            view_center = self.canvas.viewport().rect().center()
            scene_center = self.canvas.mapToScene(view_center)
            item.setPos(scene_center.x() - pixmap.width()/2, scene_center.y() - pixmap.height()/2)
            
            self.canvas.scene.addItem(item)
            self.canvas.scene.clearSelection()
            item.setSelected(True)
            self.toast.show_message("Pasted Bitmap")
            self.update_tool_ui()
        else:
            self.toast.show_message("Clipboard is empty or incompatible")

    def open_file(self):
        d = self.settings.value("default_path", os.path.expanduser("~"))
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Note", d, "JohnDraw Files (*.json)")
        if file_path:
            self.canvas.save_history()
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                self.canvas.deserialize(data)
                self.current_file = file_path
                self.toast.show_message(f"opened {os.path.basename(file_path)}")
                self.update_tool_ui()
            except Exception as e:
                self.toast.show_message(f"Open failed: {e}")

    def new_file(self):
        self.canvas.save_history()
        self.canvas.reset_canvas()
        self.current_file = None
        self.toast.show_message("New Canvas Created")
        self.update_tool_ui()

    def get_all_actions(self):
        # We can combine actions from the HotkeyManager and others that don't have hotkeys.
        # For now, let's just make sure all actions in _execute_action are representable.
        actions = []
        for h in self.hotkey_manager.hotkeys:
            actions.append(h)
        return actions

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        
        ctrl = event.modifiers() & Qt.ControlModifier
        
        # Color palette handling (independent of hotkeys for now)
        palette = {
            Qt.Key_1: "#000000", Qt.Key_2: "#e74c3c", Qt.Key_3: "#e67e22", 
            Qt.Key_4: "#f1c40f", Qt.Key_5: "#2ecc71", Qt.Key_6: "#3498db", 
            Qt.Key_7: "#3f51b5", Qt.Key_8: "#8e44ad"
        }
        if event.key() in palette and not ctrl:
            self.canvas.pen_color = QColor(palette[event.key()])
            self.update_tool_ui()
            self.toast.show_message(f"Color Set")
            return

        # Handle other keys via HotkeyManager
        key_name = self._get_key_name(event)
        modifiers = event.modifiers()
        
        action, trigger = self.hotkey_manager.handle_key(key_name, modifiers)
        self.cmd_label.setText(self.hotkey_manager.current_chain)
        self.cmd_label.adjustSize()
        self.cmd_label.move(self.canvas.width() - self.cmd_label.width(), self.canvas.height() - self.cmd_label.height())
        
        if action and action != "WAIT_FOR_CHAIN":
            if trigger == "hold":
                self.active_hold_keys[event.key()] = action
                self._execute_action(action, use_stack=True)
            else:
                # Normal press: clear holds and stack
                self.active_hold_keys.clear()
                self.canvas.tool_stack.clear()
                self._execute_action(action)
            self.cmd_label.setText("")

    def _get_key_name(self, event):
        key = event.key()
        # Map some common keys to names used in TOML
        names = {
            Qt.Key_Escape: "Esc",
            Qt.Key_Delete: "Del",
            Qt.Key_Tab: "Tab",
            Qt.Key_Backspace: "BS",
            Qt.Key_Return: "CR",
            Qt.Key_Enter: "CR",
            Qt.Key_Space: "Space",
            Qt.Key_Up: "Up",
            Qt.Key_Down: "Down",
            Qt.Key_Left: "Left",
            Qt.Key_Right: "Right",
            Qt.Key_Home: "Home",
            Qt.Key_End: "End",
            Qt.Key_PageUp: "PgUp",
            Qt.Key_PageDown: "PgDn",
            Qt.Key_Insert: "Ins",
        }
        
        if key in names:
            return names[key]
        
        # If it's a character key, use its text representation if no Ctrl/Alt
        text = event.text()
        if text and text.isprintable() and len(text) == 1:
            if not (event.modifiers() & (Qt.ControlModifier | Qt.AltModifier)):
                return text
            
        # For other keys or when modifiers are held, use QKeySequence to get a name
        s = QKeySequence(key).toString()
        if len(s) == 1:
            return s.lower()
        return s

    def _execute_action(self, action, use_stack=False):
        NAV_STEP = 50
        
        def _set_tool(tool):
            if use_stack:
                self.canvas.push_tool(tool)
            else:
                self.canvas.current_tool = tool
            self.update_tool_ui()

        def _set_anchor(anchor):
            self.canvas.current_anchor = anchor
            self.update_tool_ui()
            self.toast.show_message(f"Anchor: {anchor.name}")

        if action == "set_tool_pen":
            _set_tool(Tool.PEN)
        elif action == "set_tool_eraser":
            _set_tool(Tool.ERASER)
        elif action == "set_tool_lasso":
            _set_tool(Tool.LASSO)
        elif action == "set_tool_move":
            _set_tool(Tool.MOVE)
        elif action == "set_tool_resize":
            _set_tool(Tool.RESIZE)
        elif action == "set_tool_line":
            _set_tool(Tool.LINE)
        elif action == "set_tool_circle":
            _set_tool(Tool.CIRCLE)
        elif action == "set_tool_rectangle":
            _set_tool(Tool.RECTANGLE)
        elif action == "set_tool_travel":
            _set_tool(Tool.TRAVEL)
        elif action == "set_anchor_center":
            _set_anchor(Anchor.CENTER)
        elif action == "set_anchor_vertex":
            _set_anchor(Anchor.VERTEX)
        elif action == "set_anchor_edge":
            _set_anchor(Anchor.EDGE)
        elif action == "go_home":
            self.go_home()
        elif action == "go_to_newline":
            self.go_to_newline_point()
        elif action == "pan_left":
            self.canvas.horizontalScrollBar().setValue(self.canvas.horizontalScrollBar().value() - NAV_STEP)
        elif action == "pan_right":
            self.canvas.horizontalScrollBar().setValue(self.canvas.horizontalScrollBar().value() + NAV_STEP)
        elif action == "pan_up":
            self.canvas.verticalScrollBar().setValue(self.canvas.verticalScrollBar().value() - NAV_STEP)
        elif action == "pan_down":
            self.canvas.verticalScrollBar().setValue(self.canvas.verticalScrollBar().value() + NAV_STEP)
        elif action == "zoom_in":
            self.canvas.scale(1.2, 1.2)
            self.update_tool_ui()
        elif action == "zoom_out":
            self.canvas.scale(1/1.2, 1/1.2)
            self.update_tool_ui()
        elif action == "zoom_reset":
            self.canvas.setTransform(QTransform())
            self.update_tool_ui()
        elif action == "undo":
            self.canvas.undo()
            self.update_tool_ui()
        elif action == "redo":
            self.canvas.redo()
            self.update_tool_ui()
        elif action == "delete_selected":
            selected = self.canvas.scene.selectedItems()
            if selected:
                self.canvas.save_history()
                for item in selected:
                    if item != self.canvas.lasso_path_item:
                        self.canvas.scene.removeItem(item)
                self.toast.show_message(f"Deleted {len(selected)} items")
        elif action == "escape":
            self.hotkey_manager.current_chain = ""
            self.cmd_label.setText("")
            if self.hk_overlay.isVisible(): self.hk_overlay.hide()
            else:
                self.canvas.current_tool = Tool.PEN
                self.canvas.scene.clearSelection()
                self.update_tool_ui()
        elif action == "save_file":
            is_init = self.current_file is None
            if not self.current_file:
                d = self.settings.value("default_path", os.path.expanduser("~"))
                f = f"note_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json"
                self.current_file = os.path.join(d, f)
            try:
                with open(self.current_file, 'w') as f: json.dump(self.canvas.serialize(), f)
                self.toast.show_message(f"save {os.path.basename(self.current_file)}" if is_init else "saved")
            except Exception as e: self.toast.show_message(f"Save failed: {e}")
        elif action == "new_file":
            self.new_file()
        elif action == "open_file":
            self.open_file()
        elif action == "copy_selection":
            self.copy_selection()
        elif action == "paste_clipboard":
            self.paste_clipboard()
        elif action == "show_help":
            self.hk_overlay.show()
        elif action == "show_command_palette":
            # Pass all hotkeys to the palette
            self.cmd_palette.show_palette(self.get_all_actions(), self._execute_action)
        elif action == "open_settings":
            SettingsDialog(self).exec()

    def keyReleaseEvent(self, event):
        if event.key() in self.active_hold_keys and not event.isAutoRepeat():
            self.canvas.pop_tool()
            del self.active_hold_keys[event.key()]
            self.update_tool_ui()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
