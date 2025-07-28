# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.

"""
Microscope GUI

Description:
    Graphical User Interface (GUI) for controlling a microscope and performing image processing
    in an SLM-based parallel RESOLFT microscopy system with Adaptive Optics.

Usage:
    Run this app from the Command Prompt (Conda)

Notes:
    - The order of package imports in this script is critical and **must not be changed**.
    - Changing the import order may cause runtime errors or unexpected behavior.

Author: Ruizhe Lin
Date: 2025-07-21
"""


import os
import sys
import time

from miao.widgets import widget_main
from miao.controllers import controller_main
from miao.modules import module_main
from miao.processes import process_main
from miao.utilities import configurations, error_log
from miao.utilities import customized_widgets as cw

from PyQt5 import QtWidgets


class MicroscopeGUI(QtWidgets.QMainWindow):

    def __init__(self, config_file, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self.config = configurations.MicroscopeConfiguration(config_file)
        except Exception as e:
            self.error_n_exit(f"Error loading configuration: {e}")
            return

        self.data_folder = f"{self.config.configs['Data Path']}\\{time.strftime('%Y%m%d')}"
        try:
            os.makedirs(self.data_folder, exist_ok=True)
            print(f'Directory {self.data_folder} has been created successfully.')
        except Exception as e:
            print(f'Error creating directory {self.data_folder}: {e}')

        self.log_file = os.path.join(self.data_folder, time.strftime("%H%M%S") + 'app.log')
        self.info_log = error_log.ErrorLog(self.log_file)

        try:
            self.module = module_main.MainModule(self.config, self.info_log, self.data_folder)
        except Exception as e:
            self.info_log.error_log.error(f"Error: {e}")
        try:
            self.process = process_main.MainProcess(self.config, self.info_log, self.data_folder)
        except Exception as e:
            self.info_log.error_log.error(f"Error: {e}")
        try:
            self.view = widget_main.MainWidget(self.config, self.info_log, self.data_folder)
        except Exception as e:
            self.info_log.error_log.error(f"Error: {e}")
        try:
            self.controller = controller_main.MainController(self.view, self.module, self.process,
                                                             self.config, self.info_log, self.data_folder)
        except Exception as e:
            self.info_log.error_log.error(f"Error: {e}")

    def error_n_exit(self, message):
        msg_box = cw.MessageBoxWidget("Error", message)
        msg_box.exec_()
        self.close()


cfd = r"C:\\Users\\Public\\Documents\\Data\\config_files\\microscope_configurations__polarization_scan.json"


class AppWrapper:
    def __init__(self, config_file):
        self.app = QtWidgets.QApplication(sys.argv)  # Create an instance of QApplication
        self.gui = MicroscopeGUI(config_file)
        self.gui.view.Signal_quit.connect(self.close)  # Ensure this signal exists in your GUI

    def run(self):
        try:
            self.gui.view.show()
            sys.exit(self.app.exec_())
        except Exception as e:
            print(f"Fatal error: {e}")
            sys.exit(1)

    def close(self):
        self.gui.module.close()
        self.app.exit()


def main():
    app_wrapper = AppWrapper(cfd)
    app_wrapper.run()


if __name__ == '__main__':
    main()
