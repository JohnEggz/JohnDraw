import sys
import os

# Ensure project root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# DEBUG: Check where PyQt6 is coming from
try:
    import PyQt6
    print(f"DEBUG: PyQt6 loaded from: {PyQt6.__file__}")
except ImportError:
    print("CRITICAL: PyQt6 not found in main.py environment!")

from PyQt6.QtWidgets import QApplication
from app.gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
