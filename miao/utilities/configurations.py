import json


class MicroscopeConfiguration:

    def __init__(self, fd=None):
        if fd:
            self.cfd = fd
            self.configs = self.load_config(self.cfd)
        else:
            raise AttributeError(f"Configuration File Failed to Load")

    @staticmethod
    def write_config(dataframe, dfd):
        with open(dfd, 'w') as f:
            json.dump(dataframe, f, indent=4)

    @staticmethod
    def load_config(dfd):
        with open(dfd, 'r') as f:
            cfg = json.load(f)
        return cfg

    @staticmethod
    def change_config(values, dfd):
        with open(dfd, 'w') as f:
            json.dump(values, f)
