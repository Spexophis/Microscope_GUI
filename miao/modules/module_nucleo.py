import struct
import time
import threading
import numpy as np
import serial


class NucleoBoards:

    def __init__(self, logg=None):
        self.logg = logg or self.setup_logging()
        self.com_port = "COM12"
        self.ser = serial.Serial(self.com_port, 115200, timeout=1)
        self.prescaler = 0
        self.period = 63
        self.sample_rate = 64e6/(self.prescaler + 1) * (self.period + 1)
        self.sequence_length = 64000  # must match firmware
        self.t = 0.1 * max((1e6 / self.sample_rate), 1)
        self.trg_thread = None
        self.infinity = False
        self.send_command("CLOCK 63 3")

    @staticmethod
    def setup_logging():
        import logging
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
        return logging

    def close(self):
        self.ser.close()

    def send_command(self, cmd):
        self.ser.write(cmd.encode())
        reply = self.ser.read_until(b'\n')
        print("CMD:", cmd, "| Reply:", reply)

    def send_sequence(self, seq_id, data, dtype="H"):
        packet = bytearray()
        packet += b"\xAA\x55"
        packet += struct.pack("<B", seq_id)
        packet += struct.pack("<I", len(data))
        packet += np.array(data, dtype=dtype).tobytes()
        self.ser.write(packet)
        reply = self.ser.read_until(b'\n')
        print("SEQ:", seq_id, "| Reply:", reply)

    def set_rate(self, prescaler, period):
        self.prescaler = prescaler
        self.period = period
        self.sample_rate = 64/(self.prescaler + 1) * (self.period + 1)
        self.t = 0.1 * max((1e6 / self.sample_rate), 1)
        cmd = f"CLOCK {prescaler} {period}"
        self.send_command(cmd)

    def set_galvo_position(self, pos):
        ps = [int(p * 4096 / 3.3) for p in pos]
        cmd = f"DAC {ps[0]} {ps[1]}"
        self.send_command(cmd)

    def write_digital_sequences(self, digital_sequences, indices=[0, 1, 2]):
        if isinstance(digital_sequences, np.ndarray):
            digital_sequences = digital_sequences.tolist()
        if len(digital_sequences) == len(indices):
            try:
                for seq, idx in zip(digital_sequences, indices):
                    dfn = self.sequence_length - len(seq)
                    if dfn > 0:
                        data = seq
                    else:
                        data = seq[:self.sequence_length]
                    self.send_sequence(idx, data, dtype="B")  # Digital PA0
                    time.sleep(0.1)
            except RuntimeError as e:
                self.logg.error("GPIO channels writing error: %s", e)
        else:
            self.logg.error("GPIO channels error")
            return

    def write_galvo_sequences(self, galvo_sequences, indices=[3, 4]):
        if isinstance(galvo_sequences, np.ndarray):
            galvo_sequences = galvo_sequences.tolist()
        if len(galvo_sequences) == len(indices):
            try:
                for seq, idx in zip(galvo_sequences, indices):
                    dfn = self.sequence_length - len(seq)
                    if dfn > 0:
                        data = seq
                    else:
                        data = seq[:self.sequence_length]
                    self.send_sequence(idx, data, dtype="H")  # DAC1
                    time.sleep(0.1)
            except RuntimeError as e:
                self.logg.error("DAC channels writing error: %s", e)
        else:
            self.logg.error("GPIO channels error")
            return

    def write_triggers(self, galvo_sequences=None, galvo_channels=None, digital_sequences=None, digital_channels=None, infinity=True):
        try:
            self.infinity = infinity
            if digital_sequences is not None:
                self.write_digital_sequences(digital_sequences, indices=digital_channels)
            if galvo_sequences is not None:
                self.write_galvo_sequences(galvo_sequences, indices=galvo_channels)
        except RuntimeError as e:
            self.logg.error("Sequence writing error: %s", e)

    def run_triggers(self):
        if self.infinity:
            self.trg_thread = TriggerThread(self, self.t)
            self.trg_thread.start()
            self.logg.info("Trigger starts infinitely")
        else:
            self.send_command("START")
            time.sleep(self.sequence_length / self.sample_rate)
            self.logg.info("Trigger runs once")

    def stop_triggers(self):
        if self.infinity:
            self.trg_thread.stop()
            self.trg_thread = None
        self.logg.info("Trigger stopped")


def same_list(lst):
    return len(set(lst)) == 1 if lst else True


class TriggerThread(threading.Thread):
    running = False
    lock = threading.Lock()

    def __init__(self, bd, dt):
        threading.Thread.__init__(self)
        self.bd = bd
        self.dt = dt

    def run(self):
        self.running = True
        while self.running:
            with self.lock:
                self.bd.send_command("START")
            time.sleep(self.dt)

    def stop(self):
        self.running = False
        self.join()
