import win32gui
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import win32gui
import win32con


ACTIVATION_RANGE = 250  # Size (in pixels) of the screen capture box for neural net
CIRCLE_RADIUS = min(ACTIVATION_RANGE, ACTIVATION_RANGE) // 2
OUTLINE_COLOR = QColor(Qt.white)
DOT_RADIUS = 1


class GameOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # Configure window properties
        self.setWindowTitle("Skippy: Neural-Network Aimbot (v0.1)")
        self.setWindowFlags(Qt.FramelessWindowHint |
                            Qt.WindowStaysOnTopHint |
                            Qt.WindowTransparentForInput |
                            Qt.MaximizeUsingFullscreenGeometryHint |
                            Qt.X11BypassWindowManagerHint |
                            Qt.SplashScreen |
                            Qt.Popup |
                            Qt.Tool |
                            Qt.Sheet
                            )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)

        # Get screen dimensions
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        # Set overlay size to match the screen
        self.setGeometry(0, 0, screen_width, screen_height)

        # Make sure window is on top all windows
        win32gui.SetWindowPos(self.winId(), win32con.HWND_TOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
        self.raise_()
        self.show()
        self.activateWindow()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw a transparent background
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        painter.drawRect(self.rect())

        # Calculate circle's center position
        circle_center_x = self.width() // 2
        circle_center_y = self.height() // 2

        # Draw circle outline
        painter.setPen(QColor(OUTLINE_COLOR))
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        painter.drawEllipse(circle_center_x - CIRCLE_RADIUS, circle_center_y - CIRCLE_RADIUS,
                            CIRCLE_RADIUS * 2, CIRCLE_RADIUS * 2)

        # Calculate dot's position in the center of the circle
        dot_center_x = circle_center_x
        dot_center_y = circle_center_y

        # Draw the dot
        painter.setPen(QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(QColor(OUTLINE_COLOR)))
        painter.drawEllipse(dot_center_x - DOT_RADIUS, dot_center_y - DOT_RADIUS,
                            DOT_RADIUS * 2, DOT_RADIUS * 2)


def get_window_id(name):
    def enum_windows_callback(hwnd, window_ids):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            window_text = win32gui.GetWindowText(hwnd)
            if window_text == name:
                window_ids.append(hwnd)
        return True

    window_ids = []
    win32gui.EnumWindows(enum_windows_callback, window_ids)
    print(window_ids)

    if window_ids:
        return window_ids[0]
    else:
        return None


def run_app(window_id):
    app = QApplication([])
    main_widget = GameOverlay()
    layout = QVBoxLayout(main_widget)

    window = QWindow.fromWinId(window_id)
    widget = QWidget.createWindowContainer(window)
    layout.addWidget(widget)

    main_widget.show()
    app.exec_()


if __name__ == '__main__':
    window_id = get_window_id('Clock')
    if window_id:
        run_app(window_id)
