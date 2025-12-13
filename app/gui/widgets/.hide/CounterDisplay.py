from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import Qt
from app.core.api_interface import CommandableWidget
from typing import Optional

class CounterDisplay(QLabel, CommandableWidget):
    """
    A simple numeric display that accepts API commands.
    """
    def __init__(self, text: str = "0", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.count = 0
        
        # Default styling
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("font-size: 40px; font-weight: bold; color: white;")
        
        # Sync internal state with text
        try:
            self.count = int(text)
        except ValueError:
            self.count = 0

    # --- Builder Setters ---
    
    def setValue(self, value: int):
        """Builder setter for initial value."""
        self.count = int(value)
        self.setText(str(self.count))

    # --- API Endpoints ---
    # These are callable via: router.process(Command("my_display", ["increment"]))

    def api_increment(self, amount=1):
        """Increments the counter. Can accept a custom amount."""
        self.count += int(amount)
        self.setText(str(self.count))
        self._animate_update() # Optional visual feedback

    def api_decrement(self, amount=1):
        """Decrements the counter."""
        self.count -= int(amount)
        self.setText(str(self.count))

    def api_reset(self):
        """Resets counter to zero."""
        self.count = 0
        self.setText("0")

    def _animate_update(self):
        # Placeholder for visual flash effect
        pass

def main() -> QWidget:
    return CounterDisplay()
