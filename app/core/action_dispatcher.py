class ActionDispatcher:
    def __init__(self, state_store):
        self.state_store = state_store

    def dispatch(self, cmd_obj):
        """
        Automatically routes 'command_name' to 'handle_command_name'.
        Example: 'state set ...' -> handle_state(cmd_obj)
        """
        method_name = f"handle_{cmd_obj.name}"
        
        if hasattr(self, method_name):
            handler = getattr(self, method_name)
            try:
                handler(cmd_obj)
            except Exception as e:
                print(f"❌ Error executing '{cmd_obj.name}': {e}")
        else:
            print(f"⚠️ Unknown Command: '{cmd_obj.name}' (No {method_name} found)")

    # --- COMMAND HANDLERS ---

    def handle_state(self, cmd):
        """
        Handles: state set --key=x --val=y
        Handles: state math --key=x --op=add --val=1
        """
        if "set" in cmd.args:
            key = cmd.kwargs.get("key")
            val = cmd.kwargs.get("value")
            if key: 
                print(f"   -> State SET: {key} = {val}")
                self.state_store.set(key, val)

        elif "math" in cmd.args:
            key = cmd.kwargs.get("key")
            op = cmd.kwargs.get("op")
            val = float(cmd.kwargs.get("val", 1))
            
            if key:
                current = float(self.state_store.get(key, 0))
                new_val = current
                
                if op == "add": new_val += val
                elif op == "sub": new_val -= val
                
                if new_val.is_integer(): new_val = int(new_val)
                self.state_store.set(key, new_val)

    def handle_canvas(self, cmd):
        """
        Example: canvas move --x=10 --y=20
        """
        # This is where you'd hook into your actual Canvas widget logic.
        # For now, we just update state to show it works.
        action = cmd.args[0] if cmd.args else "unknown"
        self.state_store.set("status", f"Canvas {action}: {cmd.kwargs}")

    def handle_app(self, cmd):
        """
        Example: app exit, app minimize
        """
        if "exit" in cmd.args:
            print("Requesting App Exit...")
            # sys.exit() or similar
