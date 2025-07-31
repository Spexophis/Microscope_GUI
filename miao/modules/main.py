from pyb import Pin
import time
import nucleo_board

p = nucleo_board.NUCLEO()

# Poll the user button in main loop
button = Pin('PC13', Pin.IN, Pin.PULL_UP)

p.start()

while True:
    if p.signals_running and button.value() == 0:
        p.stop()
        print("Signals stopped by user button.")
        while button.value() == 0:  # Debounce: wait for release
            time.sleep_ms(20)
    time.sleep_ms(50)
