import numpy as np
import torch
import torch.nn as nn

sqrt3 = np.sqrt(3)
sqrt5 = np.sqrt(5)


class TimeNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(2, 1000),
                                nn.LeakyReLU(),
                                nn.Linear(1000, 200),
                                nn.LeakyReLU(),
                                nn.Linear(200, 1),
                                nn.ReLU())

    def forward(self, x):
        return self.fc(x)


def wind_mouse(start_x, start_y, dest_x, dest_y, G_0=9, W_0=3, M_0=15, D_0=12, move_mouse=lambda x, y, pred_time: None,
               time_model=None):
    """
    WindMouse algorithm. Calls the move_mouse kwarg with each new step.
    Released under the terms of the GPLv3 license.
    G_0 - magnitude of the gravitational fornce
    W_0 - magnitude of the wind force fluctuations
    M_0 - maximum step size (velocity clip threshold)
    D_0 - distance where wind behavior changes from random to damped
    """
    current_x, current_y = start_x, start_y
    pred_time = 0
    v_x = v_y = W_x = W_y = 0
    while (dist := np.hypot(dest_x - start_x, dest_y - start_y)) >= 1:
        W_mag = min(W_0, dist)
        if dist >= D_0:
            W_x = W_x / sqrt3 + (2 * np.random.random() - 1) * W_mag / sqrt5
            W_y = W_y / sqrt3 + (2 * np.random.random() - 1) * W_mag / sqrt5
        else:
            W_x /= sqrt3
            W_y /= sqrt3
            if M_0 < 3:
                M_0 = np.random.random() * 3 + 3
            else:
                M_0 /= sqrt5
        v_x += W_x + G_0 * (dest_x - start_x) / dist
        v_y += W_y + G_0 * (dest_y - start_y) / dist
        v_mag = np.hypot(v_x, v_y)
        if v_mag > M_0:
            v_clip = M_0 / 2 + np.random.random() * M_0 / 2
            v_x = (v_x / v_mag) * v_clip
            v_y = (v_y / v_mag) * v_clip
        start_x += v_x
        start_y += v_y
        move_x = int(np.round(start_x))
        move_y = int(np.round(start_y))

        if time_model:
            pred_time = time_model(torch.from_numpy(np.array([current_x, current_y], dtype=np.float32)))
            pred_time = pred_time.cpu().detach().numpy()[0]

        if current_x != move_x or current_y != move_y:
            # This should wait for the mouse polling interval
            move_mouse(current_x := move_x, current_y := move_y, pred_time=pred_time)

    return current_x, current_y, pred_time


def wind_mouse_points(x1, y1, x2, y2, time_model):
    points = []
    wind_mouse(x1, y1, x2, y2, move_mouse=lambda x, y, pred_time: points.append([x, y, pred_time]), time_model=time_model)
    points = np.asarray(points)
    return points
