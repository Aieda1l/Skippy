import sys

import cv2
import numpy as np
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from termcolor import colored

# Custom modules
from lib.skippy import *


def addHoverEffect(button):
    button.setStyleSheet("""
        QToolButton:hover {
            background-color: rgba(0, 0, 0, 0.2);
        }
    """)


def setButtonIcon(button, icon_path):
    pixmap = QPixmap(icon_path)
    button.setIcon(QIcon(pixmap))
    button.setIconSize(pixmap.size())
    button.setStyleSheet("QToolButton { background-color: transparent; }")
    button.setCursor(Qt.PointingHandCursor)
    button.setAutoFillBackground(True)


class TitleBar(QWidget):
    height = 35

    def __init__(self, parent, skippy, config):
        super(TitleBar, self).__init__(parent)

        self.skippy = skippy
        self.config = config

        # Window movement attributes
        self.prevGeo = self.geometry()
        self.pressing = False
        self.maximizedWindow = False
        self.prevMousePos = QPointF()

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 10, 0)

        # Window title
        self.window_title = QLabel("Skippy: Neural-Network Aimbot (v0.1)")
        self.window_title.setAlignment(Qt.AlignCenter)
        self.window_title.setAccessibleName("lbl_title")
        self.window_title.setFixedHeight(self.height)

        # Changing title font
        self.window_title.setStyleSheet(f'font: bold 12pt "Segoe UI"')

        self.layout.addStretch(1)
        self.layout.addWidget(self.window_title)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.maximizedWindow = False

        # Close button
        self.closeButton = QToolButton()
        self.closeButton.setAccessibleName("btn_close")
        setButtonIcon(self.closeButton, "images/icon_close.svg")
        self.closeButton.clicked.connect(self.onClickClose)
        addHoverEffect(self.closeButton)

        # Maximize button
        self.maxButton = QToolButton()
        self.maxButton.setAccessibleName("btn_max")
        setButtonIcon(self.maxButton, "images/icon_maximize.svg")
        self.maxButton.clicked.connect(self.showMaxRestore)
        addHoverEffect(self.maxButton)

        # Minimize button
        self.hideButton = QToolButton()
        self.hideButton.setAccessibleName("btn_min")
        setButtonIcon(self.hideButton, "images/icon_minimize.svg")
        self.hideButton.clicked.connect(self.onClickHide)
        addHoverEffect(self.hideButton)

        self.layout.addWidget(self.hideButton)
        self.layout.addWidget(self.maxButton)
        self.layout.addWidget(self.closeButton)
        self.setLayout(self.layout)

        # Set button tooltips
        self.hideButton.setToolTip("Minimize")
        self.maxButton.setToolTip("Maximize")
        self.closeButton.setToolTip("Close")

    def onClickClose(self):
        print("\n[INFO] Cleaning up...")
        self.skippy.mouse_position.stop_mouse()
        self.skippy.sct.close()
        cv2.destroyAllWindows()
        self.skippy.gui.main_window.close()
        if self.skippy.overlay:
            self.skippy.overlay.close()
        sys.exit(0)

    def onClickHide(self):
        self.skippy.gui.main_window.showMinimized()

    # Event functions
    def mouseReleaseEvent(self, event):
        if event.globalPosition().y() < 10:
            self.showMaxRestore()

    def mousePressEvent(self, event):
        self.prevMousePos = event.scenePosition()
        self.pressing = True

        if event.type() == QEvent.MouseButtonDblClick:
            self.showMaxRestore()

    def mouseMoveEvent(self, event):
        if self.maximizedWindow:
            self.skippy.gui.main_window.showNormal()
            self.maximizedWindow = False
            self.prevMousePos = QPointF((self.prevGeo.width() * .5), (self.prevGeo.height() * .5))

        if self.pressing:
            mousePosition = event.globalPosition()
            pos = mousePosition - self.prevMousePos
            x = pos.x()
            y = pos.y()
            self.skippy.gui.main_window.move(x, y)

    def showMaxRestore(self):
        if self.maximizedWindow:
            self.skippy.gui.main_window.showNormal()
            self.maximizedWindow = False
            setButtonIcon(self.maxButton, "images/icon_maximize.svg")
            self.maxButton.setToolTip("Maximize")
        else:
            self.prevGeo = self.geometry()
            self.skippy.gui.main_window.showMaximized()
            self.maximizedWindow = True
            setButtonIcon(self.maxButton, "images/icon_restore.svg")
            self.maxButton.setToolTip("Restore")


class GUIOverlay(QMainWindow):
    def __init__(self, skippy, config):
        super(GUIOverlay, self).__init__()

        self.skippy = skippy
        self.config = config

        # Create the main window
        self.main_window = QMainWindow()
        self.main_window.setWindowTitle("Skippy: Neural-Network Aimbot (v0.1)")
        self.main_window.setGeometry(100, 100, 800, 600)
        self.main_window.setWindowFlags(Qt.FramelessWindowHint |
                                        Qt.WindowMaximizeButtonHint |
                                        Qt.WindowMinimizeButtonHint |
                                        Qt.WindowStaysOnTopHint
                                        )
        self.main_window.setAttribute(Qt.WA_TranslucentBackground)

        # Set default font and round edges
        self.main_window.setStyleSheet('''
            font: 10pt "Segoe UI";
            border-radius: 10px;
        ''')

        # Create a central widget
        self.central_widget = QWidget()
        self.main_window.setCentralWidget(self.central_widget)

        # Create a layout for the central widget
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Title bar
        self.title_bar = TitleBar(self, skippy=self.skippy, config=self.config)
        self.layout.addWidget(self.title_bar, 1)

        # Create and configure labels and controls for adjustable variables
        self.config_label = QLabel("Configurations:")
        self.layout.addWidget(self.config_label)

        # Aimbot checkbox
        self.aimbot_checkbox = QCheckBox("Enable Aimbot")
        self.aimbot_checkbox.setChecked(self.config.ENABLE_AIMBOT)
        self.layout.addWidget(self.aimbot_checkbox)

        # Overlay enabled checkbox
        self.overlay_enabled_checkbox = QCheckBox("Enable Overlay")
        self.overlay_enabled_checkbox.setChecked(self.config.OVERLAY_ENABLED)
        self.layout.addWidget(self.overlay_enabled_checkbox)

        # Confidence slider
        confidence_layout = QHBoxLayout()
        self.confidence_label = QLabel("Confidence:")
        self.layout.addWidget(self.confidence_label)
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setMinimum(0)
        self.confidence_slider.setMaximum(100)
        self.confidence_slider.setValue(int(self.config.CONFIDENCE * 100))
        confidence_layout.addWidget(self.confidence_slider)
        self.confidence_value_label = QLabel(f"{self.config.CONFIDENCE:.2f}")  # Add a label to display the value
        self.confidence_value_label.setAlignment(Qt.AlignCenter)
        confidence_layout.addWidget(self.confidence_value_label)
        self.layout.addLayout(confidence_layout)

        # Create labels to display min and max values for sliders
        self.confidence_min_label = QLabel("Min: 0.00")
        self.confidence_max_label = QLabel("Max: 1.00")
        confidence_min_max_layout = QHBoxLayout()
        confidence_min_max_layout.addWidget(self.confidence_min_label)
        confidence_min_max_layout.addWidget(self.confidence_slider)
        confidence_min_max_layout.addWidget(self.confidence_max_label)
        self.layout.addLayout(confidence_min_max_layout)

        # Max detections slider
        maxdetections_layout = QHBoxLayout()
        self.maxdetections_label = QLabel("Max Detections:")
        self.layout.addWidget(self.maxdetections_label)
        self.maxdetections_slider = QSlider(Qt.Horizontal)
        self.maxdetections_slider.setMinimum(1)
        self.maxdetections_slider.setMaximum(20)
        self.maxdetections_slider.setValue(self.config.MAXDETECTIONS)
        maxdetections_layout.addWidget(self.maxdetections_slider)
        self.maxdetections_value_label = QLabel(f"{self.config.MAXDETECTIONS:.2f}")  # Add a label to display the value
        self.maxdetections_value_label.setAlignment(Qt.AlignCenter)
        maxdetections_layout.addWidget(self.maxdetections_value_label)
        self.layout.addLayout(maxdetections_layout)

        # Create labels to display min and max values for slider
        self.maxdetections_min_label = QLabel("Min: 1")
        self.maxdetections_max_label = QLabel("Max: 20")
        maxdetections_min_max_layout = QHBoxLayout()
        maxdetections_min_max_layout.addWidget(self.maxdetections_min_label)
        maxdetections_min_max_layout.addWidget(self.maxdetections_slider)
        maxdetections_min_max_layout.addWidget(self.maxdetections_max_label)
        self.layout.addLayout(maxdetections_min_max_layout)

        # Activation range slider
        activation_range_layout = QHBoxLayout()
        self.activation_range_label = QLabel("Activation Range:")
        self.layout.addWidget(self.activation_range_label)
        self.activation_range_slider = QSlider(Qt.Horizontal)
        self.activation_range_slider.setMinimum(50)
        self.activation_range_slider.setMaximum(800)
        self.activation_range_slider.setValue(self.config.ACTIVATION_RANGE)
        activation_range_layout.addWidget(self.activation_range_slider)
        self.activation_range_value_label = QLabel(
            f"{self.config.ACTIVATION_RANGE}")  # Add a label to display the value
        self.activation_range_value_label.setAlignment(Qt.AlignCenter)
        activation_range_layout.addWidget(self.activation_range_value_label)
        self.layout.addLayout(activation_range_layout)

        # Create labels to display min and max values for slider
        self.activation_range_min_label = QLabel("Min: 50")
        self.activation_range_max_label = QLabel("Max: 800")
        activation_range_min_max_layout = QHBoxLayout()
        activation_range_min_max_layout.addWidget(self.activation_range_min_label)
        activation_range_min_max_layout.addWidget(self.activation_range_slider)
        activation_range_min_max_layout.addWidget(self.activation_range_max_label)
        self.layout.addLayout(activation_range_min_max_layout)

        # Create a slider for smoothness
        smoothness_layout = QHBoxLayout()
        self.smoothness_label = QLabel("Smoothness:")
        self.layout.addWidget(self.smoothness_label)
        self.smoothness_slider = QSlider(Qt.Horizontal)
        self.smoothness_slider.setMinimum(0)
        self.smoothness_slider.setMaximum(10)
        self.smoothness_slider.setValue(self.config.SMOOTHNESS)
        smoothness_layout.addWidget(self.smoothness_slider)
        self.smoothness_value_label = QLabel(f"{self.config.SMOOTHNESS}")  # Add a label to display the value
        self.smoothness_value_label.setAlignment(Qt.AlignCenter)
        smoothness_layout.addWidget(self.smoothness_value_label)
        self.layout.addLayout(smoothness_layout)

        # Create labels to display min and max values for the slider
        self.smoothness_min_label = QLabel("Min: 0")
        self.smoothness_max_label = QLabel("Max: 20")
        smoothness_min_max_layout = QHBoxLayout()
        smoothness_min_max_layout.addWidget(self.smoothness_min_label)
        smoothness_min_max_layout.addWidget(self.smoothness_slider)
        smoothness_min_max_layout.addWidget(self.smoothness_max_label)
        self.layout.addLayout(smoothness_min_max_layout)

        # Disable rounding of the edges for elements
        self.aimbot_checkbox.setStyleSheet('''
            border-radius: 0px;
        ''')
        self.overlay_enabled_checkbox.setStyleSheet('''
            border-radius: 0px;
        ''')

        # Outline color dropdown menu
        self.outline_color_label = QLabel("Outline Color:")
        self.layout.addWidget(self.outline_color_label)
        self.outline_color_dropdown = QComboBox()
        self.outline_color_dropdown.addItems(["White", "Red", "Green", "Blue"])
        current_color_index = self.outline_color_dropdown.findText("White")
        self.outline_color_dropdown.setCurrentIndex(current_color_index)
        self.layout.addWidget(self.outline_color_dropdown)

        # Outline color dropdown menu
        self.enemy_color_label = QLabel("Outline Color:")
        self.layout.addWidget(self.enemy_color_label)
        self.enemy_color_dropdown = QComboBox()
        self.enemy_color_dropdown.addItems(["Purple", "Red"])
        current_enemy_color_index = self.enemy_color_dropdown.findText("Purple")
        self.enemy_color_dropdown.setCurrentIndex(current_enemy_color_index)
        self.layout.addWidget(self.enemy_color_dropdown)

        # Target limb dropdown menu
        self.target_limb_label = QLabel("Target Limb:")
        self.layout.addWidget(self.target_limb_label)
        self.target_limb_dropdown = QComboBox()
        self.target_limb_dropdown.addItems(["Nose", "Left Eye", "Right Eye", "Left Ear", "Right Ear", "Left Shoulder", "Right Shoulder", "Left Elbow", "Right Elbow", "Left Wrist", "Right Wrist", "Left Hip", "Right Hip", "Left Knee", "Right Knee", "Left Ankle", "Right Ankle"])
        current_target_limb_index = self.target_limb_dropdown.findText("Nose")
        self.target_limb_dropdown.setCurrentIndex(current_target_limb_index)
        self.layout.addWidget(self.target_limb_dropdown)

        # Create and configure labels for FPS and interpolation delay
        self.fps_label = QLabel("FPS: 0")
        self.layout.addWidget(self.fps_label)

        self.delay_label = QLabel("Interpolation Delay: 0 ms")
        self.layout.addWidget(self.delay_label)

        # Connect slider and checkbox signals to the update_variables function
        self.aimbot_checkbox.stateChanged.connect(self.update_aimbot)
        self.confidence_slider.valueChanged.connect(self.update_variables)
        self.maxdetections_slider.valueChanged.connect(self.update_variables)
        self.activation_range_slider.sliderReleased.connect(self.update_fov)
        self.activation_range_slider.valueChanged.connect(self.update_value_labels)
        self.smoothness_slider.valueChanged.connect(self.update_variables)
        self.overlay_enabled_checkbox.stateChanged.connect(self.update_overlay)
        self.outline_color_dropdown.currentIndexChanged.connect(self.update_overlay_color)
        self.enemy_color_dropdown.currentIndexChanged.connect(self.update_enemy_color)
        self.target_limb_dropdown.currentIndexChanged.connect(self.update_target_limb)

        # Update the value labels initially
        self.update_value_labels()

    # Function to update FPS and interpolation delay labels
    def update_labels(self):
        self.fps_label.setText(f"FPS: {self.skippy.fps:.2f}")
        self.delay_label.setText(f"Interpolation Delay: {self.skippy.interpolation_delay:.2f} ms")

    # Update the value labels for sliders
    def update_value_labels(self):
        self.confidence_value_label.setText(f"{self.confidence_slider.value() / 100.0:.2f}")
        self.maxdetections_value_label.setText(f"{self.maxdetections_slider.value()}")
        self.activation_range_value_label.setText(f"{self.activation_range_slider.value()}")
        self.smoothness_value_label.setText(f"{self.smoothness_slider.value()}")

    # Log whether aimbot is enabled
    def update_aimbot(self):
        self.update_variables()
        self.skippy.mouse_position.toggle_movement()

        if not self.config.ENABLE_AIMBOT:
            print("[INFO] Aimbot disabled, using visualizer only...")
        else:
            print(colored("[OKAY] Aimbot enabled!", "green"))

    # Create/destroy FOV overlay
    def update_fov(self):
        self.update_variables()

        self.skippy.origbox = (int(self.skippy.Wd / 2 - self.config.ACTIVATION_RANGE / 2),
                               int(self.skippy.Hd / 2 - self.config.ACTIVATION_RANGE / 2),
                               int(self.skippy.Wd / 2 + self.config.ACTIVATION_RANGE / 2),
                               int(self.skippy.Hd / 2 + self.config.ACTIVATION_RANGE / 2))

        if self.skippy.overlay:
            self.skippy.overlay = GameOverlay(config=self.config)
            self.skippy.overlay.show()
            self.skippy.overlay.show()

        print("[INFO] FOV changed to " + str(self.config.ACTIVATION_RANGE))

    def update_overlay(self):
        self.update_variables()

        if not self.config.OVERLAY_ENABLED:
            print("[INFO] Overlay disabled")
            if self.skippy.overlay:
                self.skippy.overlay.close()
        else:
            print(colored("[OKAY] Overlay enabled!", "green"))
            self.skippy.overlay = GameOverlay(config=self.config)
            self.skippy.overlay.show()

    def update_overlay_color(self):
        self.update_variables()

        print("[INFO] Changed overlay color to " + self.outline_color_dropdown.currentText())

        self.skippy.overlay = GameOverlay(config=self.config)
        self.skippy.overlay.show()

    def update_enemy_color(self):
        self.update_variables()

        print("[INFO] Changed enemy color to " + self.enemy_color_dropdown.currentText())

    def update_target_limb(self):
        self.update_variables()

        print("[INFO] Changed target limb to " + self.target_limb_dropdown.currentText())

    # Update variables when sliders or checkboxes change
    def update_variables(self):
        self.config.ENABLE_AIMBOT = self.aimbot_checkbox.isChecked()
        self.config.CONFIDENCE = self.confidence_slider.value() / 100.0
        self.config.MAXDETECTIONS = self.maxdetections_slider.value()
        self.config.ACTIVATION_RANGE = self.activation_range_slider.value()
        self.config.OVERLAY_ENABLED = self.overlay_enabled_checkbox.isChecked()
        self.config.CIRCLE_RADIUS = min(self.config.ACTIVATION_RANGE, self.config.ACTIVATION_RANGE) // 2
        self.config.SMOOTHNESS = self.smoothness_slider.value()

        # Update the min and max labels for sliders
        self.confidence_min_label.setText(f"Min: {self.confidence_slider.minimum() / 100.0:.2f}")
        self.confidence_max_label.setText(f"Max: {self.confidence_slider.maximum() / 100.0:.2f}")
        self.maxdetections_min_label.setText(f"Min: {self.maxdetections_slider.minimum()}")
        self.maxdetections_max_label.setText(f"Max: {self.maxdetections_slider.maximum()}")
        self.activation_range_min_label.setText(f"Min: {self.activation_range_slider.minimum()}")
        self.activation_range_max_label.setText(f"Max: {self.activation_range_slider.maximum()}")
        self.smoothness_min_label.setText(f"Min: {self.smoothness_slider.minimum()}")
        self.smoothness_max_label.setText(f"Max: {self.smoothness_slider.maximum()}")

        # Update the value labels
        self.update_value_labels()

        # Assign the equivalent Qt color variable to OUTLINE_COLOR
        color_name = self.outline_color_dropdown.currentText()
        if color_name == "White":
            self.config.OUTLINE_COLOR = QColor(Qt.white)
        elif color_name == "Red":
            self.config.OUTLINE_COLOR = QColor(Qt.red)
        elif color_name == "Green":
            self.config.OUTLINE_COLOR = QColor(Qt.green)
        elif color_name == "Blue":
            self.config.OUTLINE_COLOR = QColor(Qt.blue)

        # Assign the equivalent Qt color variable to OUTLINE_COLOR
        color_name = self.enemy_color_dropdown.currentText()
        if color_name == "Purple":
            self.config.ENEMY_COLOR_LOWER = np.array([140, 110, 150])
            self.config.ENEMY_COLOR_UPPER = np.array([150, 195, 255])
        elif color_name == "Red":
            self.config.ENEMY_COLOR_LOWER = np.array([150, 110, 110])
            self.config.ENEMY_COLOR_UPPER = np.array([255, 181, 150])

        self.config.TARGET_LIMB = self.target_limb_dropdown.currentIndex()


# Custom widget for the game overlay
class GameOverlay(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)

        self.config = config

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
        painter.setPen(QColor(self.config.OUTLINE_COLOR))
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        painter.drawEllipse(circle_center_x - self.config.CIRCLE_RADIUS, circle_center_y - self.config.CIRCLE_RADIUS,
                            self.config.CIRCLE_RADIUS * 2, self.config.CIRCLE_RADIUS * 2)

        # Calculate dot's position in the center of the circle
        dot_center_x = circle_center_x
        dot_center_y = circle_center_y

        # Draw the dot
        painter.setPen(QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(QColor(self.config.OUTLINE_COLOR)))
        painter.drawEllipse(dot_center_x - self.config.DOT_RADIUS, dot_center_y - self.config.DOT_RADIUS,
                            self.config.DOT_RADIUS * 2, self.config.DOT_RADIUS * 2)
