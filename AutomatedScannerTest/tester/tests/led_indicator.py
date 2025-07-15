from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPainter, QBrush, QColor
from PySide6.QtCore import Qt


class PassFailIndicator(QLabel):
    """
    A QLabel-based widget that displays a circular LED-style indicator, which can be colored to represent pass/fail or other statuses.
    Parameters:
        color (str): The initial color of the indicator (default is "red").
        size (int): The diameter of the indicator in pixels (default is 20).
        parent (QWidget, optional): The parent widget.
    Methods:
        set_color(color):
            Set the color of the LED indicator and update its appearance.
    Overrides:
        paintEvent(event):
            Custom paint event to draw the circular indicator with the current color.
    """
    def __init__(self, color="red", size=20, parent=None):
        """
        Initializes the LED indicator widget.

        Args:
            color (str, optional): The color of the LED indicator. Defaults to "red".
            size (int, optional): The size (width and height) of the LED indicator in pixels. Defaults to 20.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.color = color
        self.size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        """
        Handles the paint event for the widget, rendering a circular LED indicator.

        This method creates a QPainter object to draw an anti-aliased ellipse (circle)
        representing the LED indicator. The ellipse is filled with the color specified
        by `self.color` and sized according to `self.size`. No border is drawn.

        Args:
            event (QPaintEvent): The paint event object containing event parameters.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(QColor(self.color))
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.size, self.size)

    def set_color(self, color):
        """
        Sets the color of the LED indicator and updates its display.

        Args:
            color (str): The color to set the LED indicator to.
        """
        self.color = color
        self.update()
