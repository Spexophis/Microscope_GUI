import struct
import time

import numpy as np
import serial


class Boards:

    def __init__(self, logg=None, config=None):
        self.logg = logg or self.setup_logging()
        self.config = config or self.load_configs()
        self.com_port = {"nucleo_digital": "COM5", "nucleo_analog": "COM4"}
        self.ser_dig = serial.Serial(self.com_port["nucleo_digital"], 115200, timeout=1)
        self.ser_ang = serial.Serial(self.com_port["nucleo_analog"], 115200, timeout=1)

        self.target = {
            'DAC1': 0,
            'DAC2': 1,
            'PA0': 2,
            'PA1': 3,
            'PB10': 4,
            "switch_on": 5,
            "switch_off": 6,
            "switch_off_clock": 7
        }

        self.digital_length = 16000  # must match firmware
        self.signal_length = 16000  # must match firmware

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

    def close(self):
        self.ser_dig.close()
        self.ser_ang.close()

    def send_sequence(self, ser, target_name, samples, is_dac):
        """Send one array to the board."""
        targ = self.target[target_name]
        # start byte
        pkt = bytearray([0xA5, targ])

        if is_dac:
            # clamp & pack 16-bit big-endian
            for v in samples:
                v = max(0, min(4095, int(v)))
                pkt += struct.pack('>H', v)
        else:
            # pack 8-bit 0/1
            for v in samples:
                pkt.append(1 if v else 0)
        ser.write(pkt)
        ser.flush()

    def set_galvo_position(self, pos, indices=None):
        try:
            self.send_sequence(self.ser_ang, 'DAC1', [pos[0]] * self.signal_length, is_dac=True)
            time.sleep(5)
            self.send_sequence(self.ser_ang, 'DAC2', [pos[1]] * self.signal_length, is_dac=True)
            time.sleep(5)
        except RuntimeError as e:
            self.logg.error("GPIO channels writing error: %s", e)

    def write_digital_sequences(self, digital_sequences, indices=None):
        if isinstance(digital_sequences, np.ndarray):
            digital_sequences = digital_sequences.tolist()
        try:
            dfn = self.signal_length - len(digital_sequences[0])
            if dfn > 0:
                temp = [digital_sequences[0][-1]] * dfn
                pa0 = digital_sequences[0]
                pa0.extend(temp)
            else:
                pa0 = digital_sequences[0][:self.signal_length]
            self.send_sequence(self.ser_dig, 'PA0', pa0, is_dac=False)
            time.sleep(0.2)
            dfn = self.signal_length - len(digital_sequences[1])
            if dfn > 0:
                temp = [digital_sequences[1][-1]] * dfn
                pa1 = digital_sequences[1]
                pa1.extend(temp)
            else:
                pa1 = digital_sequences[1][:self.signal_length]
            self.send_sequence(self.ser_dig, 'PA1', pa1, is_dac=False)
            time.sleep(0.2)
            dfn = self.signal_length - len(digital_sequences[2])
            if dfn > 0:
                temp = [digital_sequences[2][-1]] * dfn
                pb10 = digital_sequences[2]
                pb10.extend(temp)
            else:
                pb10 = digital_sequences[2][:self.signal_length]
            self.send_sequence(self.ser_dig, 'PB10', pb10, is_dac=False)
            time.sleep(0.2)
        except RuntimeError as e:
            self.logg.error("GPIO channels writing error: %s", e)

    def write_galvo_sequences(self, galvo_sequences, indices=None):
        if isinstance(galvo_sequences, np.ndarray):
            galvo_sequences = galvo_sequences * 4096 / 3.3
            galvo_sequences = galvo_sequences.astype(np.uint16)
            galvo_sequences = galvo_sequences.tolist()
        try:
            dfn = self.signal_length - len(galvo_sequences[0])
            if dfn > 0:
                temp = [galvo_sequences[0][-1]] * dfn
                dac1 = galvo_sequences[0]
                dac1.extend(temp)
            else:
                dac1 = galvo_sequences[0][:self.signal_length]
            self.send_sequence(self.ser_ang, 'DAC1', dac1, is_dac=True)
            time.sleep(5)
            dfn = self.signal_length - len(galvo_sequences[1])
            if dfn > 0:
                temp = [galvo_sequences[1][-1]] * dfn
                dac2 = galvo_sequences[1]
                dac2.extend(temp)
            else:
                dac2 = galvo_sequences[1][:self.signal_length]
            self.send_sequence(self.ser_ang, 'DAC2', dac2, is_dac=True)
            time.sleep(5)
        except RuntimeError as e:
            self.logg.error("DAC channels writing error: %s", e)

    def write_triggers(self, galvo_sequences=None, galvo_channels=None, digital_sequences=None, digital_channels=None, finite=True):
        try:
            if digital_sequences is not None:
                self.write_digital_sequences(digital_sequences, indices=digital_channels)
            if galvo_sequences is not None:
                self.write_galvo_sequences(galvo_sequences, indices=galvo_channels)
        except RuntimeError as e:
            self.logg.error("Sequence writing error: %s", e)

    def run_triggers(self):
        self.send_sequence(self.ser_ang, 'switch_on', [0,0], is_dac=False)

    def stop_triggers(self):
        self.send_sequence(self.ser_ang, 'switch_off', [0,0], is_dac=False)
