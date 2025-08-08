import serial
import time

class ArduinoUno:

    def __init__(self, logg=None, config=None):
        self.logg = logg or self.setup_logging()
        self.config = config or self.load_configs()
        self.com_port = 'COM8'
        self.ser = serial.Serial(self.com_port, 9600, timeout=1)
        time.sleep(2)

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
        self.ser.close()

    def run_triggers(self):
        self.ser.write(b'H')

    def stop_triggers(self):
        self.ser.write(b'L')
