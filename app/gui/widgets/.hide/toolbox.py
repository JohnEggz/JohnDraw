from PyQt6.QtWidgets import QWidget, QHBoxLayout
from PyQt6.QtCore import pyqtSignal
from .flick_widget import FlickButton, FlickAction

class Toolbox(QWidget):
    # Signals to notify the Main Window
    toolChanged = pyqtSignal(str)       # "Pen", "Line", "Eraser"
    colorChanged = pyqtSignal(str)      # "Black", "Blue", "Green", etc.
    newFrameRequested = pyqtSignal(str) # "None", "<=>", "=", "->", "=>"
    moveRequested = pyqtSignal(str)     # "left", "right", "up", "down"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # --- BUTTON 1: DRAWING TOOLS ---
        self.btn_draw = FlickButton("Drawing\n(Pen)")
        self.btn_draw.set_feedback_text(FlickAction.CLICK, "Tool:\nPen")
        self.btn_draw.set_feedback_text(FlickAction.LEFT, "Tool:\nLine")
        self.btn_draw.set_feedback_text(FlickAction.RIGHT, "Tool:\nEraser")
        # Unused directions
        self.btn_draw.set_feedback_text(FlickAction.UP, "---")
        self.btn_draw.set_feedback_text(FlickAction.DOWN, "---")
        
        self.btn_draw.actionTriggered.connect(self._handle_draw)
        layout.addWidget(self.btn_draw)

        # --- BUTTON 2: COLORS ---
        self.btn_color = FlickButton("Color\n(Black)")
        self.btn_color.set_feedback_text(FlickAction.CLICK, "Black")
        self.btn_color.set_feedback_text(FlickAction.LEFT, "Blue")
        self.btn_color.set_feedback_text(FlickAction.RIGHT, "Red")
        self.btn_color.set_feedback_text(FlickAction.UP, "Yellow")
        self.btn_color.set_feedback_text(FlickAction.DOWN, "Green")
        
        self.btn_color.actionTriggered.connect(self._handle_color)
        layout.addWidget(self.btn_color)

        # --- BUTTON 3: FRAMES ---
        self.btn_frame = FlickButton("New Frame")
        self.btn_frame.set_feedback_text(FlickAction.CLICK, "New Frame\n(No Relation)")
        self.btn_frame.set_feedback_text(FlickAction.LEFT, "Relation\n<=>")
        self.btn_frame.set_feedback_text(FlickAction.RIGHT, "Relation\n=>")
        self.btn_frame.set_feedback_text(FlickAction.UP, "Relation\n->")
        self.btn_frame.set_feedback_text(FlickAction.DOWN, "Relation\n=")
        
        self.btn_frame.actionTriggered.connect(self._handle_frame)
        layout.addWidget(self.btn_frame)

        # --- BUTTON 4: MOVEMENT ---
        self.btn_move = FlickButton("Move")
        self.btn_move.set_feedback_text(FlickAction.CLICK, "---")
        self.btn_move.set_feedback_text(FlickAction.LEFT, "Move\nLeft")
        self.btn_move.set_feedback_text(FlickAction.RIGHT, "Move\nRight")
        self.btn_move.set_feedback_text(FlickAction.UP, "Move\nUp")
        self.btn_move.set_feedback_text(FlickAction.DOWN, "Move\nDown")
        
        self.btn_move.actionTriggered.connect(self._handle_move)
        layout.addWidget(self.btn_move)

    # --- INTERNAL HANDLERS ---
    def _handle_draw(self, action):
        if action == FlickAction.CLICK: self.toolChanged.emit("Pen")
        elif action == FlickAction.LEFT: self.toolChanged.emit("Line")
        elif action == FlickAction.RIGHT: self.toolChanged.emit("Eraser")

    def _handle_color(self, action):
        if action == FlickAction.CLICK: self.colorChanged.emit("Black")
        elif action == FlickAction.LEFT: self.colorChanged.emit("Blue")
        elif action == FlickAction.RIGHT: self.colorChanged.emit("Red")
        elif action == FlickAction.UP: self.colorChanged.emit("Yellow")
        elif action == FlickAction.DOWN: self.colorChanged.emit("Green")

    def _handle_frame(self, action):
        if action == FlickAction.CLICK: self.newFrameRequested.emit("None")
        elif action == FlickAction.LEFT: self.newFrameRequested.emit("<=>")
        elif action == FlickAction.RIGHT: self.newFrameRequested.emit("=>")
        elif action == FlickAction.UP: self.newFrameRequested.emit("->")
        elif action == FlickAction.DOWN: self.newFrameRequested.emit("=")

    def _handle_move(self, action):
        if action == FlickAction.LEFT: self.moveRequested.emit("left")
        elif action == FlickAction.RIGHT: self.moveRequested.emit("right")
        elif action == FlickAction.UP: self.moveRequested.emit("up")
        elif action == FlickAction.DOWN: self.moveRequested.emit("down")
