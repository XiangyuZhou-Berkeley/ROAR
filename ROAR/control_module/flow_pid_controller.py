from matplotlib.pyplot import get
from pydantic import BaseModel, Field
from ROAR.control_module.controller import Controller
from ROAR.utilities_module.vehicle_models import VehicleControl, Vehicle

from ROAR.utilities_module.data_structures_models import Transform, Location
from collections import deque
import numpy as np
import math
import logging
from ROAR.agent_module.agent import Agent
from typing import Tuple
import json
from pathlib import Path


class FlowPIDController(Controller):
    def __init__(self, agent, steering_boundary: Tuple[float, float],
                 throttle_boundary: Tuple[float, float], **kwargs):
        super().__init__(agent, **kwargs)
        self.max_speed = self.agent.agent_settings.max_speed
        self.throttle_boundary = throttle_boundary
        self.steering_boundary = steering_boundary
        self.config = json.load(Path(agent.agent_settings.pid_config_file_path).open(mode='r'))
        self.long_pid_controller = LongPIDController(agent=agent,
                                                     throttle_boundary=throttle_boundary,
                                                     max_speed=self.max_speed,
                                                     config=self.config["longitudinal_controller"])
        self.lat_pid_controller = LatPIDController(
            agent=agent,
            config=self.config["latitudinal_controller"],
            steering_boundary=steering_boundary
        )
        self.logger = logging.getLogger(__name__)

    def run_in_series(self, is_brake, config_b, **kwargs) -> VehicleControl:
        config_b = json.load(Path(config_b).open(mode='r'))
        config_b = config_b["longitudinal_controller"]
        throttle = self.long_pid_controller.run_in_series(is_brake, config_b,
                                                          target_speed=kwargs.get("target_speed", self.max_speed),
                                                          dt=kwargs.get("dt"))
        # steering = self.lat_pid_controller.run_in_series()
        return VehicleControl(throttle=throttle, steering=0)
        # return VehicleControl(throttle=0.08, steering=0)

    @staticmethod
    def find_k_values(vehicle: Vehicle, config: dict) -> np.array:
        current_speed = Vehicle.get_speed(vehicle=vehicle)
        k_p, k_d, k_i = 1, 0, 0
        for speed_upper_bound, kvalues in config.items():
            speed_upper_bound = float(speed_upper_bound)
            if current_speed < speed_upper_bound:
                k_p, k_d, k_i = kvalues["Kp"], kvalues["Kd"], kvalues["Ki"]
                break
        return np.array([k_p, k_d, k_i])


class LongPIDController(Controller):
    def __init__(self, agent, config: dict, throttle_boundary: Tuple[float, float], max_speed: float,
                 dt: float = 0.05, **kwargs):
        super().__init__(agent, **kwargs)
        self.config = config
        self.max_speed = max_speed
        self.throttle_boundary = throttle_boundary
        # TODO: change deque size (increase)
        self._buffer_size = 50
        self._error_buffer = deque(maxlen=self._buffer_size)
        # add time buffer, mapping to error
        self._time_buffer = deque(maxlen=self._buffer_size)
        self.kp = 0
        self.ki = 0
        self.kd = 0
        self.de = 0
        self._dt = dt
        # we need to use error[-1] - error[-_nframe] / dt to get _de
        self._nframe = 5
        self.dt_sum = 0
        assert (self._nframe < self._buffer_size)

    def run_in_series(self, is_brake, config_b, **kwargs) -> float:
        target_speed = min(self.max_speed, kwargs.get("target_speed", self.max_speed))
        self._dt = kwargs.get("dt", self._dt)

        current_speed = Vehicle.get_speed(self.agent.vehicle)

        if is_brake == False:
            k_p, k_d, k_i = FlowPIDController.find_k_values(vehicle=self.agent.vehicle, config=self.config)
        else:
            k_p, k_d, k_i = FlowPIDController.find_k_values(vehicle=self.agent.vehicle, config=config_b)

        self.kp = k_p
        self.kd = k_d
        self.ki = k_i

        error = target_speed - current_speed
        # print("Error speed: " + str(error))
        # print("Target speed: " + str(target_speed))
        # print("kp kd ki = " + str(k_p) + " " + str(k_d))

        self._error_buffer.append(error)
        print(self._dt)
        self._time_buffer.append(self._dt)

        if len(self._error_buffer) >= self._nframe:
            # print(self._error_buffer[-1], self._error_buffer[-2])
            # TODO:also add error and _de to the table; repeat the experiment
            dt_sum = 0
            for i in range(1, self._nframe + 1):
                dt_sum += self._time_buffer[-i]
            self.dt_sum = dt_sum
            _de = (self._error_buffer[-self._nframe] - self._error_buffer[-1]) / dt_sum
            _ie = sum(self._error_buffer) * self._dt
            # temporaraily remove de's constraint '
            # if _de != 0 and abs(_de * k_d) < 0.3:
            #     self.de = _de
            self.de = _de
        else:
            _de = 0.0
            _ie = 0.0
        output = float(np.clip((k_p * error) + (k_d * self.de) + (k_i * _ie), self.throttle_boundary[0],
                               self.throttle_boundary[1]))
        # print(str(k_d * self.de))
        # self.logger.debug(f"curr_speed: {round(current_speed, 2)} | kp: {round(k_p, 2)} | kd: {k_d} | ki = {k_i} | "
        #       f"err = {round(error, 2)} | de = {round(_de, 2)} | ie = {round(_ie, 2)}")
        # f"self._error_buffer[-1] {self._error_buffer[-1]} | self._error_buffer[-2] = {self._error_buffer[-2]}")
        return output


class LatPIDController(Controller):
    def __init__(self, agent, config: dict, steering_boundary: Tuple[float, float],
                 dt: float = 0.03, **kwargs):
        super().__init__(agent, **kwargs)
        self.config = config
        self.steering_boundary = steering_boundary
        self._error_buffer = deque(maxlen=10)
        self._dt = dt

    def run_in_series(self, **kwargs) -> float:
        """
        Calculates a vector that represent where you are going.
        Args:
            next_waypoint ():
            **kwargs ():
        Returns:
            lat_control
        """
        # calculate a vector that represent where you are going
        v_begin = self.agent.vehicle.transform.location.to_array()
        direction_vector = np.array([-np.sin(np.deg2rad(self.agent.vehicle.transform.rotation.yaw)),
                                     0,
                                     -np.cos(np.deg2rad(self.agent.vehicle.transform.rotation.yaw))])

        v_end = v_begin + direction_vector

        v_vec = np.array([(v_end[0] - v_begin[0]), 0, (v_end[2] - v_begin[2])])
        # calculate error projection
        w_vec = np.array(
            [
                0,  # TODO: temp set the diff to 0. FLOW test do not need the steering
                0,
                0,
            ]
        )

        v_vec_normed = v_vec / np.linalg.norm(v_vec)
        w_vec_normed = w_vec / np.linalg.norm(w_vec)

        error = np.arccos(v_vec_normed @ w_vec_normed.T)
        _cross = np.cross(v_vec_normed, w_vec_normed)

        if _cross[1] > 0:
            error *= -1

        self._error_buffer.append(error)
        if len(self._error_buffer) >= 2:
            _de = (self._error_buffer[-1] - self._error_buffer[-2]) / self._dt
            _ie = sum(self._error_buffer) * self._dt
        else:
            _de = 0.0
            _ie = 0.0

        k_p, k_d, k_i = FlowPIDController.find_k_values(config=self.config, vehicle=self.agent.vehicle)

        lat_control = float(
            np.clip((k_p * error) + (k_d * _de) + (k_i * _ie), self.steering_boundary[0], self.steering_boundary[1])
        )

        return lat_control