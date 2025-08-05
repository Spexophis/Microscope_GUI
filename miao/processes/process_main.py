# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


from miao.processes import process_shwfs, process_trigger, process_flock


class MainProcess:

    def __init__(self, config, logg, path):
        self.config = config
        self.logg = logg
        self.data_folder = path
        self.shwfsr = process_shwfs.WavefrontSensing(logg=self.logg.error_log)
        self.trigger = process_trigger.TriggerSequence(logg=self.logg.error_log)
        self.foc_ctrl = process_flock.FocusLocker()
        self.logg.error_log.info("All processing set up")
