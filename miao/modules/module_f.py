import serial, struct, time

PORT = "COM9"
BAUD = 115200

def be16(x): return struct.pack(">H", x & 0xFFFF)

def send(ser, target, payload=b"", ack=True):
    ser.write(bytes([0xA5, target]) + payload)
    if ack:
        r = ser.read(3)
        assert len(r)==3 and r[0]==0xA5 and r[1]==target and r[2]==0x00, f"Bad ACK: {r}"

def load_seq(ser, target, bits):
    b = bytes(1 if x else 0 for x in bits)
    send(ser, target, be16(len(b)) + b)

def set_rate(ser, psc, arr): send(ser, 0x18, be16(psc)+be16(arr))
def start(ser):              send(ser, 0x15)
def stop(ser):               send(ser, 0x17)

def square_period(samples, duty):
    on = int(samples*duty)
    return [1]*on + [0]*(samples-on)

with serial.Serial(PORT, BAUD, timeout=1) as ser:
    # 50 kHz sample: PSC=239, ARR=19 (matches CubeMX)
    set_rate(ser, 239, 19)

    # 100-sample base period → 500 Hz squares at 50 kHz sample
    L = 1000  # sequence length
    s0 = (square_period(100, 0.50)) * 10   # PA0
    s1 = (square_period(100, 0.25)) * 10   # PA1
    s2 = (square_period(100, 0.75)) * 10   # PB10

    load_seq(ser, 0x10, s0)
    load_seq(ser, 0x11, s1)
    load_seq(ser, 0x12, s2)

    start(ser)
    time.sleep(3)
    stop(ser)
