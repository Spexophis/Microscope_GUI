from pyb import Timer, Pin, DAC


class NUCLEO:

    def __init__(self):
        self.freq = 4000
        self.timer = None

        self.dig_pins = [Pin('PA0', Pin.OUT), Pin('PA1', Pin.OUT), Pin('PB10', Pin.OUT)]
        self.dac_pins = [DAC(Pin.board.PA4), DAC(Pin.board.PA5)]

        self.signals_running = False

        self.digital_sequences = [[1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0],
                                  [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
                                  [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1]]
        self.analog_sequences = [[0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 255],
                                 [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 255]]

        self.idx = 0
        self.n = len(self.digital_sequences[0])

    def start(self):
        self.idx = 0
        self.n = len(self.digital_sequences[0])
        self.timer = Timer(2, freq=self.freq)
        self.timer.callback(self.output_step)
        self.signals_running = True

    def output_step(self, t):
        for i in range(3):
            self.dig_pins[i].value(self.digital_sequences[i][self.idx])
        for i in range(2):
            self.dac_pins[i].write(self.analog_sequences[i][self.idx])
        self.idx = (self.idx + 1) % self.n

    def stop(self):
        for ch in self.dig_pins:
            ch.value(0)
        if self.timer:
            self.timer.deinit()
        for dac in self.dac_pins:
            dac.write(0)
        self.signals_running = False
