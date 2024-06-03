import time
import interception
import serial
import socket
import threading
import win32con

# Custom modules
from lib.skippy import *
from lib.windmouse import *
class Mouse:
    def __init__(self, config):
        self.COM_TYPE = config.COM_TYPE
        self.CLICK_THREAD = threading.Thread(target=self.send_click)
        self.LAST_CLICK_TIME = time.time()
        self.TARGET_CPS = config.TARGET_CPS

        # Create a lock, so we can use it to not send multiple mouse clicks at the same time
        self.LOCK = threading.Lock()

        self.SYMBOLS = config.SYMBOLS
        self.CODE = config.CODE
        self.ENCRYPT = config.ENCRYPT

        self.IP = config.IP
        self.PORT = config.PORT
        self.CLIENT = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.COM_PORT = config.COM_PORT
        self.BOARD = None

        # Create variables to store the remainder decimal points for our mouse move function
        self.REMAINDER_X = 0
        self.REMAINDER_Y = 0

        match self.COM_TYPE:
            case "socket":
                print(f"Connecting to {self.IP}:{self.PORT}...")
                try:
                    self.CLIENT.connect((self.IP, self.PORT))
                    print("Socket connected")
                except Exception as e:
                    print(f"ERROR: Could not connect (Socket). {e}")
                    self.close_connection()
            case "serial":
                try:
                    self.BOARD = serial.Serial(self.COM_PORT, 115200)
                    print("Serial connected")
                except Exception as e:
                    print(f"ERROR: Could not connect (Serial). {e}")
                    self.close_connection()
            case "driver":
                interception.auto_capture_devices(mouse=True)

    def __del__(self):
        self.close_connection()

    def close_connection(self):
        if self.COM_TYPE == "socket":
            if self.CLIENT is not None:
                self.CLIENT.close()
        elif self.COM_TYPE == "serial":
            if self.BOARD is not None:
                self.BOARD.close()

    def encrypt_command(self, command):
        if self.ENCRYPT:
            encrypted_command = ""
            for char in command:
                if char in self.SYMBOLS:
                    index = self.SYMBOLS.index(char)
                    encrypted_command += self.CODE[index]
                else:
                    encrypted_command += char  # Keep non-symbol characters unchanged
            return encrypted_command
        else:
            return command

    def move(self, x, y):
        # Add the remainder from the previous calculation
        x += self.REMAINDER_X
        y += self.REMAINDER_Y

        # Round x and y, and calculate the new remainder
        self.REMAINDER_X = x
        self.REMAINDER_Y = y
        x = int(x)
        y = int(y)
        self.REMAINDER_X -= x
        self.REMAINDER_Y -= y

        if x != 0 or y != 0:
            match self.COM_TYPE:
                case "socket" | "serial":
                    self.send_command(f"M{x},{y}\r")
                case "driver":
                    interception.move_relative(x, y)
                    print(f"M({x}, {y})")
                case "none":
                    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, x, y, 0, 0)
                    print(f"M({x}, {y})")

    def click(self, delay_before_click=0):
        if (
                not self.CLICK_THREAD.is_alive() and
                time.time() - self.LAST_CLICK_TIME >= 1 / self.TARGET_CPS
        ):
            self.CLICK_THREAD = threading.Thread(target=self.send_click, args=(delay_before_click,))
            self.CLICK_THREAD.start()

    def send_click(self, delay_before_click=0):
        time.sleep(delay_before_click)
        self.LAST_CLICK_TIME = time.time()
        match self.COM_TYPE:
            case "socket" | "serial":
                self.send_command("C\r")
            case "driver":
                random_delay = (np.random.randint(40) + 40) / 1000
                interception.mouse_down("left")
                time.sleep(random_delay)
                interception.mouse_up("left")
                print(f"C({random_delay * 1000:g})")
            case "none":
                random_delay = (np.random.randint(40) + 40) / 1000
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(random_delay)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                print(f"C({random_delay * 1000:g})")
        time.sleep((np.random.randint(10) + 25) / 1000)  # Sleep to avoid sending another click instantly after mouseup

    def send_command(self, command):
        command = self.encrypt_command(command)
        with self.LOCK:
            match self.COM_TYPE:
                case "socket":
                    print(self.CLIENT)
                    self.CLIENT.sendall(command.encode())
                case "serial":
                    self.BOARD.write(command.encode())
            print(f"Sent: {command}")
            print(f"Response from {self.COM_TYPE}: {self.get_response()}")

    def get_response(self):  # Waits for a response before sending a new instruction
        match self.COM_TYPE:
            case "socket":
                return self.CLIENT.recv(4).decode()
            case "serial":
                while True:
                    receive = self.BOARD.readline().decode("utf-8").strip()
                    if len(receive) > 0:
                        return receive
