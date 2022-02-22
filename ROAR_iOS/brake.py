from collections import deque

import numpy as np

from ROAR.utilities_module.vehicle_models import VehicleControl, Vehicle


class Brake:
    def __init__(self, kp, kd, ki, k_incline, max_brake=0.15, time_horizon=10):
        self.kp = kp
        self.kd = kd
        self.ki = ki
        self.k_incline = k_incline
        self.max_brake = max_brake
        self.error_deque = deque(maxlen=time_horizon)

    def run_step(self, control: VehicleControl, vehicle: Vehicle) -> VehicleControl:
        if control.brake:

            # velx = vehicle.velocity.x
            # velz = vehicle.velocity.z
            #
            #
            # v_vec = np.array([-np.sin(np.deg2rad(vehicle.transform.rotation.yaw)),
            #                   0,
            #                   -np.cos(np.deg2rad(vehicle.transform.rotation.yaw))])
            # w_vec = np.array([
            #     velx,
            #     0,
            #     velz
            # ])
            # v_vec_normed = v_vec / np.linalg.norm(v_vec)
            # w_vec_normed = w_vec / np.linalg.norm(w_vec)
            # forward_error = np.arccos(v_vec_normed @ w_vec_normed.T)
            # _cross = np.cross(v_vec_normed, w_vec_normed)
            # forward_error = np.rad2deg(forward_error)
            # if _cross[1] > 0:
            #     forward_error *= -1
            # forward_error = forward_error % 360
            # e = 0 - vehicle.get_speed(vehicle)
            # e = 0 if -4 < e < 4 else e
            # is_forward = True if 270 < forward_error < 360 or 0 < forward_error < 90 else False  # TODO fix this.
            e = 0 - vehicle.get_speed(vehicle)
            is_forward = vehicle.velocity.x + vehicle.velocity.z < 0

            neutral = -90
            incline = vehicle.transform.rotation.pitch - neutral
            e = e if is_forward else e * -1
            e = e * - 1 if incline > 10 else e
            self.error_deque.append(e)
            de = 0 if len(self.error_deque) < 2 else self.error_deque[-2] - self.error_deque[-1]
            ie = 0 if len(self.error_deque) < 2 else np.sum(self.error_deque)
            incline = np.clip(incline, -18, 18)
            control.throttle = np.clip(self.kp * e + self.kd * de + self.ki * ie + self.k_incline * incline,
                                       -0.1,
                                       abs(self.max_brake))
            return control
        else:
            self.error_deque.clear()
            return control
