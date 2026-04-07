# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


"""
Thorlabs Kinesis Piezo
from BPC3XX Pythonnet Example

"""

import time
import clr

clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericPiezoCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.Benchtop.PiezoCLI.dll")
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericPiezoCLI import *
from Thorlabs.MotionControl.GenericPiezoCLI import Piezo
from Thorlabs.MotionControl.GenericPiezoCLI import DeviceUnits
from Thorlabs.MotionControl.Benchtop.PiezoCLI import *
from System import Decimal  # necessary for real world units


class KinesisPiezo:

    def __init__(self, serial_no="71824990", logg=None, config=None):
        self.logg = logg or self.setup_logging()
        self.config = config or self.load_configs()
        # self.piezo_serial = serial_no
        self.piezo_serial = self.config.configs["Sample Stages"]["Piezo Stage"]["Thorlabs"]["Serial"]
        self.piezo, self.channels, self.vmax = self._initialize_piezo(self.piezo_serial)

    @staticmethod
    def setup_logging():
        import logging
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
        return logging

    @staticmethod
    def load_configs():
        config_file = input("Enter configuration file directory: ")
        from miao.utilities import configurations
        cfg = configurations.MicroscopeConfiguration(fd=config_file)
        return cfg

    def _initialize_piezo(self, sn):
        try:
            DeviceManagerCLI.BuildDeviceList()
            device = BenchtopPiezo.CreateBenchtopPiezo(sn)
            device.Connect(sn)

            channels = []
            vmax = []
            for i in range(3):
                # Retrieve channel for the device. Can call multiple times for (X) channels.
                channel = device.GetChannel(i + 1)

                # Ensure that the device settings have been initialized.
                if not channel.IsSettingsInitialized():
                    channel.WaitForSettingsInitialized(10000)  # 10 second timeout
                    assert channel.IsSettingsInitialized() is True

                # Start polling and enable.
                channel.StartPolling(250)  # 250ms polling rate
                time.sleep(0.25)
                channel.EnableDevice()
                time.sleep(0.25)  # Wait for device to enable

                # Get Device Information and display description.
                device_info = channel.GetDeviceInfo()
                print(device_info.Description)

                # Load any configuration settings needed by the controller/stage.
                motor_config = channel.GetPiezoConfiguration(channel.DeviceID)
                time.sleep(0.25)

                currentDeviceSettings = channel.PiezoDeviceSettings

                # Get Max voltage that is accessible.
                vm = float(str(channel.GetMaxOutputVoltage()).replace(',', '.'))
                vmax.append(vm)

                channels.append(channel)
                self.logg.info(f"Piezo Channel {i + 1} set")
            return device, channels, vmax
        except Exception as e:
            self.logg.error(f"Error Initializing Piezo {sn}: {e}")
            return None, None

    def read_position(self, ch):
        newVolts = self.channels[ch].GetOutputVoltage()
        newMicron = float(str(newVolts).replace(',', '.'))/(self.vmax[ch]/20)
        return newMicron

    def move_position(self, ch, pos):
        maxVolts = self.vmax[ch]
        voltage = pos*(self.vmax[ch]/20) #Convertion from position to volt
        if (voltage >= 0) & (voltage <= maxVolts):
            # Update voltage if required using real world methods.
            self.channels[ch].SetOutputVoltage(Decimal(voltage))

    def close(self):
        for channel in self.channels:
            channel.StopPolling()
        self.piezo.Disconnect()

