import struct
import time

import numpy as np
import serial


class NucleoBoards:

    def __init__(self, logg=None, config=None):
        self.logg = logg or self.setup_logging()
        self.config = config or self.load_configs()
        self.com_port = "COM8"
        self.ser = serial.Serial(self.com_port, 115200, timeout=1)
        self.prescaler = 0
        self.period = 63
        self.sample_rate = 64/(self.prescaler + 1) * (self.period + 1)
        self.sequence_length = 64000  # must match firmware
        self.digital_sequences = []
        self.analog_sequences = []

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
        self.stop_triggers()
        self.ser.close()

    def send_command(self, cmd):
        self.ser.write(cmd.encode())
        reply = self.ser.read_until(b'\n')
        self.logg.info("CMD:", cmd, "| Reply:", reply)

    def send_sequence(self, seq_id, data, dtype="H"):
        packet = bytearray()
        packet += b"\xAA\x55"
        packet += struct.pack("<B", seq_id)
        packet += struct.pack("<I", len(data))
        packet += np.array(data, dtype=dtype).tobytes()
        self.ser.write(packet)
        reply = self.ser.read_until(b'\n')
        self.logg.info("SEQ:", seq_id, "| Reply:", reply)

    def set_rate(self, prescaler, period):
        self.prescaler = prescaler
        self.period = period
        self.sample_rate = 64/(self.prescaler + 1) * (self.period + 1)
        cmd = f"CLOCK {prescaler} {period}"
        self.send_command(cmd)

    def set_galvo_position(self, pos):
        ps = [int(p * 4096 / 3.3) for p in pos]
        cmd = f"DAC {ps[0]} {ps[1]}"
        self.send_command(cmd)

    def write_digital_sequences(self, digital_sequences, indices=None):
        if isinstance(digital_sequences, np.ndarray):
            digital_sequences = digital_sequences.tolist()
        if digital_sequences == self.digital_sequences:
            return
        else:
            try:
                self.digital_sequences = digital_sequences
                dfn = self.sequence_length - len(digital_sequences[0])
                if dfn > 0:
                    temp = [digital_sequences[0][-1]] * dfn
                    pa0 = digital_sequences[0]
                    pa0.extend(temp)
                else:
                    pa0 = digital_sequences[0][:self.sequence_length]
                self.send_sequence(0, pa0, dtype="B")  # Digital PA0
                time.sleep(0.1)
                dfn = self.sequence_length - len(digital_sequences[1])
                if dfn > 0:
                    temp = [digital_sequences[1][-1]] * dfn
                    pa1 = digital_sequences[1]
                    pa1.extend(temp)
                else:
                    pa1 = digital_sequences[1][:self.sequence_length]
                self.send_sequence(1, pa1, dtype="B")  # Digital PA1
                time.sleep(0.1)
                dfn = self.sequence_length - len(digital_sequences[-1])
                if dfn > 0:
                    temp = [digital_sequences[-1][-1]] * dfn
                    pa2 = digital_sequences[-1]
                    pa2.extend(temp)
                else:
                    pa2 = digital_sequences[-1][:self.sequence_length]
                self.send_sequence(2, pa2, dtype="B")  # Digital PA2
                time.sleep(0.1)
            except RuntimeError as e:
                self.logg.error("GPIO channels writing error: %s", e)     

    def write_galvo_sequences(self, galvo_sequences, indices=None):
        if isinstance(galvo_sequences, np.ndarray):
            galvo_sequences = galvo_sequences * 4096 / 3.3
            galvo_sequences = galvo_sequences.astype(np.uint16)
            galvo_sequences = galvo_sequences.tolist()
        if galvo_sequences == self.analog_sequences:
            return
        else:
            try:
                self.analog_sequences = galvo_sequences
                dfn = self.sequence_length - len(galvo_sequences[0])
                if dfn > 0:
                    temp = [galvo_sequences[0][-1]] * dfn
                    dac1 = galvo_sequences[0]
                    dac1.extend(temp)
                else:
                    dac1 = galvo_sequences[0][:self.sequence_length]
                self.send_sequence(3, dac1, dtype="H")  # DAC1
                time.sleep(0.1)
                dfn = self.sequence_length - len(galvo_sequences[1])
                if dfn > 0:
                    temp = [galvo_sequences[1][-1]] * dfn
                    dac2 = galvo_sequences[1]
                    dac2.extend(temp)
                else:
                    dac2 = galvo_sequences[1][:self.sequence_length]
                self.send_sequence(4, dac2, dtype="H")  # DAC2
                time.sleep(0.1)
            except RuntimeError as e:
                self.logg.error("DAC channels writing error: %s", e)

    def write_triggers(self, galvo_sequences=None, galvo_channels=None, digital_sequences=None, digital_channels=None, infinity=True):
        try:
            if digital_sequences is not None:
                self.write_digital_sequences(digital_sequences, indices=digital_channels)
            if galvo_sequences is not None:
                self.write_galvo_sequences(galvo_sequences, indices=galvo_channels)
        except RuntimeError as e:
            self.logg.error("Sequence writing error: %s", e)

    def run_triggers(self):
        self.send_command("START")
        time.sleep(self.sequence_length / self.sample_rate)

    def stop_triggers(self):
        self.send_command("STOP")


def same_list(lst):
    return len(set(lst)) == 1 if lst else True
