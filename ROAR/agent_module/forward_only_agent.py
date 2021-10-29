from collections import deque

from ROAR.agent_module.agent import Agent
from ROAR.utilities_module.data_structures_models import SensorsData
from ROAR.utilities_module.vehicle_models import Vehicle, VehicleControl
from ROAR.configurations.configuration import Configuration as AgentConfig
from ROAR.control_module.pid_controller import PIDController
import cv2
import numpy as np


class ForwardOnlyAgent(Agent):
    def __init__(self, vehicle: Vehicle, agent_settings: AgentConfig, **kwargs):
        super().__init__(vehicle, agent_settings, **kwargs)
        self._error_buffer = deque(maxlen=10)
        self._dt = 0.03

    def run_step(self, sensors_data: SensorsData, vehicle: Vehicle) -> VehicleControl:
        super().run_step(sensors_data=sensors_data, vehicle=vehicle)

        self.logger.info(self.vehicle.get_speed(self.vehicle))
        throttle = 0.2
        throttle = self.calculate_throttle(20)



        return VehicleControl(throttle=throttle, steering=0)

    def calculate_throttle(self, target_speed):
        current_speed = self.vehicle.get_speed(self.vehicle)
        k_p, k_d, k_i = 0.1, 0.1, 0
        error = target_speed - current_speed
        print("current speed = " + str(current_speed) + " ; error = " + str(error))

        self._error_buffer.append(error)

        if len(self._error_buffer) >= 2:
            # print(self._error_buffer[-1], self._error_buffer[-2])
            _de = (self._error_buffer[-2] - self._error_buffer[-1]) / self._dt
            _ie = sum(self._error_buffer) * self._dt
        else:
            _de = 0.0
            _ie = 0.0
        output = float(np.clip((k_p * error) + (k_d * _de) + (k_i * _ie), 0,
                               0.3))
        # self.logger.debug(f"curr_speed: {round(current_speed, 2)} | kp: {round(k_p, 2)} | kd: {k_d} | ki = {k_i} | "
        #       f"err = {round(error, 2)} | de = {round(_de, 2)} | ie = {round(_ie, 2)}")
        # f"self._error_buffer[-1] {self._error_buffer[-1]} | self._error_buffer[-2] = {self._error_buffer[-2]}")
        print("output=" + str(output))
        return output