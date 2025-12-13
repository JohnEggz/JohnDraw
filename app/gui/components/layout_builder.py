import json
import os
import sys
import importlib
import importlib.util
from functools import partial
from PyQt6.QtWidgets import QWidget, QLayout, QLabel
from PyQt6.QtCore import Qt

# Import parser
from app.core.command_parser import parse_command

# Optional TOML support
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

class LayoutBuilder:
    # --- UPDATED INIT: Add state_store ---
    def __init__(self, workspace_name, base_dir, plugin_dir, state_store, command_handler=None):
        self.workspace_name = workspace_name
        self.base_dir = base_dir
        self.plugin_dir = plugin_dir
        self.state_store = state_store  # <--- Store reference
        self.command_handler = command_handler
        self.objects = {} 
        self.schema = {}
        self.required_paths = [] 

    def build(self) -> QWidget:
        self._load_and_merge_schema()
        if not self.schema:
            return self._create_main_container()

        root_key = self.schema.get("root")
        if not root_key:
            raise ValueError("Config exists but missing 'root' key.")
        
        built = self._build_element(root_key)
        
        container = self._create_main_container()
        if isinstance(built, QLayout):
            container.setLayout(built)
        elif isinstance(built, QWidget):
            built.setParent(container)
        
        container.setStyleSheet(self._load_and_merge_css())
        return container

    def _create_main_container(self):
        c = QWidget()
        c.setObjectName("MainContainer")
        return c

    def _resolve_type(self, type_name):
        clean_name = type_name.strip().strip("'").strip('"')
        try:
            qt_mod = importlib.import_module("PyQt6.QtWidgets")
            if hasattr(qt_mod, clean_name):
                return getattr(qt_mod, clean_name)
        except ImportError as e:
            print(f"CRITICAL: Could not import PyQt6.QtWidgets: {e}")
        return self._load_plugin(clean_name)

    def _load_plugin(self, widget_type):
        paths_to_try = [
            os.path.join(self.plugin_dir, f"{widget_type}.py"),
            os.path.join(self.plugin_dir, f"{widget_type.lower()}.py") 
        ]
        for p in paths_to_try:
            if os.path.exists(p):
                try:
                    spec = importlib.util.spec_from_file_location(widget_type, p)
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[widget_type] = mod
                    spec.loader.exec_module(mod)
                    if hasattr(mod, "main"):
                        return mod.main()
                except Exception as e:
                    print(f"Plugin Load Error ({p}): {e}")
        return None

    def _build_element(self, key):
        if key not in self.schema:
            lbl = QLabel(f"MISSING: {key}")
            lbl.setStyleSheet("background: red; color: white;")
            return lbl

        data = self.schema[key]
        raw_type = data.get("type", "QWidget")
        cls_or_instance = self._resolve_type(raw_type)

        if cls_or_instance is None:
            print(f"DEBUG FAILURE: Could not resolve type '{raw_type}' for key '{key}'")
            return QLabel(f"UNKNOWN TYPE: {raw_type}")

        if isinstance(cls_or_instance, type):
            instance = cls_or_instance()
        else:
            instance = cls_or_instance

        if hasattr(instance, "set_state_store"):
            instance.set_state_store(self.state_store)

        if isinstance(instance, QWidget):
            instance.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.objects[key] = instance
        
        reserved = {"type", "children", "require"}
        for prop, val in data.items():
            if prop in reserved: continue
            
            if prop.startswith("on_"):
                self._connect_signal(instance, prop, val)
            elif prop in ["id", "objectName"]:
                instance.setObjectName(val)
            else:
                self._set_property(instance, prop, val)

        for child in data.get("children", []):
            child_obj = self._build_element(child)
            self._attach_child(instance, child_obj)

        return instance

    def _set_property(self, instance, prop, val):
        setter_name = f"set{prop[0].upper()}{prop[1:]}"
        setter = getattr(instance, setter_name, None)
        
        if not setter:
            return

        # --- FEATURE: State Binding ---
        if isinstance(val, str) and val.startswith("$"):
            var_key = val[1:] 
            
            def update_widget(new_value):
                # FIX: Try raw value first (Essential for Lists/Dicts)
                try:
                    setter(new_value)
                except TypeError:
                    # Fallback: Convert to string (Useful for QLabels expecting text)
                    setter(str(new_value))

            # Subscribe to the store
            self.state_store.subscribe(var_key, update_widget)
            
        else:
            setter(val)

    def _attach_child(self, parent, child):
        if isinstance(parent, QLayout):
            if isinstance(child, QWidget): parent.addWidget(child)
            elif isinstance(child, QLayout): parent.addLayout(child)
        elif isinstance(parent, QWidget):
            if isinstance(child, QLayout): parent.setLayout(child)
            elif isinstance(child, QWidget): child.setParent(parent)

    def _connect_signal(self, instance, event, cmd):
        base = event[3:]
        candidates = [base + "ed", base, base + "d"]
        for name in candidates:
            if hasattr(instance, name):
                sig = getattr(instance, name)
                if hasattr(sig, 'connect'):
                    try:
                        sig.connect(partial(self._dispatch_command, cmd))
                        return
                    except: pass
        print(f"Warning: Signal {event} not found on {type(instance)}")

    def _dispatch_command(self, cmd_str):
        if self.command_handler:
            obj = parse_command(cmd_str)
            if obj: self.command_handler(obj)

    def _load_and_merge_schema(self):
        def_path = os.path.join(self.base_dir, "defaults", "default")
        self.schema.update(self._load_file(def_path))
        ws_path = os.path.join(self.base_dir, self.workspace_name)
        ws_data = self._load_file(ws_path)
        self.schema.update(ws_data)
        reqs = ws_data.get("require", [])
        if isinstance(reqs, str): reqs = [reqs]
        for r in reqs:
            self.schema.update(self._load_file(os.path.join(self.base_dir, r)))
            self.required_paths.append(r)

    def _load_file(self, base_path):
        data = {}
        if os.path.exists(base_path + ".json"):
            with open(base_path + ".json", 'rb') as f: data.update(json.load(f))
        if tomllib and os.path.exists(base_path + ".toml"):
            with open(base_path + ".toml", 'rb') as f: data.update(tomllib.load(f))
        return data

    def _load_and_merge_css(self):
        parts = []
        for p in [os.path.join(self.base_dir, "defaults", "default.css"),
                  os.path.join(self.base_dir, f"{self.workspace_name}.css")]:
            if os.path.exists(p):
                with open(p, 'r') as f: parts.append(f.read())
        return "\n".join(parts)
