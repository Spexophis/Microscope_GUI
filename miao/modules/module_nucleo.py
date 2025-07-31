import subprocess
import serial
import time

class NucleoBoard:

    def __init__(self, logg=None, config=None):
        self.logg = logg or self.setup_logging()
        self.config = config or self.load_configs()
        self.com_port = 'COM4'
        self.ser = serial.Serial(self.com_port, 115200, timeout=2)
        self.logg.info(self.ser.readline().decode())

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

    def write_triggers(self, seq1, seq2, seq3, seq4, seq5):
        self.ser.write(b'LOAD\n')
        self.logg.info(self.ser.readline().decode())
        for arr in [seq1, seq2, seq3, seq4, seq5]:
            line = ','.join(str(x) for x in arr) + '\n'
            self.ser.write(line.encode())
        self.logg.info(self.ser.readline().decode())

    def run_triggers(self):
        self.ser.write(b'TRIGGER\n')
        time.sleep(0.1)
        while self.ser.in_waiting:
            self.logg.info(self.ser.readline().decode().strip())

    def stop_triggers(self):
        self.ser.write(b'STOP\n')
        time.sleep(0.1)
        while self.ser.in_waiting:
            self.logg.info(self.ser.readline().decode().strip())

    def load_board(self, filenames=None):
        if filenames is None:
            filenames = [r"C:\Users\Public\Documents\Github\Microscope_GUI\miao\modules\nucleo_board.py",
                         r"C:\Users\Public\Documents\Github\Microscope_GUI\miao\modules\main.py"]
        for fn in filenames:
            cmd = ['mpremote', 'connect', self.com_port, 'fs', 'cp', fn, ':']
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print('Upload successful!')
                print(result.stdout)
            except subprocess.CalledProcessError as e:
                print('Upload failed!')
                print(e.stderr)
