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
import time
import os

class FlowAgent(Agent):
    def __init__(self, vehicle: Vehicle, agent_settings: AgentConfig, **kwargs):
        super().__init__(vehicle, agent_settings, **kwargs)
        self.agent_settings.save_sensor_data = True
        super().__init__(vehicle, agent_settings, **kwargs)
        self.logger = logging.getLogger("Recording Agent")
        self._error_buffer = deque(maxlen=10)
        self.brake_pid_config = kwargs.get("brake_config", "")
        self.pid_controller = FlowPIDController(agent=self, steering_boundary=(-1, 1), throttle_boundary=(-0.5, 1))


        #real dt
        # Solved: update dt in get_current_data()
        self._dt = 0.05
        self.target_speed = 7.2 # 10.8 # in km/h
        # self.kwargs.__setitem__("target_speed", self.target_speed)
        self.break_state = False
        self.vehicle = vehicle
        self.vehicle_control = VehicleControl()
        self.time_counter = 0
        self.current_data_list = []
        self.data_file_path = ""
        self.time_start = time.time()
        self.write_meta_data()
        self.done = False
        self.t_b = time.time()
        self.can_brake = False
        self.prev_time = 0
        self.recv_time = 0

    def run_step(self, sensors_data: SensorsData, vehicle: Vehicle) -> VehicleControl:
        super(FlowAgent,self).run_step(sensors_data=sensors_data, vehicle=vehicle)
        self.time_counter += 1
        is_brake = False
        if (self.time_counter % 20 == 0):
            self.write_current_data()
            self.current_data_list = []
        if self.vehicle.get_speed(self.vehicle) >= self.target_speed and not self.done:
            self.logger.info("Start braking")
            self.can_brake = True
            self.t_b = time.time()
            self.done = True
        if self.can_brake:
            t_c = time.time()
            if (t_c - self.t_b >= 3):
                is_brake = True
                self.target_speed = 0
        self.recv_time = self.vehicle.recv_time
        if (self.recv_time != self.prev_time):
            self._dt = self.recv_time - self.prev_time
        # if self._dt == 0:
        #     self._dt = 0.0001
            if (self.prev_time == 0):
                self._dt = 0
            self.vehicle_control = self.pid_controller.run_in_series(is_brake=is_brake, config_b=self.brake_pid_config,
                                                                 target_speed=self.target_speed, dt = self._dt)
            self.get_current_data()
            self.prev_time = self.recv_time

        return self.vehicle_control

    def write_meta_data(self):
        # vehicle_state_file = (self.vehicle_state_output_folder_path / "flow_data2.csv").open(mode='w')
        # self.data_file_path = self.vehicle_state_output_folder_path / "flow_data" / f"{datetime.now().strftime('%m-%d-%H:%M:%S')}.csv"
        self.data_file_path = self.output_folder_path / "flow_data" / f"{datetime.now().strftime('%m-%d-%H:%M:%S')}.csv"
        directory = os.path.dirname(self.data_file_path)
        try:
            os.stat(directory)
        except:
            os.mkdir(directory)
        vehicle_state_file = (self.data_file_path).open('w')
        vehicle_state_file.write("t,prev_t,dt,_dt_sum,de,vx,vy,vz,ax,ay,az,x,y,z,v_current,v_ref,throttle_computer,throttle_vehicle,kp,ki,kd\n")
        vehicle_state_file.close()

    def get_current_data(self):
        t = time.time()
        vx = self.vehicle.velocity.x
        vy = self.vehicle.velocity.y
        vz = self.vehicle.velocity.z
        x = self.vehicle.transform.location.x
        y = self.vehicle.transform.location.y
        z = self.vehicle.transform.location.z
        ax = self.vehicle.acceleration.x
        ay = self.vehicle.acceleration.y
        az = self.vehicle.acceleration.z
        v_current = self.vehicle.get_speed(self.vehicle) / 3.6
        v_ref = self.target_speed / 3.6
        throttle_computer = self.vehicle_control.get_throttle()
        throttle_vehicle = self.vehicle.throttle
        controller = self.pid_controller.long_pid_controller
        de = controller.de
        dt_sum = controller.dt_sum
        kp = controller.kp * 3.6
        ki = controller.ki * 3.6
        kd = controller.kd * 3.6
        # Tadd, _de, dt,previous_time
        self.current_data_list.append([self.recv_time, self.prev_time, self._dt, dt_sum,de,vx, vy, vz, ax, ay, az, x, y, z, v_current, v_ref, throttle_computer,throttle_vehicle, kp, ki, kd])

    def write_current_data(self):
        vehicle_state_file = (self.data_file_path).open(mode='a+')
        for d in self.current_data_list:
            vehicle_state_file.write(f"{d[0]},{d[1]},{d[2]},{d[3]},{d[4]},{d[5]},{d[6]},{d[7]},{d[8]},{d[9]},{d[10]},{d[11]},"
                                     f"{d[12]},{d[13]},{d[14]},{d[15]},{d[16]},{d[17]},{d[18]}, {d[19]},{d[20]}\n")
        vehicle_state_file.close()
