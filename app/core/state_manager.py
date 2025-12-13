class StateStore:
    def __init__(self):
        self._data = {}
        self._listeners = {} # { "variable_name": [callback_function, ...] }

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        """
        Updates the state and notifies all listeners.
        """
        self._data[key] = value
        
        # Notify listeners
        if key in self._listeners:
            for callback in self._listeners[key]:
                try:
                    callback(value)
                except Exception as e:
                    print(f"State Update Error ({key}): {e}")

    def subscribe(self, key, callback):
        """
        Registers a callback function to be called when 'key' changes.
        """
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)
        
        # If value exists, trigger immediately so widget has initial state
        if key in self._data:
            callback(self._data[key])
