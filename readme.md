# Robot Open Autonomous Racing (ROAR) + FLOW



please using:

```
git clone --recursive https://github.com/XiangyuZhou-Berkeley/ROAR.git
```

```
git checkout test
```

Test branch is the branch we implement FLOW

Remember to change [ROAR_iOS](https://github.com/wuxiaohua1011/ROAR_iOS/tree/81ee4ea30c32e62bd18a3da9213778a7113a5c83)/[configurations](https://github.com/wuxiaohua1011/ROAR_iOS/tree/81ee4ea30c32e62bd18a3da9213778a7113a5c83/configurations)/**ios_config.json** , change iOS_ip_addr, max_throttle and steering_offset

Currently finished:

1. create a new agent to record raw data of x,y,z,vx,vy,vz and kp ki kd, throttle. See flow_agent.py and flow_pid_controller.py

2. building an acclerating and braking for pid, see [ROAR](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test)/[ROAR](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test/ROAR)/[configurations](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test/ROAR/configurations)/[carla](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test/ROAR/configurations/carla)/**brake_pid.json**  

   and [ROAR](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test)/[ROAR](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test/ROAR)/[configurations](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test/ROAR/configurations)/[carla](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test/ROAR/configurations/carla)/**carla_pid_config.json** 
