import time

import numpy as np
import sys, os
from pathlib import Path
import time

sys.path.append(Path(os.getcwd()).parent.as_posix())
from ROAR_iOS.udp_receiver import UDPStreamer
from ROAR.utilities_module.data_structures_models import Transform, Vector3D
from collections import deque


class VehicleStateStreamer(UDPStreamer):
    def __init__(self, max_vel_buffer=5, **kwargs):
        super().__init__(**kwargs)
        self.transform = Transform()
        self.velocity = Vector3D()
        self.acceleration = Vector3D()
        self.gyro = Vector3D()

        self.max_vel_buffer = max_vel_buffer
        self.vx_deque = deque(maxlen=self.max_vel_buffer)
        self.vy_deque = deque(maxlen=self.max_vel_buffer)
        self.vz_deque = deque(maxlen=self.max_vel_buffer)

        self.recv_time: float = 0
        self.throttle: float = 0
    def run_in_series(self, **kwargs):
        try:
            data = self.recv()
            if data is None:
                return
            d = [float(s) for s in data.decode('utf-8').split(",")]
            # d = np.frombuffer(data, dtype=np.float32)
            self.transform.location.x = d[0]
            self.transform.location.y = d[1]
            self.transform.location.z = d[2]
            self.transform.rotation.roll = d[3]
            self.transform.rotation.pitch = d[4]
            self.transform.rotation.yaw = d[5]

            self.vx_deque.append(d[6])
            self.vy_deque.append(d[7])
            self.vz_deque.append(d[8])

            self.velocity.x = np.average(self.vx_deque) #d[6] #np.average(self.vx_deque)
            self.velocity.y = np.average(self.vy_deque) #d[7]#np.average(self.vy_deque)
            self.velocity.z = np.average(self.vz_deque) #d[8]#np.average(self.vz_deque)

            # print("x" + str(self.velocity.x))
            # print("y" + str(self.velocity.y))
            # print("z" + str(self.velocity.z))
            self.acceleration.x = d[9]
            self.acceleration.y = d[10]
            self.acceleration.z = d[11]
            self.gyro.x = d[12]
            self.gyro.y = d[13]
            self.gyro.z = d[14]

            self.recv_time = d[15]
            self.throttle = d[16]
        except Exception as e:
            self.logger.error(e)


if __name__ == '__main__':
    streamer = VehicleStateStreamer(ios_address="10.0.0.26",
                                    port=8003,
                                    name="VehicleStateStreamer",
                                    update_interval=0.025,
                                    threaded=True)
    while True:
        streamer.run_in_series()
        print(streamer.transform, streamer.velocity)
