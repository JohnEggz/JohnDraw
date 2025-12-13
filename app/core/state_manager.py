class StateStore:
    def __init__(self):
        self._data = {}
        self._listeners = {} # { "variable_name": [callback_function, ...] }

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        """
        Updates the state and notifies all listeners.
        Removes dead listeners (deleted widgets) automatically.
        """
        self._data[key] = value
        
        if key in self._listeners:
            # We create a new list for surviving listeners
            active_listeners = []
            
            for callback in self._listeners[key]:
                try:
                    callback(value)
                    # If it didn't crash, it's still alive. Keep it.
                    active_listeners.append(callback)
                except RuntimeError as e:
                    # Check for standard PyQt "object deleted" error
                    if "wrapped C/C++ object" in str(e) or "has been deleted" in str(e):
                        # It's a zombie widget. Let it die (don't add to active_listeners).
                        pass
                    else:
                        # Some other real logic error, print it
                        print(f"State Update Error ({key}): {e}")
                except Exception as e:
                    print(f"State Update Error ({key}): {e}")

            # Replace the old list with the cleaned list
            self._listeners[key] = active_listeners

    def subscribe(self, key, callback):
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)
        
        if key in self._data:
            try:
                callback(self._data[key])
            except RuntimeError:
                pass

    def clear_listeners(self):
        """
        Called when switching workspaces to dump all old connections.
        """
        self._listeners = {}
