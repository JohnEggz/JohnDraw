import json
import os
import importlib.util
import sys
from functools import partial
from PyQt6.QtWidgets import QWidget, QLayout
from PyQt6.QtCore import Qt
from PyQt6 import QtWidgets

# Import the CLI parser logic
from test.command_parser import parse_command

# Try importing TOML parser
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

class JsonUiBuilder:
    def __init__(self, workspace_name, base_dir="test/workspaces", plugin_dir="test/widgets", command_handler=None):
        """
        :param command_handler: A callable that accepts a Command object (from command_parser.py)
        """
        self.workspace_name = workspace_name
        self.base_dir = base_dir
        self.plugin_dir = plugin_dir
        self.command_handler = command_handler
        self.objects = {} 
        self.schema = {}
        self.required_paths = [] 

    def build(self) -> QWidget:
        # 1. Resolve and Load all Schemas
        self._load_and_merge_schema()
        
        if not self.schema:
            print("Warning: No configuration found. Returning empty container.")
            return self._create_container()

        root_key = self.schema.get("root")
        if not root_key:
            raise ValueError("Merged config exists but is missing a 'root' key.")
        
        # 2. Build Widget Hierarchy
        built_structure = self._build_element(root_key)

        # 3. Create Container
        container = self._create_container()
        
        if isinstance(built_structure, QLayout):
            container.setLayout(built_structure)
        elif isinstance(built_structure, QWidget):
            built_structure.setParent(container)
        
        # 4. Load and Apply CSS
        container.setStyleSheet(self._load_and_merge_css())
        
        return container

    def _create_container(self):
        c = QWidget()
        c.setObjectName("MainContainer")
        return c

    # --- Signal & Command Handling ---
    
    def _dispatch_command(self, command_str):
        """
        Slot triggered by Qt signals. 
        Parses the CLI string and delegates to the command_handler.
        """
        if not self.command_handler:
            return

        cmd_obj = parse_command(command_str)
        if cmd_obj:
            self.command_handler(cmd_obj)

    def _connect_signal(self, instance, event_name, command_str):
        """
        Connects a JSON event (e.g. 'on_click') to a PyQt signal.
        """
        # Remove 'on_' prefix (e.g. 'click')
        base_name = event_name[3:] 

        # We look for candidates in this specific order:
        # 1. Past tense (click -> clicked) - Most common for actions
        # 2. Exact name (textChanged) - Common for state changes
        # 3. 'd' suffix (change -> changed) - Edge cases
        candidate_names = [base_name + "ed", base_name, base_name + "d"]

        signal_obj = None
        
        for name in candidate_names:
            if hasattr(instance, name):
                attr = getattr(instance, name)
                if hasattr(attr, 'connect') and callable(attr.connect):
                    signal_obj = attr
                    break
        
        if signal_obj:
            # We use functools.partial to bake the specific command string 
            # into the callback function for this specific signal.
            callback = partial(self._dispatch_command, command_str)
            try:
                signal_obj.connect(callback)
            except Exception as e:
                print(f"Failed to connect {event_name} on {instance}: {e}")
        else:
            print(f"Warning: No valid signal found for '{event_name}' on {type(instance).__name__}")

    # --- Loading Logic ---

    def _load_plugin(self, widget_type):
        """
        Attempts to load a python plugin from widgets/{widget_type}.py
        Expects the file to have a 'main()' function returning a QWidget.
        """
        plugin_path = os.path.join(self.plugin_dir, f"{widget_type}.py")
        
        if not os.path.exists(plugin_path):
            return None

        try:
            # Dynamic import magic
            spec = importlib.util.spec_from_file_location(widget_type, plugin_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[widget_type] = module
                spec.loader.exec_module(module)
                
                if hasattr(module, "main"):
                    instance = module.main()
                    if not isinstance(instance, (QWidget, QLayout)):
                        print(f"Warning: Plugin {widget_type}.main() did not return a QWidget/QLayout.")
                    return instance
                else:
                    print(f"Error: Plugin {plugin_path} missing 'def main()' function.")
        except Exception as e:
            print(f"Error loading plugin {widget_type}: {e}")
            
        return None

    def _load_file_raw(self, full_path):
        if not os.path.exists(full_path):
            return {}
        try:
            with open(full_path, 'rb') as f:
                content = f.read()
                if not content: return {}
                if full_path.endswith('.json'): return json.loads(content)
                elif full_path.endswith('.toml') and tomllib: return tomllib.load(open(full_path, "rb"))
        except Exception as e:
            print(f"Warning: Failed to parse {full_path}: {e}")
        return {}

    def _load_layer(self, name_or_path):
        if os.path.splitext(name_or_path)[1] in ['.json', '.toml']:
            full_path = name_or_path if os.path.isabs(name_or_path) else os.path.join(self.base_dir, name_or_path)
            return self._load_file_raw(full_path)

        data = {}
        data.update(self._load_file_raw(os.path.join(self.base_dir, f"{name_or_path}.json")))
        toml_data = self._load_file_raw(os.path.join(self.base_dir, f"{name_or_path}.toml"))
        if toml_data: data.update(toml_data)
        return data

    def _load_and_merge_schema(self):
        default_config = self._load_layer("default")
        workspace_config = self._load_layer(self.workspace_name)
        requires = workspace_config.get("require") or default_config.get("require") or []
        if isinstance(requires, str): requires = [requires]
        self.required_paths = requires

        self.schema = {}
        self.schema.update(default_config)
        for req_path in self.required_paths:
            self.schema.update(self._load_layer(req_path))
        self.schema.update(workspace_config)

    def _load_and_merge_css(self) -> str:
        css_parts = []
        def load_css(path):
            if os.path.exists(path):
                with open(path, 'r') as f:
                    c = f.read().strip()
                    if c: css_parts.append(c)

        load_css(os.path.join(self.base_dir, "default.css"))
        for req_path in self.required_paths:
            if os.path.isabs(req_path):
                base = os.path.splitext(req_path)[0]
                load_css(f"{base}.css")
            else:
                base = os.path.splitext(req_path)[0]
                load_css(os.path.join(self.base_dir, f"{base}.css"))
        load_css(os.path.join(self.base_dir, f"{self.workspace_name}.css"))
        return "\n".join(css_parts)

    def _build_element(self, key):
        if key not in self.schema:
            raise KeyError(f"Key '{key}' is referenced but not defined.")

        data = self.schema[key]
        widget_type = data.get("type")
        if not widget_type:
             raise ValueError(f"Element '{key}' missing 'type' definition.")
        
        instance = None

        # 1. Try Standard Qt Widget
        if hasattr(QtWidgets, widget_type):
            instance = getattr(QtWidgets, widget_type)()
        
        # 2. Try Custom Python Plugin
        if instance is None:
            instance = self._load_plugin(widget_type)

        # 3. Fail if neither found
        if instance is None:
            raise TypeError(f"Unknown widget type: '{widget_type}'. Checked QtWidgets and {self.plugin_dir}/")
        
        # Auto-enable styling for raw Widgets
        if type(instance) == QWidget:
            instance.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.objects[key] = instance

        # Apply Properties
        reserved_keys = {"type", "children", "require"} 
        for prop, value in data.items():
            if prop in reserved_keys: continue
            
            # --- FEATURE ADDED: Event Handler Detection ---
            if prop.startswith("on_"):
                self._connect_signal(instance, prop, value)
                continue
            # ----------------------------------------------

            if prop in ["id", "objectName"]:
                instance.setObjectName(value)
                continue
            self._set_property(instance, prop, value)

        # Build Children
        children = data.get("children", [])
        for child_key in children:
            child_instance = self._build_element(child_key)
            self._attach_child(instance, child_instance)

        return instance

    def _set_property(self, instance, prop_name, value):
        setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
        if hasattr(instance, setter_name):
            getattr(instance, setter_name)(value)

    def _attach_child(self, parent, child):
        if isinstance(parent, QLayout):
            if isinstance(child, QWidget): parent.addWidget(child)
            elif isinstance(child, QLayout): parent.addLayout(child)
        elif isinstance(parent, QWidget):
            if isinstance(child, QLayout): parent.setLayout(child)
            elif isinstance(child, QWidget): child.setParent(parent)
