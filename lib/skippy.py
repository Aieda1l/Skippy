import sys
import keyboard
import timeit
import math
import signal
import ctypes
import mss
import qdarktheme
from termcolor import colored
from PySide6 import *
from PySide6.QtGui import *

if __name__ == "__main__":
    print("Do not run this file directly.")

# Custom modules
from lib.grab import *
from lib.mouse_handler import *
from lib.gui import *

# Pose detection
import torch
import posenet


class Config:
    def __init__(self):
        self.ENABLE_AIMBOT = True
        self.YOLO_DIRECTORY = "models"
        # Neural net configs
        self.CONFIDENCE = 0.15
        self.MAXDETECTIONS = 10
        # FOV
        self.ACTIVATION_RANGE = 250  # Size (in pixels) of the screen capture box for neural net
        # Overlay
        self.OVERLAY_ENABLED = True
        self.OUTLINE_COLOR = QColor(Qt.white)
        self.DOT_RADIUS = 1
        # Aimbot configs
        self.SMOOTHNESS = 0
        self.TARGET_LIMB = "head"
        self.ENEMY_COLOR_LOWER = np.array([140, 110, 150])
        self.ENEMY_COLOR_UPPER = np.array([150, 195, 255])

        # Other
        self.CIRCLE_RADIUS = min(self.ACTIVATION_RANGE, self.ACTIVATION_RANGE) // 2
        self.TARGET_WIDTH = 512  # Size (in pixels) of what to scale the screen capture up to before it's fed into the neural net
        self.LINE_LENGTH = 20  # Bounding box corner length


# Initialize posenet model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = posenet.load_model(101)
model = model.to(device)
output_stride = model.output_stride

# Define the number of keypoints per pose (17 in this case)
keypoints_per_pose = 17

# Mouse time model
timeNet = TimeNet()
timeNet.to(device)
timeNet.load_state_dict(torch.load("./_models/time_network_state_R3", map_location=device))


# Keypoint index numbers:
# 0: nose
# 1: left_eye
# 2: right_eye
# 3: left_ear
# 4: right_ear
# 5: left_shoulder
# 6: right_shoulder
# 7: left_elbow
# 8: right_elbow
# 9: left_wrist
# 10: right_wrist
# 11: left_hip
# 12: right_hip
# 13: left_knee
# 14: right_knee
# 15: left_ankle
# 16: right_ankle

# Structures for input handling
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]


class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]


class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]


class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]


class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]


def calculate_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def is_enemy(image, x, y, width, height,
             lower=np.array([140, 110, 150]),
             upper=np.array([150, 195, 255])):
    try:
        # Crop the image to the specified rectangle
        roi = image[y:y + height, x:x + width]

        # Convert the cropped region to HSV color space
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # Create a mask to isolate purple pixels within the specified range
        mask = cv2.inRange(hsv_roi, lower, upper)

        dilated = cv2.dilate(mask, None, iterations=5)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        if not contours:
            return False

        return True
    except:
        pass

    return False


class Skippy:
    def __init__(self):
        self.config = Config()
        self.sct = mss.mss()
        self.fps = 0
        self.interpolation_delay = 0
        # Define screen capture area
        print("[INFO] Loading screen capture device...")
        self.Wd, self.Hd = self.sct.monitors[1]["width"], self.sct.monitors[1]["height"]
        self.origbox = (int(self.Wd / 2 - self.config.ACTIVATION_RANGE / 2),
                        int(self.Hd / 2 - self.config.ACTIVATION_RANGE / 2),
                        int(self.Wd / 2 + self.config.ACTIVATION_RANGE / 2),
                        int(self.Hd / 2 + self.config.ACTIVATION_RANGE / 2))
        self.mouse_position = MousePosition(skippy=self, config=self.config)
        self.mouse_position.timeNet = timeNet
        self.app = QApplication(sys.argv)
        self.gui = GUIOverlay(skippy=self, config=self.config)
        self.gui.main_window.show()
        self.overlay = None

        if not self.config.OVERLAY_ENABLED:
            print("[INFO] Overlay disabled")
        else:
            print(colored("[OKAY] Overlay enabled!", "green"))
            self.overlay = GameOverlay(config=self.config)
            self.overlay.show()
        qdarktheme.setup_theme("dark")

    # Function to start the main process
    def start(self):
        # Log whether aimbot is enabled
        if not self.config.ENABLE_AIMBOT:
            print("[INFO] Aimbot disabled, using visualizer only...")
        else:
            print(colored("[OKAY] Aimbot enabled!", "green"))

        # Handle Ctrl+C in terminal, release pointers
        def signal_handler(sig=0, frame=0):
            # Release the file pointers
            print("\n[INFO] Cleaning up...")
            self.mouse_position.stop_mouse()
            self.sct.close()
            cv2.destroyAllWindows()
            self.gui.main_window.close()
            if self.overlay:
                self.overlay.close()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        # Register a hotkey to exit the application
        # keyboard.add_hotkey("esc", signal_handler)

        # Function to toggle aimbot state
        def toggle_aimbot():
            self.config.ENABLE_AIMBOT = not self.config.ENABLE_AIMBOT
            self.gui.aimbot_checkbox.setChecked(self.config.ENABLE_AIMBOT)

        keyboard.add_hotkey("f", toggle_aimbot)

        # Test for GPU support
        build_info = str("".join(cv2.getBuildInformation().split()))
        if cv2.ocl.haveOpenCL():
            cv2.ocl.setUseOpenCL(True)
            cv2.ocl.useOpenCL()
            print(colored("[OKAY] OpenCL is working!", "green"))
        else:
            print(
                colored("[WARNING] OpenCL acceleration is disabled!", "yellow"))

        if "CUDA:YES" in build_info:
            print(colored("[OKAY] CUDA is working!", "green"))
        else:
            print(
                colored("[WARNING] CUDA acceleration is disabled!", "yellow"))

        print()

        start_time = timeit.default_timer()
        frame_count = 0

        while True:
            frame = np.array(grab_screen(region=self.origbox))
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

            # Resize the frame to target width while preserving the aspect ratio
            scale_factor = self.config.TARGET_WIDTH / self.config.ACTIVATION_RANGE
            target_height = int(frame.shape[0] * scale_factor)
            frame = cv2.resize(frame, (self.config.TARGET_WIDTH, target_height))

            input_image, display_image, output_scale = posenet.read_numpy(
                frame, scale_factor=0.7125, output_stride=output_stride)

            # Start measuring frame processing time
            frame_start_time = timeit.default_timer()

            with torch.no_grad():
                input_image = torch.Tensor(input_image).to(device)
                heatmaps_result, offsets_result, displacement_fwd_result, displacement_bwd_result = model(input_image)

                pose_scores, keypoint_scores, keypoint_coords, pose_offsets = posenet.decode_multiple_poses(
                    heatmaps_result.squeeze(0),
                    offsets_result.squeeze(0),
                    displacement_fwd_result.squeeze(0),
                    displacement_bwd_result.squeeze(0),
                    output_stride=output_stride,
                    max_pose_detections=self.config.MAXDETECTIONS,
                    min_pose_score=self.config.CONFIDENCE)

            keypoint_coords *= output_scale

            # TODO this isn't particularly fast, use GL for drawing and display someday...
            overlay_image = posenet.draw_skel_and_kp(
                display_image, pose_scores, keypoint_scores, keypoint_coords,
                min_pose_score=self.config.CONFIDENCE, min_part_score=self.config.CONFIDENCE,
                color=(self.config.OUTLINE_COLOR.blue(), self.config.OUTLINE_COLOR.green(), self.config.OUTLINE_COLOR.red()))

            keypoints = posenet.get_keypoints(
                pose_scores, keypoint_scores, keypoint_coords,
                min_pose_score=self.config.CONFIDENCE, min_part_score=self.config.CONFIDENCE)

            if any(keypoints):
                best_pose = None
                closest_distance = None

                for pose in keypoints:
                    keypoints_np = np.array(pose)

                    # Remove keypoints with zero values
                    keypoints_np = keypoints_np[(keypoints_np[:, 0] != 0) & (keypoints_np[:, 1] != 0)]

                    if not keypoints_np.size == 0:
                        # Find the minimum and maximum coordinates
                        min_x = np.min(keypoints_np[:, 0])
                        min_y = np.min(keypoints_np[:, 1])
                        max_x = np.max(keypoints_np[:, 0])
                        max_y = np.max(keypoints_np[:, 1])

                        # Draw the bounding box on the image
                        color = (self.config.OUTLINE_COLOR.blue(), self.config.OUTLINE_COLOR.green(), self.config.OUTLINE_COLOR.red())

                        # Top-left corner lines
                        cv2.line(overlay_image, (int(min_x), int(min_y)), (int(min_x) + self.config.LINE_LENGTH, int(min_y)), color)
                        cv2.line(overlay_image, (int(min_x), int(min_y)), (int(min_x), int(min_y) + self.config.LINE_LENGTH), color)

                        # Top-right corner lines
                        cv2.line(overlay_image, (int(max_x), int(min_y)), (int(max_x) - self.config.LINE_LENGTH, int(min_y)), color)
                        cv2.line(overlay_image, (int(max_x), int(min_y)), (int(max_x), int(min_y) + self.config.LINE_LENGTH), color)

                        # Bottom-right corner lines
                        cv2.line(overlay_image, (int(max_x), int(max_y)), (int(max_x) - self.config.LINE_LENGTH, int(max_y)), color)
                        cv2.line(overlay_image, (int(max_x), int(max_y)), (int(max_x), int(max_y) - self.config.LINE_LENGTH), color)

                        # Bottom-left corner lines
                        cv2.line(overlay_image, (int(min_x), int(max_y)), (int(min_x) + self.config.LINE_LENGTH, int(max_y)), color)
                        cv2.line(overlay_image, (int(min_x), int(max_y)), (int(min_x), int(max_y) - self.config.LINE_LENGTH), color)

                        enemy = is_enemy(display_image, int(min_x), int(min_y), int(max_x), int(max_y),
                                              self.config.ENEMY_COLOR_LOWER,
                                              self.config.ENEMY_COLOR_UPPER)
                        enemy_distance = calculate_distance([min_x, min_y], [max_x, max_y])

                        if (not closest_distance or enemy_distance > closest_distance) and enemy:
                            best_pose = pose
                            closest_distance = enemy_distance

                if best_pose:
                    x = 0
                    y = 0

                    for keypoint in best_pose:
                        if any(keypoint):
                            x = keypoint[0]
                            y = keypoint[1]
                            break

                    # Draw target dot on the frame
                    cv2.circle(overlay_image, (int(x), int(y)), 5, (0, 0, 255), -1)

                    if self.config.ENABLE_AIMBOT:
                        scaledX = x / scale_factor
                        scaledY = y / scale_factor

                        mouseX = scaledX + (self.Wd - overlay_image.shape[0] / scale_factor) / 2
                        mouseY = scaledY + (self.Hd - overlay_image.shape[1] / scale_factor) / 2

                        self.mouse_position.set_pos(mouseX, mouseY, self.config.SMOOTHNESS)

            cv2.imshow('Neural Net Vision (Skippy)', overlay_image)
            elapsed = timeit.default_timer() - start_time

            frame_count += 1
            if frame_count >= 10:  # Update FPS every 10 frames
                elapsed = timeit.default_timer() - start_time
                self.fps = frame_count / elapsed
                frame_count = 0
                start_time = timeit.default_timer()

            # Calculate inference time for the current frame
            frame_end_time = timeit.default_timer()
            self.interpolation_delay = (frame_end_time - frame_start_time) * 1000  # Convert to milliseconds

            # Update labels in the GUI
            self.gui.update_labels()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Clean up on exit
        signal_handler(0, 0)
