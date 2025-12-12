from PyQt6.QtWidgets import QPushButton, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QMouseEvent
from enum import Enum, auto
from typing import Optional, Dict

class FlickAction(Enum):
    """
    Enumeration representing the detected input gestures.
    """
    CLICK = auto()
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

class FlickButton(QPushButton):
    """
    A custom QPushButton that distinguishes between a standard Click and directional Swipes (Flicks).

    It emits a single signal `actionTriggered` containing the `FlickAction` detected.
    Visual feedback is updated in real-time during the drag operation.

    Attributes:
        min_swipe_distance (int): The minimum distance (in pixels) the mouse must travel
            to register as a swipe rather than a click. Defaults to 10.
        actionTriggered (pyqtSignal): Signal emitted on release. Passes a `FlickAction` enum member.
    """

    # Signal emitting the detected action
    actionTriggered = pyqtSignal(FlickAction)

    def __init__(self, text: str = "Flick Me", parent: Optional[QWidget] = None) -> None:
        """
        Initialize the FlickButton.

        Args:
            text (str): The initial text to display on the button.
            parent (Optional[QWidget]): The parent widget, if any.
        """
        super().__init__(text, parent)
        
        # --- Public Configuration ---
        self.min_swipe_distance: int = 10
        
        # --- Internal State ---
        self.base_text: str = text
        self.start_pos: Optional[QPoint] = None
        self.current_action: FlickAction = FlickAction.CLICK
        
        # Mapping of actions to feedback text
        self.feedback_map: Dict[FlickAction, str] = {
            FlickAction.CLICK: "Release\nto Click",
            FlickAction.UP: "↑ UP",
            FlickAction.DOWN: "↓ DOWN",
            FlickAction.LEFT: "← LEFT",
            FlickAction.RIGHT: "→ RIGHT",
        }

        # Initial Style
        self.update_style(active=False)

    def set_feedback_text(self, action: FlickAction, text: str) -> None:
        """
        Sets the preview text displayed when a specific action is triggered.

        Args:
            action (FlickAction): The direction/action to customize (e.g., FlickAction.UP).
            text (str): The string to display on the button during the gesture.
        """
        self.feedback_map[action] = text

    def update_style(self, active: bool, action: Optional[FlickAction] = None) -> None:
        """
        Updates the button's visual style (QSS) based on the current state.

        Args:
            active (bool): True if the user is currently holding/dragging the button.
            action (Optional[FlickAction]): The currently detected action. 
                                            Used to distinguish between Click (blue) and Swipe (orange).
        """
        base_css = """
            QPushButton {
                border-radius: 15px;
                font-weight: bold;
                font-size: 14px;
                border: 3px solid #555;
                padding: 10px;
            }
        """
        
        if not active:
            # Idle State
            color_css = "background-color: #eee; color: #333;"
        elif action == FlickAction.CLICK:
            # Hover/Click State (Dead Zone)
            color_css = "background-color: #90cdf4; color: #000; border-color: #3182ce;"
        else:
            # Swipe State
            color_css = "background-color: #fbd38d; color: #000; border-color: #dd6b20;"

        self.setStyleSheet(base_css + color_css)

    def _get_action(self, end_pos: QPoint) -> FlickAction:
        """
        Calculates the action based on the vector from start_pos to end_pos.

        Args:
            end_pos (QPoint): The current global position of the mouse/touch.

        Returns:
            FlickAction: The determined action (CLICK, UP, DOWN, LEFT, or RIGHT).
        """
        if not self.start_pos: 
            return FlickAction.CLICK

        dx = end_pos.x() - self.start_pos.x()
        dy = end_pos.y() - self.start_pos.y()
        dist = (dx**2 + dy**2)**0.5

        if dist < self.min_swipe_distance:
            return FlickAction.CLICK
        
        # Determine dominant axis
        if abs(dx) > abs(dy):
            return FlickAction.RIGHT if dx > 0 else FlickAction.LEFT
        else:
            return FlickAction.DOWN if dy > 0 else FlickAction.UP

    # --- Event Handlers ---
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()
            self.current_action = FlickAction.CLICK
            self.update_style(active=True, action=self.current_action)
            self.setText(self.feedback_map[FlickAction.CLICK])
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.start_pos:
            curr_pos = event.globalPosition().toPoint()
            new_action = self._get_action(curr_pos)

            if new_action != self.current_action:
                self.current_action = new_action
                self.update_style(active=True, action=new_action)
                # Show preview text
                self.setText(self.feedback_map.get(new_action, ""))
        
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.start_pos:
            # Emit the signal with the final action
            self.actionTriggered.emit(self.current_action)
            
        # Reset UI
        self.start_pos = None
        self.setText(self.base_text)
        self.update_style(active=False)
        super().mouseReleaseEvent(event)
