from PyQt6.QtWidgets import QPushButton, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QMouseEvent
from enum import Enum, auto
from typing import Optional

class FlickAction(Enum):
    """
    Internal state enum for gesture detection.
    Defines the possible outcomes of a mouse interaction.
    """
    CLICK = auto()
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

class FlickButton(QPushButton):
    """
    A specific QPushButton that distinguishes between Clicks and Directional Flicks.

    TEMPLATE NOTE:
    To be compatible with the builder, this class must:
    1. Be instantiated via the module-level main() function.
    2. Provide setters naming 'set<Property>' for any custom JSON keys.
    3. Define signals that match 'on_<signal_name>' keys in the JSON.
    """

    # --- Signals ---
    # TEMPLATE NOTE: 
    # The builder maps JSON keys like "on_flick_up" to snake_case signals here.
    # Ensure your signal names match the JSON event names minus the "on_" prefix.
    clicked = pyqtSignal()
    flick_up = pyqtSignal()
    flick_down = pyqtSignal()
    flick_left = pyqtSignal()
    flick_right = pyqtSignal()

    def __init__(self, text: Optional[str] = None, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the widget.
        
        Args:
            text: Initial text (standard QPushButton argument).
            parent: Parent widget (standard Qt argument).
        """
        super().__init__(text, parent)

        # --- Internal Properties ---
        # Initialize defaults. The builder will populate custom properties 
        # via the setters defined below.
        self._default_text: str = text if text is not None else ""
        self.min_swipe_distance: int = 10
        
        # Feedback text holders (None means "use default text")
        self.clicked_text: Optional[str] = None
        self.flick_up_text: Optional[str] = None
        self.flick_down_text: Optional[str] = None
        self.flick_left_text: Optional[str] = None
        self.flick_right_text: Optional[str] = None

        # --- Internal State ---
        self.start_pos: Optional[QPoint] = None
        self.current_action: FlickAction = FlickAction.CLICK
        
        # Initial Style
        self._update_style(active=False)

    # --- Builder Compatibility Setters ---
    # TEMPLATE NOTE:
    # Your builder constructs setter names dynamically using:
    # setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
    #
    # Therefore, for a JSON property "flick_up_text", the builder looks for "setFlick_up_text".
    # Standard Python properties (@property) won't work with that specific loader logic 
    # unless you define these specific setter methods.

    def setClicked_text(self, text: str) -> None:
        """Sets the text displayed when the button is held/clicked."""
        self.clicked_text = text

    def setFlick_up_text(self, text: str) -> None:
        """Sets the text displayed when dragging UP."""
        self.flick_up_text = text

    def setFlick_down_text(self, text: str) -> None:
        """Sets the text displayed when dragging DOWN."""
        self.flick_down_text = text

    def setFlick_left_text(self, text: str) -> None:
        """Sets the text displayed when dragging LEFT."""
        self.flick_left_text = text

    def setFlick_right_text(self, text: str) -> None:
        """Sets the text displayed when dragging RIGHT."""
        self.flick_right_text = text

    def setMin_swipe_distance(self, dist: int) -> None:
        """Sets the minimum pixel distance to qualify as a flick."""
        self.min_swipe_distance = dist

    # -------------------------------------------------
    # --- Internal Logic ---
    # -------------------------------------------------

    def _get_feedback_text(self, action: FlickAction) -> str:
        """
        Retrieves the feedback text for a specific action.
        Falls back to the default button text if no specific text is set.
        """
        text_map = {
            FlickAction.CLICK: self.clicked_text,
            FlickAction.UP: self.flick_up_text,
            FlickAction.DOWN: self.flick_down_text,
            FlickAction.LEFT: self.flick_left_text,
            FlickAction.RIGHT: self.flick_right_text,
        }
        content = text_map.get(action)
        return content if content is not None else self._default_text

    def _update_style(self, active: bool, action: Optional[FlickAction] = None) -> None:
        """
        Placeholder for dynamic styling (e.g., changing colors based on direction).
        """
        pass

    def _calculate_action(self, end_pos: QPoint) -> FlickAction:
        """
        Calculates whether the user clicked or flicked based on drag distance and angle.
        
        Args:
            end_pos: The current mouse position.
            
        Returns:
            The determined FlickAction.
        """
        if not self.start_pos: 
            return FlickAction.CLICK

        dx = end_pos.x() - self.start_pos.x()
        dy = end_pos.y() - self.start_pos.y()
        
        # Euclidean distance
        dist = (dx**2 + dy**2)**0.5

        if dist < self.min_swipe_distance:
            return FlickAction.CLICK
        
        # Determine dominant axis
        if abs(dx) > abs(dy):
            return FlickAction.RIGHT if dx > 0 else FlickAction.LEFT
        else:
            return FlickAction.DOWN if dy > 0 else FlickAction.UP

    # --- Event Overrides ---

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handles the start of the interaction."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()
            self.current_action = FlickAction.CLICK
            
            # TEMPLATE NOTE:
            # We capture self.text() here because the text might have been set 
            # via the standard "text" property in JSON after __init__ ran.
            self._default_text = self.text()

            # Update UI to show feedback
            self.setText(self._get_feedback_text(FlickAction.CLICK))
            self._update_style(active=True, action=FlickAction.CLICK)
            
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handles the drag interaction to update feedback text dynamically."""
        if self.start_pos:
            curr_pos = event.globalPosition().toPoint()
            new_action = self._calculate_action(curr_pos)

            # Only update UI if the action state has changed
            if new_action != self.current_action:
                self.current_action = new_action
                self.setText(self._get_feedback_text(new_action))
                self._update_style(active=True, action=new_action)
        
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Finalizes the interaction and emits the appropriate signal."""
        if self.start_pos:
            if self.current_action == FlickAction.CLICK:
                self.clicked.emit()
            elif self.current_action == FlickAction.UP:
                self.flick_up.emit()
            elif self.current_action == FlickAction.DOWN:
                self.flick_down.emit()
            elif self.current_action == FlickAction.LEFT:
                self.flick_left.emit()
            elif self.current_action == FlickAction.RIGHT:
                self.flick_right.emit()
            
        # Reset UI to default state
        self.start_pos = None
        self.setText(self._default_text)
        self._update_style(active=False)
        super().mouseReleaseEvent(event)

def main() -> QWidget:
    """
    TEMPLATE NOTE:
    This is the mandatory entry point for the builder.
    It must return an instance of the QWidget (or QLayout).
    """
    return FlickButton()
