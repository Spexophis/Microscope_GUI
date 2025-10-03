import serial
import struct
import numpy as np
import time

# Adjust COM port to your STM32's USB CDC port
ser = serial.Serial("COM8", 115200, timeout=1)


def send_command(cmd):
    ser.write(cmd.encode())
    reply = ser.read_until(b'\n')
    print("CMD:", cmd, "| Reply:", reply)


def send_sequence(seq_id, data, dtype="H"):
    packet = bytearray()
    packet += b"\xAA\x55"
    packet += struct.pack("<B", seq_id)
    packet += struct.pack("<I", len(data))
    packet += np.array(data, dtype=dtype).tobytes()
    ser.write(packet)
    reply = ser.read_until(b'\n')
    print("SEQ:", seq_id, "| Reply:", reply)


N = 64000
dac1 = 1024 + np.arange(N, dtype=np.uint16) % 4096         # Sawtooth 0–4095
dac2 = 4095 - 1024 - dac1                                  # Inverted sawtooth
dig0 = np.array([(i >> 0) & 1 for i in range(N)], dtype=np.uint8)  # PA0
dig1 = np.array([(i >> 0) & 1 for i in range(N)], dtype=np.uint8)  # PA1
dig2 = np.array([(i >> 0) & 1 for i in range(N)], dtype=np.uint8)  # PA2
dac1[-1] = 2048
dac2[-1] = 2048
dig0[-1] = 0
dig1[-1] = 0
dig2[-1] = 0


send_sequence(0, dig0, dtype="B") # Digital PA0
send_sequence(1, dig1, dtype="B") # Digital PA1
send_sequence(2, dig2, dtype="B") # Digital PA1

send_sequence(3, dac1, dtype="H")   # DAC1
send_sequence(4, dac2, dtype="H")   # DAC2

for i in range(20):
    send_command("START")
    time.sleep(0.1)

ser.close()
