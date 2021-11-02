from collections import deque

from ROAR.agent_module.agent import Agent
from ROAR.utilities_module.data_structures_models import SensorsData
from ROAR.utilities_module.vehicle_models import Vehicle, VehicleControl
from ROAR.configurations.configuration import Configuration as AgentConfig
from ROAR.control_module.flow_pid_controller import FlowPIDController
import cv2
import numpy as np
import logging
from datetime import datetime

class FlowAgent(Agent):
    def __init__(self, vehicle: Vehicle, agent_settings: AgentConfig, **kwargs):
        super().__init__(vehicle, agent_settings, **kwargs)
        self.agent_settings.save_sensor_data = True
        super().__init__(vehicle, agent_settings, **kwargs)
        self.logger = logging.getLogger("Recording Agent")
        self._error_buffer = deque(maxlen=10)

        self.pid_controller = FlowPIDController(agent=self, steering_boundary=(-1, 1), throttle_boundary=(0, 1))
        self._dt = 0.03
        self.target_speed = 18 # in km/h
        # self.kwargs.__setitem__("target_speed", self.target_speed)
        self.break_state = False
        self.vehicle = vehicle
        self.write_meta_data()
        self.vehicle_control = VehicleControl()

    def run_step(self, sensors_data: SensorsData, vehicle: Vehicle) -> VehicleControl:
        super(FlowAgent,self).run_step(sensors_data=sensors_data, vehicle=vehicle)

        if self.vehicle.get_speed(self.vehicle) >= self.target_speed:
            self.target_speed = 0
            self.logger.info("Start breaking")

        self.vehicle_control = self.pid_controller.run_in_series(target_speed=self.target_speed)
        return self.vehicle_control

    def write_meta_data(self):
        vehicle_state_file = (self.vehicle_state_output_folder_path / "flow_data.csv").open(mode='w')
        vehicle_state_file.write("t,vx,vy,vz,v_ref,x,y,z,throttle,kp,ki,kd\n")
        vehicle_state_file.close()

    def write_current_data(self):
        vehicle_state_file = (self.vehicle_state_output_folder_path / "flow_data.csv").open(mode='a+')
        t = datetime.now().time()
        vx = self.vehicle.velocity.x
        vy = self.vehicle.velocity.y
        vz = self.vehicle.velocity.z
        x = self.vehicle.transform.location.x
        y = self.vehicle.transform.location.y
        z = self.vehicle.transform.location.z
        v_ref = self.target_speed
        throttle = self.vehicle_control.get_throttle()
        controller = self.pid_controller.long_pid_controller
        kp = controller.kp
        ki = controller.ki
        kd = controller.kd
        vehicle_state_file.write(f"{t},{vx},{vy},{vz},{v_ref},{x},{y},{z},{throttle},{kp},{ki},{kd}\n")
        vehicle_state_file.close()