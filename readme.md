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



#### TODO

1. ` ROAR/agent_module/flow_agent.py`

   (1) TODO: real dt

2. `ROAR/control_module/flow_pid_controller.py`

   \(2) TODO: change deque size (increase)

   \(3) TODO: add time buffer, mapping to error

   (4) TODO:choose data with larger interval, also add error and _de to the table; repeat the experiment



Feb 7:

1.solved the steering bug in auto-pilot, now it can run in a straight line in --auto

2.try different kp and kd when target is 3 m/s and 2 m/s, maybe need to add ki to make it more stable.

3.the latency problem still has some effect, needs to talk about it.

TODO:

1.change the data output file name to : target, kp, ki, kd , time to make it more clear

2.change the process from one target to multiple target process.

3.change pid process();

# get additional data



To get additional data from iphone what should we change in the program:

i will explain this with an example like recv_time ( to get time from iphone as data)

## In ROAR IOS:

### [ROAR](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test)/[ROAR_iOS](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test/ROAR_iOS)/**veh_state_streamer.py**

1.

https://github.com/XiangyuZhou-Berkeley/ROAR/blob/74302a0c230c51315aba7a98649224eb42a641ba/ROAR_iOS/veh_state_streamer.py#L27

add a line intialzie the variable

2.https://github.com/XiangyuZhou-Berkeley/ROAR/blob/74302a0c230c51315aba7a98649224eb42a641ba/ROAR_iOS/veh_state_streamer.py#L61

in data package which one is recv_time

### [ROAR](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test)/[ROAR_iOS](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test/ROAR_iOS)/**ios_runner.py**

1.

https://github.com/XiangyuZhou-Berkeley/ROAR/blob/74302a0c230c51315aba7a98649224eb42a641ba/ROAR_iOS/ios_runner.py#L192

transmit this data from veh_state_streamer to Vehicle class

use convert_vehicle_from_source_to_agent(self, source) -> Vehicle  in iOS_bridge

### [ROAR](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test)/[Bridges](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test/Bridges)/**ios_bridge.py**

1.

https://github.com/XiangyuZhou-Berkeley/ROAR/blob/74302a0c230c51315aba7a98649224eb42a641ba/Bridges/ios_bridge.py#L60

get data

2. https://github.com/XiangyuZhou-Berkeley/ROAR/blob/74302a0c230c51315aba7a98649224eb42a641ba/Bridges/ios_bridge.py#L75

   transmit into vehicle class

### [ROAR](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test)/[ROAR](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test/ROAR)/[utilities_module](https://github.com/XiangyuZhou-Berkeley/ROAR/tree/test/ROAR/utilities_module)/**vehicle_models.py**

1.

https://github.com/XiangyuZhou-Berkeley/ROAR/blob/74302a0c230c51315aba7a98649224eb42a641ba/ROAR/utilities_module/vehicle_models.py#L52

intialize recv_time in vehicle class





## ROAR_XCODE

### [ROAR-IOS](https://github.com/Jerry-Ge/ROAR-IOS)/[ROAR](https://github.com/Jerry-Ge/ROAR-IOS/tree/master/ROAR)/**ControlCenter.swift**

1

https://github.com/Jerry-Ge/ROAR-IOS/blob/109b74514dd19a04729b39016d9e88080d5d6106/ROAR/ControlCenter.swift#L88

record the time and reduce length

2.

https://github.com/Jerry-Ge/ROAR-IOS/blob/109b74514dd19a04729b39016d9e88080d5d6106/ROAR/ControlCenter.swift#L118

add time and to send back to iPhone





### [ROAR-IOS](https://github.com/Jerry-Ge/ROAR-IOS)/[ROAR](https://github.com/Jerry-Ge/ROAR-IOS/tree/master/ROAR)/**utility.swift**

https://github.com/Jerry-Ge/ROAR-IOS/blob/109b74514dd19a04729b39016d9e88080d5d6106/ROAR/utility.swift#L100



https://github.com/Jerry-Ge/ROAR-IOS/blob/109b74514dd19a04729b39016d9e88080d5d6106/ROAR/utility.swift#L105





https://github.com/Jerry-Ge/ROAR-IOS/blob/109b74514dd19a04729b39016d9e88080d5d6106/ROAR/utility.swift#L117



https://github.com/Jerry-Ge/ROAR-IOS/blob/109b74514dd19a04729b39016d9e88080d5d6106/ROAR/utility.swift#L134
