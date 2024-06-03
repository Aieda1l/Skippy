import sys
import threading
import pynput
from pynput.mouse import Controller
import win_precise_time as wpt

# Custom modules
from lib.skippy import *
from lib.windmouse import *

SendInput = ctypes.windll.user32.SendInput
PUL = ctypes.POINTER(ctypes.c_ulong)


class MousePosition:
    def __init__(self, skippy, config):
        self.skippy = skippy
        self.config = config

        self.mouse = Controller()
        self.x, self.y = self.mouse.position
        self.target_x, self.target_y = None, None
        self.enabled = True
        self.idle = False
        self.kill = False
        self.timeNet = None
        self.move_thread = threading.Thread(target=self.move_mouse)
        self.move_thread.start()

    def move_mouse(self):
        while True:
            if not self.target_x is None and not self.target_x is None and not self.x == self.target_x and not self.y == self.target_y and self.enabled and not self.idle:
                points = wind_mouse_points(self.x, self.y, self.target_x, self.target_y, time_model=self.timeNet)

                for i in range(len(points)):
                    point = points[i]

                    new_x = 1 + int(point[0] * 65536.0 / self.skippy.Wd)  # Adjust for screen width
                    new_y = 1 + int(point[1] * 65536.0 / self.skippy.Hd)  # Adjust for screen height

                    extra = ctypes.c_ulong(0)
                    ii_ = pynput._util.win32.INPUT_union()
                    ii_.mi = pynput._util.win32.MOUSEINPUT(new_x, new_y, 0, (0x0001 | 0x8000), 0,
                                                           ctypes.cast(ctypes.pointer(extra), ctypes.c_void_p))
                    command = pynput._util.win32.INPUT(ctypes.c_ulong(0), ii_)
                    SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))

                    # Adjust the sleep time to control the speed of mouse movement
                    time_to_sleep = float((point[2] / 1000) * (self.config.SMOOTHNESS / 10 + 1))
                    wpt.sleep(time_to_sleep)

                self.x, self.y = self.mouse.position
                self.idle = True
            elif self.kill:
                sys.exit()
            else:
                wpt.sleep(0.01)

    def set_pos(self, x, y):
        self.idle = False
        self.target_x = x
        self.target_y = y

    def stop_mouse(self):
        self.kill = True

    def toggle_movement(self):
        if self.enabled:
            self.enabled = False
        elif not self.enabled:
            self.enabled = True
