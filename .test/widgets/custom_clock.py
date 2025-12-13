from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer, QTime, Qt

def main():
    # Create a container widget to hold our logic
    container = QWidget()
    layout = QVBoxLayout(container)
    
    # Create label
    label = QLabel()
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("font-size: 20px; font-weight: bold; color: blue;")
    
    layout.addWidget(label)
    
    # Setup Timer logic
    def update_time():
        label.setText(QTime.currentTime().toString("HH:mm:ss"))

    timer = QTimer(container)
    timer.timeout.connect(update_time)
    timer.start(1000)
    
    update_time() # Initial set
    
    return container
