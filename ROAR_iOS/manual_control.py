from pygame import *
import logging
import pygame
from ROAR.utilities_module.vehicle_models import VehicleControl
import numpy as np
from typing import Tuple
from ROAR_iOS.config_model import iOSConfig
import os, sys


class ManualControl:
    def __init__(self, throttle_increment=0.05, steering_increment=0.05,
                 ios_config: iOSConfig = iOSConfig):
        self.logger = logging.getLogger(__name__)
        self.ios_config = ios_config
        self._steering_increment = steering_increment
        self._throttle_increment = throttle_increment
        self.max_reverse_throttle = ios_config.max_reverse_throttle
        self.max_forward_throttle = ios_config.max_forward_throttle
        self.max_steering = ios_config.max_steering

        self.steering_offset = ios_config.steering_offset

        self.gear_throttle_step = 0.05
        self.gear_steering_step = 0.01

        self.vertical_view_offset = 200

        self.left_trigger = 0
        self.right_trigger = 0
        self.use_joystick = False
        try:
            pygame.joystick.init()
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.logger.info(f"Joystick [{self.joystick.get_name()}] detected, Using Joytick")
            self.use_joystick = True
        except Exception as e:
            self.logger.info("No joystick detected. Plz use your keyboard instead")

        self.steering = 0.0
        self.throttle = 0.0

        self.last_switch_press_time = time.get_ticks()
        self.logger.debug("Keyboard Control Initiated")

    def parse_events(self, clock: pygame.time.Clock):
        """
        parse a keystoke event
        Args:
            clock: pygame clock

        Returns:
            Tuple bool, and vehicle control
            boolean states whether quit is pressed. VehicleControl by default has throttle = 0, steering =
        """
        events = pygame.event.get()
        key_pressed = pygame.key.get_pressed()
        for event in events:
            if event.type == pygame.QUIT or key_pressed[K_q] or key_pressed[K_ESCAPE]:
                return False, VehicleControl(), False
            if event.type == pygame.JOYHATMOTION:
                hori, vert = self.joystick.get_hat(0)
                if vert > 0:
                    self.max_forward_throttle = np.clip(self.max_forward_throttle + self.gear_throttle_step, 0, 1)
                    self.ios_config.max_forward_throttle = self.max_forward_throttle
                elif vert < 0:
                    self.max_forward_throttle = np.clip(self.max_forward_throttle - self.gear_throttle_step, 0, 1)
                    self.ios_config.max_forward_throttle = self.max_forward_throttle

                if hori > 0:
                    self.steering_offset = np.clip(self.steering_offset + self.gear_steering_step, -1, 1)
                    self.ios_config.steering_offset = self.steering_offset

                elif hori < 0:
                    self.steering_offset = np.clip(self.steering_offset - self.gear_steering_step, -1, 1)
                    self.ios_config.steering_offset = self.steering_offset

        is_brake = False
        is_switch_auto_pressed = False
        self.throttle, self.steering = self._parse_vehicle_keys(key_pressed)

        if self.use_joystick:
            self.throttle, self.steering = self._parse_joystick()
        else:
            self.throttle, self.steering = self._parse_vehicle_keys(key_pressed)
            if key_pressed[K_UP]:
                self.vertical_view_offset = min(500, self.vertical_view_offset + 5)
            elif key_pressed[K_DOWN]:
                self.vertical_view_offset = max(0, self.vertical_view_offset - 5)
            if key_pressed[K_SPACE]:
                is_brake = True
        if key_pressed[K_m] and time.get_ticks() - self.last_switch_press_time > 100:
            is_switch_auto_pressed = True
            self.last_switch_press_time = time.get_ticks()

        control = VehicleControl(throttle=np.clip(self.throttle, self.max_reverse_throttle,
                                                  self.max_forward_throttle),
                                 steering=np.clip(self.steering, -self.max_steering, self.max_steering),
                                 brake=is_brake)
        return True, control, is_switch_auto_pressed

    def _parse_joystick(self) -> Tuple[float, float]:
        # code to test which axis is your controller using
        # vals = [self.joystick.get_axis(i) for i in range(self.joystick.get_numaxes())]
        if sys.platform == "win32":
            trigger_val: float = self.joystick.get_axis(2)
            right_stick_hori_val = self.joystick.get_axis(4)
            left_stick_vert_val = self.joystick.get_axis(3)
            throttle = -trigger_val
            steering = right_stick_hori_val
            if left_stick_vert_val > 0.5:
                self.vertical_view_offset = min(500, self.vertical_view_offset + 5)
            elif left_stick_vert_val < -0.5:
                self.vertical_view_offset = max(0, self.vertical_view_offset - 5)
            return throttle, steering
        else:
            left_trigger_val: float = self.joystick.get_axis(5)
            right_trigger_val: float = self.joystick.get_axis(4)
            left_joystick_vertical_val = self.joystick.get_axis(1)
            left_joystick_horizontal_val = self.joystick.get_axis(0)
            right_joystick_vertical_val = self.joystick.get_axis(3)
            right_joystick_horizontal_val = self.joystick.get_axis(2)

            # post processing on raw values
            left_trigger_val = (1 + left_trigger_val) / 2
            right_trigger_val = (1 + right_trigger_val) / 2
            throttle = left_trigger_val + (-1 * right_trigger_val)
            steering = right_joystick_horizontal_val
            left_joystick_vertical_val = -1 * left_joystick_vertical_val

            if left_joystick_vertical_val > 0.5:
                self.vertical_view_offset = min(500, self.vertical_view_offset + 5)
            elif left_joystick_vertical_val < -0.5:
                self.vertical_view_offset = max(0, self.vertical_view_offset - 5)
            throttle, steering = 0, 0
            return throttle, steering

    def _parse_vehicle_keys(self, keys) -> Tuple[float, float]:
        """
        Parse a single key press and set the throttle & steering
        Args:
            keys: array of keys pressed. If pressed keys[PRESSED] = 1
        Returns:
            None
        """
        if keys[K_w]:
            self.throttle = min(self.throttle + self._throttle_increment, 1)

        elif keys[K_s]:
            self.throttle = max(self.throttle - self._throttle_increment, -1)
        else:
            self.throttle = 0

        if keys[K_a]:
            self.steering = max(self.steering - self._steering_increment, -1)

        elif keys[K_d]:
            self.steering = min(self.steering + self._steering_increment, 1)
        else:
            self.steering = 0

        if keys[K_LEFT]:
            self.steering_offset = np.clip(self.steering_offset - self.gear_steering_step, -1, 1)
            self.ios_config.steering_offset = self.steering_offset
        elif keys[K_RIGHT]:
            self.steering_offset = np.clip(self.steering_offset + self.gear_steering_step, -1, 1)
            self.ios_config.steering_offset = self.steering_offset
        return round(self.throttle, 5), round(self.steering, 5)
