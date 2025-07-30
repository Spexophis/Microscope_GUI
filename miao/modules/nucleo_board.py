from pyb import Timer, Pin, DAC

# --- Globals ---
freq = 1000
duties = [50, 50, 50]
timer = None
channels = []

# DACs for analog output (PA4, PA5)
dac_pins = [DAC(Pin.board.PA4), DAC(Pin.board.PA5)]
triangle_steps = 128   # Number of steps per half-wave (increase for smoother triangle)
triangle_value = 0     # Current value (0...triangle_steps*2-1)
triangle_dir = 1       # +1 for up, -1 for down

sync_timer = None
signals_running = True  # State variable

# --- Init functions ---
def init():
    global timer, channels
    timer = Timer(2, freq=freq)
    channels = [
        timer.channel(1, Timer.PWM, pin=Pin.board.PA0),
        timer.channel(2, Timer.PWM, pin=Pin.board.PA1),
        timer.channel(3, Timer.PWM, pin=Pin.board.PB10),
    ]
    start_triangle_sync()

def start():
    global timer, channels, signals_running
    if timer is None:
        init()
    for ch, duty in zip(channels, duties):
        ch.pulse_width_percent(duty)
    start_triangle_sync()
    signals_running = True

def stop():
    global channels, sync_timer, signals_running
    for ch in channels:
        ch.pulse_width_percent(0)
    if sync_timer:
        sync_timer.deinit()
    # Set DACs to 0V
    dac_pins[0].write(0)
    dac_pins[1].write(0)
    signals_running = False

def set_freq(new_freq):
    global freq, timer
    freq = new_freq
    if timer:
        timer.freq(freq)
    start_triangle_sync()

def set_duty(index, duty):
    global duties, channels
    duties[index] = duty
    if channels:
        channels[index].pulse_width_percent(duty)

# --- Triangle wave update, called on every PWM period ---
def triangle_wave_step(t):
    global triangle_value, triangle_dir, triangle_steps, dac_pins, signals_running
    if not signals_running:
        dac_pins[0].write(0)
        dac_pins[1].write(0)
        return
    # One triangle cycle is 2*triangle_steps steps (up then down)
    if triangle_dir == 1:
        triangle_value += 1
        if triangle_value >= triangle_steps * 2:
            triangle_dir = -1
    else:
        triangle_value -= 1
        if triangle_value <= 0:
            triangle_dir = 1
    # Convert to DAC range (0-255, 8-bit)
    dac_val = abs(triangle_value - triangle_steps) * (255 // triangle_steps)
    # Output to both DAC channels
    dac_pins[0].write(dac_val)
    dac_pins[1].write(255 - dac_val)  # Out of phase

def start_triangle_sync():
    global sync_timer, triangle_value, triangle_dir, freq
    if sync_timer:
        sync_timer.deinit()
    triangle_value = 0
    triangle_dir = 1
    sync_timer = Timer(4, freq=freq)
    sync_timer.callback(triangle_wave_step)
