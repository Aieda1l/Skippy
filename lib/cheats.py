import win32api


class Cheats:
    def __init__(self, config):
        self.config = config

        # Aim
        self.move_x, self.move_y = (0, 0)
        self.previous_x, self.previous_y = (0, 0)

        # Recoil
        self.RECOIL_OFFSET = 0
        self.config.RECOIL_MODE = config.RECOIL_MODE
        self.config.RECOIL_X = config.RECOIL_X
        self.config.RECOIL_Y = config.RECOIL_Y
        self.config.MAX_OFFSET = config.MAX_OFFSET
        self.config.RECOIL_RECOVER = config.RECOIL_RECOVER

    def calculate_aim(self, target):
        if target is not None:
            x, y = target

            # Calculate x and y speed
            x *= self.config.SPEED
            y *= self.config.SPEED * self.config.Y_SPEED

            """# Apply smoothing with the previous x and y value
            x = (1 - self.config.SMOOTHNESS) * self.previous_x + self.config.SMOOTHNESS * x
            y = (1 - self.config.SMOOTHNESS) * self.previous_y + self.config.SMOOTHNESS * y"""

            # Store the calculated values for next calculation
            self.previous_x, self.previous_y = (x, y)
            # Apply x and y to the move variables
            self.move_x, self.move_y = (x, y)
            print(f"({self.move_x}, {self.move_y})")

    def apply_recoil(self, delta_time):
        if delta_time != 0:
            # Mode move just applies configured movement to the move values
            if self.config.RECOIL_MODE == "move" and win32api.GetAsyncKeyState(0x01) < 0:
                self.move_x += self.config.RECOIL_X * delta_time
                self.move_y += self.config.RECOIL_Y * delta_time
            # Mode offset moves the camera upward, so it aims below target
            elif self.config.RECOIL_MODE == "offset":
                # Add RECOIL_Y to the offset when mouse1 is down
                if win32api.GetAsyncKeyState(0x01) < 0:
                    if self.RECOIL_OFFSET < self.config.MAX_OFFSET:
                        self.RECOIL_OFFSET += self.config.RECOIL_Y * delta_time
                        if self.RECOIL_OFFSET > self.config.MAX_OFFSET:
                            self.RECOIL_OFFSET = self.config.MAX_OFFSET
                # Start resetting the offset bit by bit if mouse1 is not down
                else:
                    if self.RECOIL_OFFSET > 0:
                        self.RECOIL_OFFSET -= self.config.RECOIL_RECOVER * delta_time
                        if self.RECOIL_OFFSET < 0:
                            self.RECOIL_OFFSET = 0
        else:
            # Reset recoil offset if recoil is off
            self.RECOIL_OFFSET = 0
