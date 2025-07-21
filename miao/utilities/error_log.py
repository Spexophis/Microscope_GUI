# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


import logging


class ErrorLog:

    def __init__(self, log_file):
        self.log_file = log_file
        self.error_log = self.setup_logger()

    def setup_logger(self):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filename=self.log_file,
                            filemode='w')
        logger = logging.getLogger('shared_logger')
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger
