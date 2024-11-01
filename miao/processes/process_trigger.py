import numpy as np


class TriggerSequence:
    class TriggerParameters:
        def __init__(self, sample_rate=250000):
            # daq
            self.sample_rate = sample_rate  # Hz
            # digital triggers
            self.digital_starts = [0.002, 0.007, 0.007, 0.012, 0.012, 0.012, 0.012]
            self.digital_ends = [0.004, 0.010, 0.010, 0.015, 0.015, 0.015, 0.015]
            self.digital_starts = [int(digital_start * self.sample_rate) for digital_start in self.digital_starts]
            self.digital_ends = [int(digital_end * self.sample_rate) for digital_end in self.digital_ends]
            # piezo scanner
            self.piezo_conv_factors = [10., 10., 10.]
            self.piezo_steps = [0.03, 0.03, 0.15]
            self.piezo_ranges = [0.54, 0.54, 0.0]
            self.piezo_positions = [50., 50., 50.]
            self.piezo_return_time = 0.1
            self.return_samples = int(np.ceil(self.piezo_return_time * self.sample_rate))
            self.piezo_steps = [step_size / conv_factor for step_size, conv_factor in
                                zip(self.piezo_steps, self.piezo_conv_factors)]
            self.piezo_ranges = [move_range / conv_factor for move_range, conv_factor in
                                 zip(self.piezo_ranges, self.piezo_conv_factors)]
            self.piezo_positions = [position / conv_factor for position, conv_factor in
                                    zip(self.piezo_positions, self.piezo_conv_factors)]
            self.piezo_starts = [i - j for i, j in zip(self.piezo_positions, [k / 2 for k in self.piezo_ranges])]
            self.piezo_scan_pos = [int(np.ceil(safe_divide(scan_range, scan_step))) for scan_range, scan_step in
                                   zip(self.piezo_ranges, self.piezo_steps)]
            self.piezo_scan_positions = [start + step * np.arange(ns) for start, step, ns in
                                         zip(self.piezo_starts, self.piezo_steps, self.piezo_scan_pos)]
            # galvo switcher
            self.galvo_sw_settle = 0.0025  # s
            self.galvo_sw_settle_samples = int(np.ceil(self.galvo_sw_settle * self.sample_rate))
            self.galvo_sw_states = [4., -2., 0.]
            # galvo scanner
            self.galvo_step_response = int(32e-4 * self.sample_rate)  # ~320 us
            self.galvo_return = int(8e-4 * self.sample_rate)  # ~800 us
            self.ramp_down_fraction = 0.016
            self.ramp_down_offset = 20  # samples
            # galvo scan for read out
            self.galvo_origins = [0.0, 0.0]  # V
            self.galvo_ranges = [1.0, 1.0]  # V
            self.galvo_starts = [o_ - r_ / 2 for (o_, r_) in zip(self.galvo_origins, self.galvo_ranges)]
            self.galvo_stops = [o_ + r_ / 2 for (o_, r_) in zip(self.galvo_origins, self.galvo_ranges)]
            # dot array for read out
            self.dot_ranges = [0.8, 0.8]  # V
            self.dot_starts = [o_ - r_ / 2 for (o_, r_) in zip(self.galvo_origins, self.dot_ranges)]
            self.dot_step_s = 41  # samples
            self.dot_step_v = 0.0186  # volts
            self.dot_step_y = 0.0186  # volts
            self.up_rate = self.dot_step_v / self.dot_step_s
            self.dot_pos = np.arange(self.dot_starts[0], self.dot_starts[0] + self.dot_ranges[0] + self.dot_step_v,
                                     self.dot_step_v)
            # sawtooth wave for read out
            self.ramp_up = np.arange(self.galvo_starts[0], self.galvo_stops[0], self.up_rate)
            self.ramp_up_samples = self.ramp_up.size
            self.ramp_down_samples = int(np.ceil(self.ramp_up_samples * self.ramp_down_fraction))
            self.frequency = int(self.sample_rate / self.ramp_up_samples)  # Hz
            # square wave for read out
            self.samples_high = 1
            self.samples_low = self.dot_step_s - self.samples_high
            self.samples_delay = int(np.abs(self.dot_starts[0] - self.galvo_starts[0]) / self.up_rate)
            self.samples_offset = self.ramp_up_samples - self.samples_delay - self.dot_step_s * self.dot_pos.size
            # galvo scan for activation
            self.galvo_origins_act = [0.00, 0.00]  # V
            self.galvo_ranges_act = [1.0, 1.0]  # V
            self.galvo_starts_act = [o_ - r_ / 2 for (o_, r_) in zip(self.galvo_origins_act, self.galvo_ranges_act)]
            self.galvo_stops_act = [o_ + r_ / 2 for (o_, r_) in zip(self.galvo_origins_act, self.galvo_ranges_act)]
            # dot array for activation
            self.dot_ranges_act = [0.8, 0.8]  # V
            self.dot_starts_act = [o_ - r_ / 2 for (o_, r_) in zip(self.galvo_origins_act, self.dot_ranges_act)]
            self.dot_step_s_act = 41  # samples
            self.dot_step_v_act = 0.018  # volts
            self.dot_step_y_act = 0.018  # volts
            self.up_rate_act = self.dot_step_v_act / self.dot_step_s_act
            self.dot_pos_act = np.arange(self.dot_starts_act[0],
                                         self.dot_starts_act[0] + self.dot_ranges_act[0] + self.dot_step_v_act,
                                         self.dot_step_v_act)
            # sawtooth wave for activation
            self.ramp_up_act = np.arange(self.galvo_starts_act[0], self.galvo_stops_act[0], self.up_rate_act)
            self.ramp_up_samples_act = self.ramp_up_act.size
            self.ramp_down_samples_act = int(np.ceil(self.ramp_up_samples_act * self.ramp_down_fraction))
            self.frequency_act = int(self.sample_rate / self.ramp_up_samples_act)  # Hz
            # square wave for activation
            self.samples_high_act = 1
            self.samples_low_act = self.dot_step_s_act - self.samples_high_act
            self.samples_delay_act = int(np.abs(self.dot_starts_act[0] - self.galvo_starts_act[0]) / self.up_rate_act)
            self.samples_offset_act = self.ramp_up_samples_act - self.samples_delay_act - self.dot_step_s_act * self.dot_pos_act.size
            # emccd camera
            self.cycle_time = 0.0521  # s
            self.initial_time = 0.0055  # s
            self.initial_samples = int(np.ceil(self.initial_time * self.sample_rate))
            self.standby_time = 0.0467  # s
            self.standby_samples = int(np.ceil(self.standby_time * self.sample_rate))
            self.exposure_samples = 0.  # s
            self.exposure_time = self.exposure_samples / self.sample_rate
            # rolling shutter camera (light sheet mode of Hamamatsu sCMOS)
            self.line_interval = 1e-5  # s
            self.line_interval_samples = int(np.ceil(self.line_interval * self.sample_rate))
            self.trigger_delay_samples = 9 * self.line_interval_samples
            self.interval_line_number = 10.5
            self.line_exposure = 1e-5  # s
            self.line_exposure_samples = int(np.ceil(self.line_exposure * self.sample_rate))
            self.readout_timing = 0.001  # s
            self.readout_timing_samples = int(np.ceil(self.readout_timing * self.sample_rate))

    def __init__(self, logg=None):
        self.logg = logg or self.setup_logging()
        self._parameters = self.TriggerParameters()

    def __getattr__(self, item):
        if hasattr(self._parameters, item):
            return getattr(self._parameters, item)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{item}'")

    @staticmethod
    def setup_logging():
        import logging
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
        return logging

    def update_nidaq_parameters(self, sample_rate=None):
        if sample_rate is not None:
            self._parameters = self.TriggerParameters(sample_rate)

    def update_piezo_scan_parameters(self, piezo_ranges=None, piezo_steps=None, piezo_positions=None,
                                     piezo_return_time=None):
        original_values = {"piezo_ranges": self.piezo_ranges, "piezo_steps": self.piezo_steps,
                           "piezo_positions": self.piezo_positions, "piezo_return_time": self.piezo_return_time}
        try:
            if piezo_ranges is not None:
                self.piezo_ranges = [move_range / conv_factor for move_range, conv_factor in
                                     zip(piezo_ranges, self.piezo_conv_factors)]
            if piezo_steps is not None:
                self.piezo_steps = [step_size / conv_factor for step_size, conv_factor in
                                    zip(piezo_steps, self.piezo_conv_factors)]
            if piezo_positions is not None:
                self.piezo_positions = [position / conv_factor for position, conv_factor in
                                        zip(piezo_positions, self.piezo_conv_factors)]
            if piezo_return_time is not None:
                self.piezo_return_time = piezo_return_time
                self.return_samples = int(np.ceil(self.piezo_return_time * self.sample_rate))
            self.piezo_starts = [i - j for i, j in zip(self.piezo_positions, [k / 2 for k in self.piezo_ranges])]
            self.piezo_scan_pos = [int(np.ceil(safe_divide(scan_range, scan_step))) for scan_range, scan_step in
                                   zip(self.piezo_ranges, self.piezo_steps)]
            self.piezo_scan_positions = [start + step * np.arange(ns) for start, step, ns in
                                         zip(self.piezo_starts, self.piezo_steps, self.piezo_scan_pos)]
        except ValueError:
            for attr, value in original_values.items():
                setattr(self, attr, value)
            self.logg.info("Piezo scanning parameters reverted to original values.")
            return

    def update_galvo_scan_parameters(self, origins=None, ranges=None, foci=None, origins_act=None, ranges_act=None,
                                     foci_act=None, sws=None):
        original_values = {"frequency": self.frequency, "galvo_origins": self.galvo_origins,
                           "galvo_ranges": self.galvo_ranges, "galvo_starts": self.galvo_starts,
                           "galvo_stops": self.galvo_stops,
                           "dot_ranges": self.dot_ranges, "dot_starts": self.dot_starts, "dot_step_v": self.dot_step_v,
                           "dot_step_s": self.dot_step_s, "dot_step_y": self.dot_step_y, "dot_pos": self.dot_pos,
                           "samples_low": self.samples_low, "samples_delay": self.samples_delay,
                           "samples_offset": self.samples_offset,
                           "frequency_act": self.frequency_act, "galvo_origins_act": self.galvo_origins_act,
                           "galvo_ranges_act": self.galvo_ranges_act, "galvo_starts_act": self.galvo_starts_act,
                           "galvo_stops_act": self.galvo_stops_act, "dot_ranges_act": self.dot_ranges_act,
                           "dot_starts_act": self.dot_starts_act, "dot_step_v_act": self.dot_step_v_act,
                           "dot_step_s_act": self.dot_step_s_act, "dot_step_y_act": self.dot_step_y_act,
                           "dot_pos_act": self.dot_pos_act, "samples_low_act": self.samples_low_act,
                           "samples_delay_act": self.samples_delay_act, "samples_offset_act": self.samples_offset_act,
                           "galvo_sw_states": self.galvo_sw_states}
        try:
            if origins is not None:
                self.galvo_origins = origins
            if ranges is not None:
                self.galvo_ranges, self.dot_ranges = ranges
            if foci is not None:
                [self.dot_step_s, self.dot_step_v, self.dot_step_y] = foci
            self.galvo_starts = [o_ - r_ / 2 for (o_, r_) in zip(self.galvo_origins, self.galvo_ranges)]
            self.galvo_stops = [o_ + r_ / 2 for (o_, r_) in zip(self.galvo_origins, self.galvo_ranges)]
            self.dot_starts = [o_ - r_ / 2 for (o_, r_) in zip(self.galvo_origins, self.dot_ranges)]
            self.dot_pos = np.arange(self.dot_starts[0], self.dot_starts[0] + self.dot_ranges[0] + self.dot_step_v,
                                     self.dot_step_v)
            self.up_rate = self.dot_step_v / self.dot_step_s
            self.samples_low = self.dot_step_s - self.samples_high
            self.ramp_up = np.arange(self.galvo_starts[0], self.galvo_stops[0], self.up_rate)
            self.ramp_up_samples = self.ramp_up.size
            self.ramp_down_samples = int(np.ceil(self.ramp_up_samples * self.ramp_down_fraction))
            self.frequency = int(self.sample_rate / self.ramp_up_samples)  # Hz
            self.samples_delay = int(np.abs(self.dot_starts[0] - self.galvo_starts[0]) / self.up_rate)
            self.samples_offset = self.ramp_up_samples - self.samples_delay - self.dot_step_s * self.dot_pos.size
            if self.samples_offset < 0:
                self.logg.error("Invalid parameter combination leading to negative samples_offset.")
                raise ValueError("Invalid Galvo scanning parameters.")

            if origins_act is not None:
                self.galvo_origins_act = origins_act
            if ranges is not None:
                self.galvo_ranges_act, self.dot_ranges_act = ranges_act
            if foci is not None:
                [self.dot_step_s_act, self.dot_step_v_act, self.dot_step_y_act] = foci_act
            self.galvo_starts_act = [o_ - r_ / 2 for (o_, r_) in zip(self.galvo_origins_act, self.galvo_ranges_act)]
            self.galvo_stops_act = [o_ + r_ / 2 for (o_, r_) in zip(self.galvo_origins_act, self.galvo_ranges_act)]
            self.dot_starts_act = [o_ - r_ / 2 for (o_, r_) in zip(self.galvo_origins_act, self.dot_ranges_act)]
            self.dot_pos_act = np.arange(self.dot_starts_act[0],
                                         self.dot_starts_act[0] + self.dot_ranges_act[0] + self.dot_step_v_act,
                                         self.dot_step_v_act)
            self.up_rate_act = self.dot_step_v_act / self.dot_step_s_act
            self.samples_low_act = self.dot_step_s_act - self.samples_high_act
            self.ramp_up_act = np.arange(self.galvo_starts_act[0], self.galvo_stops_act[0], self.up_rate_act)
            self.ramp_up_samples_act = self.ramp_up_act.size
            self.ramp_down_samples_act = int(np.ceil(self.ramp_up_samples_act * self.ramp_down_fraction))
            self.frequency_act = int(self.sample_rate / self.ramp_up_samples_act)  # Hz
            self.samples_delay_act = int(np.abs(self.dot_starts_act[0] - self.galvo_starts_act[0]) / self.up_rate_act)
            self.samples_offset_act = self.ramp_up_samples_act - self.samples_delay_act - self.dot_step_s_act * self.dot_pos_act.size
            if self.samples_offset_act < 0:
                self.logg.error("Invalid parameter combination leading to negative samples_offset.")
                raise ValueError("Invalid Galvo scanning parameters.")

            if sws is not None:
                self.galvo_sw_states = sws
        except ValueError:
            for attr, value in original_values.items():
                setattr(self, attr, value)
            self.logg.info("Galvo scanning parameters reverted to original values.")
            return

    def update_digital_parameters(self, digital_starts=None, digital_ends=None):
        if digital_starts is not None:
            self.digital_starts = digital_starts
        if digital_ends is not None:
            self.digital_ends = digital_ends
        self.digital_starts = [int(digital_start * self.sample_rate) for digital_start in self.digital_starts]
        self.digital_ends = [int(digital_end * self.sample_rate) for digital_end in self.digital_ends]

    def update_camera_parameters(self, initial_time=None, standby_time=None, cycle_time=None):
        if initial_time is not None:
            self.initial_time = initial_time
            self.initial_samples = int(np.ceil(self.initial_time * self.sample_rate))
        if standby_time is not None:
            self.standby_time = standby_time
            self.standby_samples = int(np.ceil(self.standby_time * self.sample_rate))
        if self.cycle_time is not None:
            self.cycle_time = cycle_time

    def generate_digital_triggers(self, lasers, camera):
        cam_sw = self.galvo_sw_states[camera]
        cam_ind = camera + 4
        lasers = lasers.copy()
        interval_samples = max(self.initial_samples, self.galvo_sw_settle_samples)
        if interval_samples > self.digital_starts[cam_ind]:
            offset_samples = interval_samples - self.digital_starts[cam_ind]
            self.digital_starts = [(_start + offset_samples) for _start in self.digital_starts]
            self.digital_ends = [(_end + offset_samples) for _end in self.digital_ends]
        cycle_samples = self.digital_ends[cam_ind] + self.standby_samples
        digital_trigger = np.zeros((len(lasers) + 1, cycle_samples), dtype=np.int8)
        switch_trigger = cam_sw * np.ones(cycle_samples, dtype=np.float16)
        self.exposure_samples = self.digital_ends[cam_ind] - self.digital_starts[cam_ind]
        self.exposure_time = self.exposure_samples / self.sample_rate
        digital_trigger[-1, self.digital_starts[cam_ind]:self.digital_ends[cam_ind]] = 1
        for ln, laser in enumerate(lasers):
            digital_trigger[ln, self.digital_starts[laser]:self.digital_ends[laser]] = 1
        lasers.append(cam_ind)
        switch_trigger[:self.digital_starts[cam_ind] - self.galvo_sw_settle_samples] = 0.
        switch_trigger[
        self.digital_starts[cam_ind] - self.galvo_sw_settle_samples:self.digital_starts[cam_ind]] = smooth_ramp(0.,
                                                                                                                cam_sw,
                                                                                                                self.galvo_sw_settle_samples)
        switch_trigger[
        self.digital_ends[cam_ind]:self.digital_ends[cam_ind] + self.galvo_sw_settle_samples] = smooth_ramp(cam_sw, 0.,
                                                                                                            self.galvo_sw_settle_samples)
        switch_trigger[self.digital_ends[cam_ind] + self.galvo_sw_settle_samples:] = 0.
        return digital_trigger, switch_trigger, lasers

    def generate_widefield_zstack_triggers(self, lasers, camera):
        cam_sw = self.galvo_sw_states[camera]
        cam_ind = camera + 4
        lasers = lasers.copy()
        interval_samples = max(self.initial_samples, self.galvo_sw_settle_samples)
        if interval_samples > self.digital_starts[cam_ind]:
            offset_samples = interval_samples - self.digital_starts[cam_ind]
            self.digital_starts = [(_start + offset_samples) for _start in self.digital_starts]
            self.digital_ends = [(_end + offset_samples) for _end in self.digital_ends]
        cycle_samples = self.digital_ends[cam_ind] + max(self.standby_samples, self.return_samples)
        digital_trigger = np.zeros((len(lasers) + 1, cycle_samples), dtype=np.int8)
        switch_trigger = cam_sw * np.ones(cycle_samples, dtype=np.float16)
        self.exposure_samples = self.digital_ends[cam_ind] - self.digital_starts[cam_ind]
        self.exposure_time = self.exposure_samples / self.sample_rate
        digital_trigger[-1, self.digital_starts[cam_ind]:self.digital_ends[cam_ind]] = 1
        for ln, laser in enumerate(lasers):
            digital_trigger[ln, self.digital_starts[laser]:self.digital_ends[laser]] = 1
        digital_sequences = [np.empty((0,)) for _ in range(len(lasers) + 1)]
        for i, dtr in enumerate(digital_trigger):
            digital_sequences[i] = np.tile(dtr, self.piezo_scan_pos[2])
        lasers.append(cam_ind)
        switch_trigger[:self.digital_starts[cam_ind] - self.galvo_sw_settle_samples] = 0.
        switch_trigger[
        self.digital_starts[cam_ind] - self.galvo_sw_settle_samples:self.digital_starts[cam_ind]] = smooth_ramp(0.,
                                                                                                                cam_sw,
                                                                                                                self.galvo_sw_settle_samples)
        switch_trigger[
        self.digital_ends[cam_ind]:self.digital_ends[cam_ind] + self.galvo_sw_settle_samples] = smooth_ramp(cam_sw, 0.,
                                                                                                            self.galvo_sw_settle_samples)
        switch_trigger[self.digital_ends[cam_ind] + self.galvo_sw_settle_samples:] = 0.
        switch_trigger = np.tile(switch_trigger, self.piezo_scan_pos[2])
        piezo_sequence = np.repeat(self.piezo_scan_positions[2], cycle_samples)
        piezo_sequence = shift_array(piezo_sequence, max(self.standby_samples, self.return_samples),
                                     fill=piezo_sequence[0], direction="backward")
        return np.asarray(digital_sequences), switch_trigger, piezo_sequence, lasers, self.piezo_scan_pos[2]

    def generate_galvo_scanning(self, g="activation"):
        if g == "activation":
            ramp_down_act = np.linspace(self.ramp_up_act[-1], self.ramp_up_act[0], num=self.ramp_down_samples_act,
                                        endpoint=True)
            extended_cycle_act = np.concatenate((self.ramp_up_act, ramp_down_act))
            fast_axis_galvo_act = np.tile(extended_cycle_act, self.dot_pos_act.size)
            slow_axis_galvo_act = np.zeros_like(fast_axis_galvo_act)
            indices_act = np.arange(self.ramp_up_samples_act + 1, len(fast_axis_galvo_act), extended_cycle_act.size)
            slow_axis_galvo_act[indices_act] = 1
            slow_axis_galvo_act = np.cumsum(slow_axis_galvo_act) * self.dot_step_y_act + self.dot_starts_act[1]
            slow_axis_galvo_act[-self.ramp_down_samples_act:] = np.linspace(
                slow_axis_galvo_act[-self.ramp_down_samples_act], self.dot_starts_act[1], self.ramp_down_samples_act)
            fill_samples_act = max(0, self.galvo_sw_settle_samples - (
                    self.samples_offset_act + self.ramp_down_samples_act))
            fast_axis_galvo_act = np.pad(fast_axis_galvo_act, (self.galvo_return, fill_samples_act), 'constant',
                                         constant_values=(self.galvo_starts[0], self.galvo_starts[0]))
            slow_axis_galvo_act = np.pad(slow_axis_galvo_act, (self.galvo_return, fill_samples_act), 'constant',
                                         constant_values=(self.dot_starts_act[1], self.dot_starts_act[1]))
            _sqr_act = np.pad(np.ones(self.samples_high_act), (0, self.samples_low_act), 'constant',
                              constant_values=(0, 0))
            square_wave_act = np.pad(np.tile(_sqr_act, self.dot_pos_act.size),
                                     (self.samples_delay_act, self.samples_offset + self.ramp_down_samples), 'constant',
                                     constant_values=(0, 0))
            laser_trigger_act = np.tile(square_wave_act, self.dot_pos_act.size)
            return fast_axis_galvo_act, slow_axis_galvo_act, laser_trigger_act
        elif g == "readout":
            ramp_down = np.linspace(self.ramp_up[-1], self.ramp_up[0], num=self.ramp_down_samples, endpoint=True)
            extended_cycle = np.concatenate((self.ramp_up, ramp_down))
            fast_axis_galvo = np.tile(extended_cycle, self.dot_pos.size)
            slow_axis_galvo = np.zeros_like(fast_axis_galvo)
            indices = np.arange(self.ramp_up_samples + 1, len(fast_axis_galvo), extended_cycle.size)
            slow_axis_galvo[indices] = 1
            slow_axis_galvo = np.cumsum(slow_axis_galvo) * self.dot_step_y + self.dot_starts[1]
            slow_axis_galvo[-self.ramp_down_samples:] = np.linspace(slow_axis_galvo[-self.ramp_down_samples],
                                                                    self.dot_starts[1], self.ramp_down_samples)
            fill_samples = max(0, self.galvo_sw_settle_samples - (self.samples_offset + self.ramp_down_samples))
            fast_axis_galvo = np.pad(fast_axis_galvo, (self.galvo_return, fill_samples), 'constant',
                                     constant_values=(self.galvo_starts[0], self.galvo_starts[0]))
            slow_axis_galvo = np.pad(slow_axis_galvo, (self.galvo_return, fill_samples), 'constant',
                                     constant_values=(self.dot_starts[1], self.dot_starts[1]))
            _sqr = np.pad(np.ones(self.samples_high), (0, self.samples_low), 'constant', constant_values=(0, 0))
            square_wave = np.pad(np.tile(_sqr, self.dot_pos.size),
                                 (self.samples_delay, self.samples_offset + self.ramp_down_samples), 'constant',
                                 constant_values=(0, 0))
            laser_trigger = np.tile(square_wave, self.dot_pos.size)
            return fast_axis_galvo, slow_axis_galvo, laser_trigger
        else:
            return

    def generate_digital_scanning_triggers(self, lasers, camera):
        cam_sw = self.galvo_sw_states[camera]
        cam_ind = camera + 4
        lasers = lasers.copy()
        if 0 in lasers:
            # galvo activation
            ramp_down_act = np.linspace(self.ramp_up_act[-1], self.ramp_up_act[0], num=self.ramp_down_samples_act,
                                        endpoint=True)
            extended_cycle_act = np.concatenate((self.ramp_up_act, ramp_down_act))
            fast_axis_galvo_act = np.tile(extended_cycle_act, self.dot_pos_act.size)
            slow_axis_galvo_act = np.zeros_like(fast_axis_galvo_act)
            indices_act = np.arange(self.ramp_up_samples_act + 1, len(fast_axis_galvo_act), extended_cycle_act.size)
            slow_axis_galvo_act[indices_act] = 1
            slow_axis_galvo_act = np.cumsum(slow_axis_galvo_act) * self.dot_step_y_act + self.dot_starts_act[1]
            slow_axis_galvo_act[-self.ramp_down_samples_act:] = np.linspace(
                slow_axis_galvo_act[-self.ramp_down_samples_act], self.dot_starts_act[1], self.ramp_down_samples_act)
            fill_samples_act = max(0, self.galvo_sw_settle_samples - (
                    self.samples_offset_act + self.ramp_down_samples_act))
            fast_axis_galvo_act = np.pad(fast_axis_galvo_act, (self.galvo_return, fill_samples_act), 'constant',
                                         constant_values=(self.galvo_starts_act[0], self.galvo_starts_act[0]))
            slow_axis_galvo_act = np.pad(slow_axis_galvo_act, (self.galvo_return, fill_samples_act), 'constant',
                                         constant_values=(self.dot_starts_act[1], self.dot_starts_act[1]))
            _sqr_act = np.pad(np.ones(self.samples_high_act), (0, self.samples_low_act), 'constant',
                              constant_values=(0, 0))
            square_wave_act = np.pad(np.tile(_sqr_act, self.dot_pos_act.size),
                                     (self.samples_delay_act, self.samples_offset_act + self.ramp_down_samples_act),
                                     'constant', constant_values=(0, 0))
            laser_trigger_act = np.tile(square_wave_act, self.dot_pos_act.size)
            if 3 in lasers:
                fast_axis_galvo_act[-fill_samples_act:] = self.galvo_starts[0]
                slow_axis_galvo_act[-fill_samples_act:] = self.dot_starts[0]
                laser_trigger_act = np.pad(laser_trigger_act, (self.galvo_return, fill_samples_act), 'constant',
                                           constant_values=(0, 0))
                switch_galvo_act = np.zeros(laser_trigger_act.shape)
                camera_trigger_act = np.zeros(laser_trigger_act.shape)
            else:
                switch_galvo_act = np.ones(fast_axis_galvo_act.shape) * cam_sw
                switch_galvo_act[:self.galvo_sw_settle_samples] = smooth_ramp(0., cam_sw, self.galvo_sw_settle_samples)
                switch_galvo_act[-self.galvo_sw_settle_samples:] = smooth_ramp(cam_sw, 0., self.galvo_sw_settle_samples)
                camera_trigger_act = np.ones(laser_trigger_act.shape, dtype=np.int8)
                camera_trigger_act[:self.samples_delay_act] = 0
                camera_trigger_act[- self.samples_offset_act - self.ramp_down_samples_act:] = 0
                laser_trigger_act = np.pad(laser_trigger_act, (self.galvo_return, fill_samples_act), 'constant',
                                           constant_values=(0, 0))
                camera_trigger_act = np.pad(camera_trigger_act, (self.galvo_return, fill_samples_act), 'constant',
                                            constant_values=(0, 0))
                tl = self.samples_delay_act + self.galvo_sw_settle_samples + self.galvo_return
                self.exposure_samples = camera_trigger_act.shape[0] - tl
                self.exposure_time = self.exposure_samples / self.sample_rate
        else:
            pass
        # galvo read out
        ramp_down = np.linspace(self.ramp_up[-1], self.ramp_up[0], num=self.ramp_down_samples, endpoint=True)
        extended_cycle = np.concatenate((self.ramp_up, ramp_down))
        fast_axis_galvo = np.tile(extended_cycle, self.dot_pos.size)
        slow_axis_galvo = np.zeros_like(fast_axis_galvo)
        indices = np.arange(self.ramp_up_samples + 1, len(fast_axis_galvo), extended_cycle.size)
        slow_axis_galvo[indices] = 1
        slow_axis_galvo = np.cumsum(slow_axis_galvo) * self.dot_step_y + self.dot_starts[1]
        slow_axis_galvo[-self.ramp_down_samples:] = np.linspace(slow_axis_galvo[-self.ramp_down_samples],
                                                                self.dot_starts[1], self.ramp_down_samples)
        fill_samples = max(0, self.galvo_sw_settle_samples - (self.samples_offset + self.ramp_down_samples))
        fast_axis_galvo = np.pad(fast_axis_galvo, (self.galvo_return, fill_samples), 'constant',
                                 constant_values=(self.galvo_starts[0], self.galvo_starts[0]))
        slow_axis_galvo = np.pad(slow_axis_galvo, (self.galvo_return, fill_samples), 'constant',
                                 constant_values=(self.dot_starts[1], self.dot_starts[1]))
        switch_galvo = np.ones(fast_axis_galvo.shape) * cam_sw
        switch_galvo[:self.galvo_sw_settle_samples] = smooth_ramp(0., cam_sw, self.galvo_sw_settle_samples)
        switch_galvo[-self.galvo_sw_settle_samples:] = smooth_ramp(cam_sw, 0., self.galvo_sw_settle_samples)
        _sqr = np.pad(np.ones(self.samples_high), (0, self.samples_low), 'constant', constant_values=(0, 0))
        square_wave = np.pad(np.tile(_sqr, self.dot_pos.size),
                             (self.samples_delay, self.samples_offset + self.ramp_down_samples), 'constant',
                             constant_values=(0, 0))
        laser_trigger = np.tile(square_wave, self.dot_pos.size)
        camera_trigger = np.ones(laser_trigger.shape, dtype=np.int8)
        camera_trigger[:self.samples_delay] = 0
        camera_trigger[- self.samples_offset - self.ramp_down_samples:] = 0
        laser_trigger = np.pad(laser_trigger, (self.galvo_return, fill_samples), 'constant', constant_values=(0, 0))
        camera_trigger = np.pad(camera_trigger, (self.galvo_return, fill_samples), 'constant', constant_values=(0, 0))
        tl = self.samples_delay + self.galvo_sw_settle_samples + self.galvo_return
        self.exposure_samples = camera_trigger.shape[0] - tl
        self.exposure_time = self.exposure_samples / self.sample_rate
        # all
        digital_sequences = [np.empty((0,)) for _ in range(len(lasers) + 1)]
        galvo_sequences = [np.empty((0,)) for _ in range(3)]
        for _, las in enumerate(lasers):
            if las == 0:
                trig = laser_trigger_act
                gvf = fast_axis_galvo_act
                gvs = slow_axis_galvo_act
                sw = switch_galvo_act
                cm = camera_trigger_act
            elif las == 1:
                itl = int(np.ceil(0.0008 * self.sample_rate))
                trig = np.pad(np.ones(self.digital_ends[las] - self.digital_starts[las]), (itl, itl), 'constant',
                              constant_values=(0, 0))
                gvf = np.ones(trig.shape) * fast_axis_galvo[0]
                gvs = np.ones(trig.shape) * slow_axis_galvo[0]
                sw = np.zeros(trig.shape)
                cm = np.zeros(trig.shape)
            elif las == 2:
                itl = int(np.ceil(0.0008 * self.sample_rate))
                trig = np.pad(np.ones(self.digital_ends[las] - self.digital_starts[las]), (itl, itl), 'constant',
                              constant_values=(0, 0))
                gvf = np.ones(trig.shape) * fast_axis_galvo[0]
                gvs = np.ones(trig.shape) * slow_axis_galvo[0]
                sw = np.zeros(trig.shape)
                cm = np.zeros(trig.shape)
            elif las == 3:
                trig = laser_trigger
                gvf = fast_axis_galvo
                gvs = slow_axis_galvo
                sw = switch_galvo
                cm = camera_trigger
            if (las == 2) and (1 in lasers):
                for i in range(len(lasers)):
                    if lasers[i] == 1:
                        temp = digital_sequences[i]
                    if lasers[i] == las:
                        digital_sequences[i] = temp
            else:
                galvo_sequences[0] = np.append(galvo_sequences[0], gvf)
                galvo_sequences[1] = np.append(galvo_sequences[1], gvs)
                digital_sequences[-1] = np.append(digital_sequences[-1], cm)
                galvo_sequences[2] = np.append(galvo_sequences[2], sw)
                for i in range(len(lasers)):
                    if lasers[i] == las:
                        digital_sequences[i] = np.append(digital_sequences[i], trig)
                    else:
                        digital_sequences[i] = np.append(digital_sequences[i], np.zeros(trig.shape))
        lasers.append(cam_ind)
        for i, dtr in enumerate(digital_sequences):
            digital_sequences[i] = np.append(dtr, dtr[-1] * np.ones(self.standby_samples))
        for i, gtr in enumerate(galvo_sequences):
            galvo_sequences[i] = np.append(gtr, gtr[-1] * np.ones(self.standby_samples))
        return np.asarray(digital_sequences), np.asarray(galvo_sequences), lasers

    def generate_roundtrip_digital_scanning_triggers(self, lasers, camera):
        cam_sw = self.galvo_sw_states[camera]
        cam_ind = camera + 4
        lasers = lasers.copy()
        lps = int(self.dot_pos_act.size / 2)
        dot_pos_act = self.dot_pos_act[:lps * 2]
        if 0 in lasers:
            # galvo activation
            ramp_down_act = np.flip(self.ramp_up_act)
            extended_cycle_act = np.concatenate((self.ramp_up_act, ramp_down_act))
            fast_axis_galvo_act = np.tile(extended_cycle_act, dot_pos_act.size)
            slow_axis_galvo_act = np.zeros_like(fast_axis_galvo_act)
            indices_act = np.arange(self.ramp_up_samples_act + 1, len(fast_axis_galvo_act), ramp_down_act.size)
            slow_axis_galvo_act[indices_act] = 1
            slow_axis_galvo_act = np.cumsum(slow_axis_galvo_act) * self.dot_step_y_act + self.dot_starts_act[1]
            slow_axis_galvo_act[-self.ramp_down_samples_act:] = np.linspace(
                slow_axis_galvo_act[-self.ramp_down_samples_act], self.dot_starts_act[1], self.ramp_down_samples_act)
            _sqr_act = np.pad(np.ones(self.samples_high_act), (0, self.samples_low_act), 'constant',
                              constant_values=(0, 0))
            square_wave_up_act = np.pad(np.tile(_sqr_act, self.dot_pos_act.size),
                                        (self.samples_delay_act, self.samples_offset_act), 'constant',
                                        constant_values=(0, 0))

            square_wave_down_act = np.pad(np.tile(_sqr_act, self.dot_pos_act.size),
                                          (self.samples_delay_act + self.ramp_down_offset,
                                           self.samples_offset_act - self.ramp_down_offset),
                                          'constant', constant_values=(0, 0))
            square_wave_act = np.concatenate((square_wave_up_act, square_wave_down_act))
            laser_trigger_act = np.tile(square_wave_act, self.dot_pos_act.size)
            fill_samples_act = max(0, self.galvo_sw_settle_samples - self.samples_offset_act)
            fast_axis_galvo_act = np.pad(fast_axis_galvo_act, (self.galvo_return, fill_samples_act), 'constant',
                                         constant_values=(self.galvo_starts_act[0], self.galvo_starts_act[0]))
            slow_axis_galvo_act = np.pad(slow_axis_galvo_act, (self.galvo_return, fill_samples_act), 'constant',
                                         constant_values=(self.dot_starts_act[1], self.dot_starts_act[1]))
            if 3 in lasers:
                fast_axis_galvo_act[-fill_samples_act:] = self.galvo_starts[0]
                slow_axis_galvo_act[-fill_samples_act:] = self.dot_starts[0]
                laser_trigger_act = np.pad(laser_trigger_act, (self.galvo_step_response, fill_samples_act), 'constant',
                                           constant_values=(0, 0))
                switch_galvo_act = np.zeros(laser_trigger_act.shape)
                camera_trigger_act = np.zeros(laser_trigger_act.shape)
            else:
                switch_galvo_act = np.ones(fast_axis_galvo_act.shape) * cam_sw
                switch_galvo_act[:self.galvo_sw_settle_samples] = smooth_ramp(0., cam_sw, self.galvo_sw_settle_samples)
                switch_galvo_act[-self.galvo_sw_settle_samples:] = smooth_ramp(cam_sw, 0., self.galvo_sw_settle_samples)
                camera_trigger_act = np.ones(laser_trigger_act.shape, dtype=np.int8)
                camera_trigger_act[:self.samples_delay_act] = 0
                camera_trigger_act[- self.samples_offset_act - self.ramp_down_samples_act:] = 0
                laser_trigger_act = np.pad(laser_trigger_act, (self.galvo_return, fill_samples_act), 'constant',
                                           constant_values=(0, 0))
                camera_trigger_act = np.pad(camera_trigger_act, (self.galvo_return, fill_samples_act), 'constant',
                                            constant_values=(0, 0))
                tl = self.samples_delay_act + self.galvo_sw_settle_samples + self.galvo_return
                self.exposure_samples = camera_trigger_act.shape[0] - tl
                self.exposure_time = self.exposure_samples / self.sample_rate
        else:
            pass
        # galvo read out
        ramp_down = np.linspace(self.ramp_up[-1], self.ramp_up[0], num=self.ramp_down_samples, endpoint=True)
        extended_cycle = np.concatenate((self.ramp_up, ramp_down))
        fast_axis_galvo = np.tile(extended_cycle, self.dot_pos.size)
        slow_axis_galvo = np.zeros_like(fast_axis_galvo)
        indices = np.arange(self.ramp_up_samples + 1, len(fast_axis_galvo), extended_cycle.size)
        slow_axis_galvo[indices] = 1
        slow_axis_galvo = np.cumsum(slow_axis_galvo) * self.dot_step_y + self.dot_starts[1]
        slow_axis_galvo[-self.ramp_down_samples:] = np.linspace(slow_axis_galvo[-self.ramp_down_samples],
                                                                self.dot_starts[1], self.ramp_down_samples)
        fill_samples = max(0, self.galvo_sw_settle_samples - (self.samples_offset + self.ramp_down_samples))
        fast_axis_galvo = np.pad(fast_axis_galvo, (self.galvo_return, fill_samples), 'constant',
                                 constant_values=(self.galvo_starts[0], self.galvo_starts[0]))
        slow_axis_galvo = np.pad(slow_axis_galvo, (self.galvo_return, fill_samples), 'constant',
                                 constant_values=(self.dot_starts[1], self.dot_starts[1]))
        switch_galvo = np.ones(fast_axis_galvo.shape) * cam_sw
        switch_galvo[:self.galvo_sw_settle_samples] = smooth_ramp(0., cam_sw, self.galvo_sw_settle_samples)
        switch_galvo[-self.galvo_sw_settle_samples:] = smooth_ramp(cam_sw, 0., self.galvo_sw_settle_samples)
        _sqr = np.pad(np.ones(self.samples_high), (0, self.samples_low), 'constant', constant_values=(0, 0))
        square_wave = np.pad(np.tile(_sqr, self.dot_pos.size),
                             (self.samples_delay, self.samples_offset + self.ramp_down_samples), 'constant',
                             constant_values=(0, 0))
        laser_trigger = np.tile(square_wave, self.dot_pos.size)
        camera_trigger = np.ones(laser_trigger.shape, dtype=np.int8)
        camera_trigger[:self.samples_delay] = 0
        camera_trigger[- self.samples_offset - self.ramp_down_samples:] = 0
        laser_trigger = np.pad(laser_trigger, (self.galvo_return, fill_samples), 'constant', constant_values=(0, 0))
        camera_trigger = np.pad(camera_trigger, (self.galvo_return, fill_samples), 'constant', constant_values=(0, 0))
        tl = self.samples_delay + self.galvo_sw_settle_samples + self.galvo_return
        self.exposure_samples = camera_trigger.shape[0] - tl
        self.exposure_time = self.exposure_samples / self.sample_rate
        # all
        digital_sequences = [np.empty((0,)) for _ in range(len(lasers) + 1)]
        galvo_sequences = [np.empty((0,)) for _ in range(3)]
        for _, las in enumerate(lasers):
            if las == 0:
                trig = laser_trigger_act
                gvf = fast_axis_galvo_act
                gvs = slow_axis_galvo_act
                sw = switch_galvo_act
                cm = camera_trigger_act
            elif las == 1:
                itl = int(np.ceil(0.0008 * self.sample_rate))
                trig = np.pad(np.ones(self.digital_ends[las] - self.digital_starts[las]), (itl, itl), 'constant',
                              constant_values=(0, 0))
                gvf = np.ones(trig.shape) * fast_axis_galvo[0]
                gvs = np.ones(trig.shape) * slow_axis_galvo[0]
                sw = np.zeros(trig.shape)
                cm = np.zeros(trig.shape)
            elif las == 2:
                itl = int(np.ceil(0.0008 * self.sample_rate))
                trig = np.pad(np.ones(self.digital_ends[las] - self.digital_starts[las]), (itl, itl), 'constant',
                              constant_values=(0, 0))
                gvf = np.ones(trig.shape) * fast_axis_galvo[0]
                gvs = np.ones(trig.shape) * slow_axis_galvo[0]
                sw = np.zeros(trig.shape)
                cm = np.zeros(trig.shape)
            elif las == 3:
                trig = laser_trigger
                gvf = fast_axis_galvo
                gvs = slow_axis_galvo
                sw = switch_galvo
                cm = camera_trigger
            if (las == 2) and (1 in lasers):
                for i in range(len(lasers)):
                    if lasers[i] == 1:
                        temp = digital_sequences[i]
                    if lasers[i] == las:
                        digital_sequences[i] = temp
            else:
                galvo_sequences[0] = np.append(galvo_sequences[0], gvf)
                galvo_sequences[1] = np.append(galvo_sequences[1], gvs)
                digital_sequences[-1] = np.append(digital_sequences[-1], cm)
                galvo_sequences[2] = np.append(galvo_sequences[2], sw)
                for i in range(len(lasers)):
                    if lasers[i] == las:
                        digital_sequences[i] = np.append(digital_sequences[i], trig)
                    else:
                        digital_sequences[i] = np.append(digital_sequences[i], np.zeros(trig.shape))
        lasers.append(cam_ind)
        for i, dtr in enumerate(digital_sequences):
            digital_sequences[i] = np.append(dtr, dtr[-1] * np.ones(self.standby_samples))
        for i, gtr in enumerate(galvo_sequences):
            galvo_sequences[i] = np.append(gtr, gtr[-1] * np.ones(self.standby_samples))
        return np.asarray(digital_sequences), np.asarray(galvo_sequences), lasers

    def generate_dotscan_resolft_2d(self, lasers, camera):
        cam_sw = self.galvo_sw_states[camera]
        cam_ind = camera + 4
        lasers = lasers.copy()
        # read out galvo
        ramp_down = np.linspace(self.ramp_up[-1], self.ramp_up[0], num=self.ramp_down_samples, endpoint=True)
        extended_cycle = np.concatenate((self.ramp_up, ramp_down))
        fast_axis_galvo = np.tile(extended_cycle, self.dot_pos.size)
        slow_axis_galvo = np.zeros_like(fast_axis_galvo)
        indices = np.arange(self.ramp_up_samples + 1, len(fast_axis_galvo), extended_cycle.size)
        slow_axis_galvo[indices] = 1
        slow_axis_galvo = np.cumsum(slow_axis_galvo) * self.dot_step_y + self.dot_starts[1]
        slow_axis_galvo[-self.ramp_down_samples:] = np.linspace(slow_axis_galvo[-self.ramp_down_samples],
                                                                self.dot_starts[1], self.ramp_down_samples)
        fill_samples = max(0, self.galvo_sw_settle_samples - (self.samples_offset + self.ramp_down_samples))
        fast_axis_galvo = np.pad(fast_axis_galvo, (self.galvo_return, fill_samples), 'constant',
                                 constant_values=(self.galvo_starts[0], self.galvo_starts[0]))
        slow_axis_galvo = np.pad(slow_axis_galvo, (self.galvo_return, fill_samples), 'constant',
                                 constant_values=(self.dot_starts[1], self.dot_starts[1]))
        _sqr = np.pad(np.ones(self.samples_high), (0, self.samples_low), 'constant', constant_values=(0, 0))
        square_wave = np.pad(np.tile(_sqr, self.dot_pos.size),
                             (self.samples_delay, self.samples_offset + self.ramp_down_samples), 'constant',
                             constant_values=(0, 0))
        laser_trigger = np.tile(square_wave, self.dot_pos.size)
        camera_trigger = np.ones(laser_trigger.shape, dtype=np.int8)
        camera_trigger[:self.samples_delay] = 0
        camera_trigger[- self.samples_offset - self.ramp_down_samples:] = 0
        laser_trigger = np.pad(laser_trigger, (self.galvo_return, fill_samples), 'constant', constant_values=(0, 0))
        camera_trigger = np.pad(camera_trigger, (self.galvo_return, fill_samples), 'constant', constant_values=(0, 0))
        tl = self.samples_delay + self.galvo_sw_settle_samples + self.galvo_return
        self.exposure_samples = camera_trigger.shape[0] - tl
        self.exposure_time = self.exposure_samples / self.sample_rate
        # activation galvo
        ramp_down_act = np.linspace(self.ramp_up_act[-1], self.ramp_up_act[0], num=self.ramp_down_samples_act,
                                    endpoint=True)
        extended_cycle_act = np.concatenate((self.ramp_up_act, ramp_down_act))
        fast_axis_galvo_act = np.tile(extended_cycle_act, self.dot_pos_act.size)
        slow_axis_galvo_act = np.zeros_like(fast_axis_galvo_act)
        indices_act = np.arange(self.ramp_up_samples_act + 1, len(fast_axis_galvo_act), extended_cycle_act.size)
        slow_axis_galvo_act[indices_act] = 1
        slow_axis_galvo_act = np.cumsum(slow_axis_galvo_act) * self.dot_step_y_act + self.dot_starts_act[1]
        slow_axis_galvo_act[-self.ramp_down_samples_act:] = np.linspace(
            slow_axis_galvo_act[-self.ramp_down_samples_act], self.dot_starts_act[1], self.ramp_down_samples_act)
        fill_samples_act = max(0, self.galvo_sw_settle_samples - (self.samples_offset_act + self.ramp_down_samples_act))
        fast_axis_galvo_act = np.pad(fast_axis_galvo_act, (self.galvo_return, fill_samples_act), 'constant',
                                     constant_values=(self.galvo_starts_act[0], self.galvo_starts_act[0]))
        slow_axis_galvo_act = np.pad(slow_axis_galvo_act, (self.galvo_return, fill_samples_act), 'constant',
                                     constant_values=(self.dot_starts_act[1], self.dot_starts_act[1]))
        _sqr_act = np.pad(np.ones(self.samples_high_act), (0, self.samples_low_act), 'constant', constant_values=(0, 0))
        square_wave_act = np.pad(np.tile(_sqr_act, self.dot_pos_act.size),
                                 (self.samples_delay_act, self.samples_offset_act + self.ramp_down_samples_act),
                                 'constant', constant_values=(0, 0))
        laser_trigger_act = np.tile(square_wave_act, self.dot_pos_act.size)
        fast_axis_galvo_act[-fill_samples_act:] = self.galvo_starts[0]
        slow_axis_galvo_act[-fill_samples_act:] = self.dot_starts[0]
        laser_trigger_act = np.pad(laser_trigger_act, (self.galvo_return, fill_samples_act), 'constant',
                                   constant_values=(0, 0))
        camera_trigger_act = np.zeros(laser_trigger_act.shape)
        # switching galvo
        switch_galvo = np.ones(fast_axis_galvo.shape) * cam_sw
        switch_galvo[:self.galvo_sw_settle_samples] = smooth_ramp(0., cam_sw, self.galvo_sw_settle_samples)
        switch_galvo[-self.galvo_sw_settle_samples:] = smooth_ramp(cam_sw, 0., self.galvo_sw_settle_samples)
        # all
        digital_sequences = [np.empty((0,)) for _ in range(len(lasers) + 1)]
        galvo_sequences = [np.empty((0,)) for _ in range(3)]
        for _, las in enumerate(lasers):
            if las == 0:
                trig = laser_trigger_act
                gvf = fast_axis_galvo_act
                gvs = slow_axis_galvo_act
                sw = np.zeros(trig.shape)
                cm = np.zeros(trig.shape)
            elif las == 1:
                itl = int(np.ceil(0.0008 * self.sample_rate))
                trig = np.pad(np.ones(self.digital_ends[las] - self.digital_starts[las]), (itl, itl), 'constant',
                              constant_values=(0, 0))
                gvf = np.ones(trig.shape) * fast_axis_galvo[0]
                gvs = np.ones(trig.shape) * slow_axis_galvo[0]
                sw = np.zeros(trig.shape)
                cm = np.zeros(trig.shape)
            elif las == 2:
                itl = int(np.ceil(0.0008 * self.sample_rate))
                trig = np.pad(np.ones(self.digital_ends[las] - self.digital_starts[las]), (itl, itl), 'constant',
                              constant_values=(0, 0))
                gvf = np.ones(trig.shape) * fast_axis_galvo[0]
                gvs = np.ones(trig.shape) * slow_axis_galvo[0]
                sw = np.zeros(trig.shape)
                cm = np.zeros(trig.shape)
            elif las == 3:
                trig = laser_trigger
                gvf = fast_axis_galvo
                gvs = slow_axis_galvo
                sw = switch_galvo
                cm = camera_trigger
            if (las == 2) and (1 in lasers):
                for i in range(len(lasers)):
                    if lasers[i] == 1:
                        temp = digital_sequences[i]
                    if lasers[i] == las:
                        digital_sequences[i] = temp
            else:
                galvo_sequences[0] = np.append(galvo_sequences[0], gvf)
                galvo_sequences[1] = np.append(galvo_sequences[1], gvs)
                digital_sequences[-1] = np.append(digital_sequences[-1], cm)
                galvo_sequences[2] = np.append(galvo_sequences[2], sw)
                for i in range(len(lasers)):
                    if lasers[i] == las:
                        digital_sequences[i] = np.append(digital_sequences[i], trig)
                    else:
                        digital_sequences[i] = np.append(digital_sequences[i], np.zeros(trig.shape))
        lasers.append(cam_ind)
        idle_samples = max(self.standby_samples, self.return_samples)
        for i, dtr in enumerate(digital_sequences):
            digital_sequences[i] = np.append(dtr, dtr[-1] * np.ones(idle_samples))
        for i, gtr in enumerate(galvo_sequences):
            galvo_sequences[i] = np.append(gtr, gtr[-1] * np.ones(idle_samples))
        piezo_sequences = [np.empty((0,)) for _ in range(2)]
        piezo_sequences[0] = np.repeat(self.piezo_scan_positions[0], digital_sequences[0].shape[0])
        piezo_sequences[0] = shift_array(piezo_sequences[0], idle_samples, piezo_sequences[0][0], "backward")
        piezo_sequences[0][-idle_samples:] = piezo_sequences[0][0]
        for i, dtr in enumerate(digital_sequences):
            digital_sequences[i] = np.tile(dtr, self.piezo_scan_pos[0])
        for i, gtr in enumerate(galvo_sequences):
            galvo_sequences[i] = np.tile(gtr, self.piezo_scan_pos[0])
        piezo_sequences[0] = np.tile(piezo_sequences[0], self.piezo_scan_pos[1])
        piezo_sequences[1] = np.repeat(self.piezo_scan_positions[1], digital_sequences[0].shape[0])
        piezo_sequences[1] = shift_array(piezo_sequences[1], idle_samples, piezo_sequences[1][0], "backward")
        for i, dtr in enumerate(digital_sequences):
            digital_sequences[i] = np.tile(dtr, self.piezo_scan_pos[1])
        for i, gtr in enumerate(galvo_sequences):
            galvo_sequences[i] = np.tile(gtr, self.piezo_scan_pos[1])
        scan_pos = self.piezo_scan_pos[0] * self.piezo_scan_pos[1]
        self.logg.info("\nGalvo start, and stop: {} \n"
                       "Dot start, step, range, and numbers: {} \n"
                       "Piezo starts: {} \n"
                       "Piezo steps: {} \n"
                       "Piezo ranges: {} \n"
                       "Piezo positions: {}".format([self.galvo_starts, self.galvo_stops],
                                                    [self.dot_starts, [self.dot_step_v, self.dot_step_y],
                                                     self.dot_ranges, self.dot_pos.size], self.piezo_starts,
                                                    self.piezo_steps, self.piezo_ranges, scan_pos))
        return np.asarray(galvo_sequences), np.asarray(piezo_sequences), np.asarray(digital_sequences), lasers, scan_pos

    def generate_monalisa_scan_2d(self, lasers, camera):
        cam_sw = self.galvo_sw_states[camera]
        cam_ind = camera + 4
        lasers = lasers.copy()
        interval_samples = max(self.initial_samples, self.galvo_sw_settle_samples)
        if interval_samples > self.digital_starts[cam_ind]:
            offset_samples = interval_samples - self.digital_starts[cam_ind]
            self.digital_starts = [(_start + offset_samples) for _start in self.digital_starts]
            self.digital_ends = [(_end + offset_samples) for _end in self.digital_ends]
        cycle_samples = self.digital_ends[cam_ind] + max(self.standby_samples, self.return_samples)
        digital_trigger = np.zeros((len(lasers) + 1, cycle_samples), dtype=np.int8)
        switch_trigger = cam_sw * np.ones(cycle_samples, dtype=np.float16)
        self.exposure_samples = self.digital_ends[cam_ind] - self.digital_starts[cam_ind]
        self.exposure_time = self.exposure_samples / self.sample_rate
        digital_trigger[-1, self.digital_starts[cam_ind]:self.digital_ends[cam_ind]] = 1
        for ln, laser in enumerate(lasers):
            digital_trigger[ln, self.digital_starts[laser]:self.digital_ends[laser]] = 1
        switch_trigger[:self.digital_starts[cam_ind] - self.galvo_sw_settle_samples] = 0.
        switch_trigger[
        self.digital_starts[cam_ind] - self.galvo_sw_settle_samples:self.digital_starts[cam_ind]] = smooth_ramp(0.,
                                                                                                                cam_sw,
                                                                                                                self.galvo_sw_settle_samples)
        switch_trigger[
        self.digital_ends[cam_ind]:self.digital_ends[cam_ind] + self.galvo_sw_settle_samples] = smooth_ramp(cam_sw, 0.,
                                                                                                            self.galvo_sw_settle_samples)
        switch_trigger[self.digital_ends[cam_ind] + self.galvo_sw_settle_samples:] = 0.
        switch_trigger = np.tile(switch_trigger, self.piezo_scan_pos[0])
        digital_sequences = [np.empty((0,)) for _ in range(len(lasers) + 1)]
        for i, dtr in enumerate(digital_trigger):
            digital_sequences[i] = np.tile(dtr, self.piezo_scan_pos[0])
        lasers.append(cam_ind)
        piezo_sequences = [np.empty((0,)) for _ in range(2)]
        piezo_sequences[0] = np.repeat(self.piezo_scan_positions[0], cycle_samples)
        piezo_sequences[0] = shift_array(piezo_sequences[0], max(self.standby_samples, self.return_samples),
                                         fill=piezo_sequences[0][0], direction="backward")
        piezo_sequences[0] = np.tile(piezo_sequences[0], self.piezo_scan_pos[1])
        piezo_sequences[1] = np.repeat(self.piezo_scan_positions[1], cycle_samples * self.piezo_scan_pos[0])
        piezo_sequences[1] = shift_array(piezo_sequences[1], max(self.standby_samples, self.return_samples),
                                         fill=piezo_sequences[1][0], direction="backward")
        switch_trigger = np.tile(switch_trigger, self.piezo_scan_pos[1])
        for i, dtr in enumerate(digital_sequences):
            digital_sequences[i] = np.tile(dtr, self.piezo_scan_pos[1])
        return np.asarray(digital_sequences), switch_trigger, piezo_sequences, lasers, self.piezo_scan_pos[2]

    def generate_piezo_line_scan(self, lasers, camera):
        cam_sw = self.galvo_sw_states[camera]
        lasers = lasers.copy()
        cam_ind = camera + 4
        scan_samples = int(0.064 * self.sample_rate)
        interval_samples = int(0.016 * self.sample_rate)
        piezo_sequences = [np.empty((0,)) for _ in range(2)]
        temp = np.concatenate((smooth_ramp(1.0, 9.0, scan_samples, 0.9), smooth_ramp(9.0, 1.0, scan_samples, 0.9)))
        piezo_sequences[0] = np.pad(temp,
                                    (self.initial_samples, 2 * scan_samples + interval_samples + self.standby_samples),
                                    'constant', constant_values=(1, 1))
        piezo_sequences[1] = np.pad(temp,
                                    (self.initial_samples + 2 * scan_samples + interval_samples, self.standby_samples),
                                    'constant', constant_values=(1, 1))
        cycle_samples = 4 * scan_samples + self.initial_samples + interval_samples + self.standby_samples
        switch_trigger = cam_sw * np.ones(cycle_samples, dtype=np.float16)
        switch_trigger[:self.initial_samples - self.galvo_sw_settle_samples] = 0.
        switch_trigger[-self.standby_samples:] = 0.
        digital_triggers = np.zeros((len(lasers) + 1, cycle_samples), dtype=np.int8)
        digital_triggers[-1, self.initial_samples:] = 1
        digital_triggers[-1, -self.standby_samples:] = 0
        for ln, laser in enumerate(lasers):
            digital_triggers[ln, self.initial_samples:self.initial_samples + 2 * scan_samples] = 1
            digital_triggers[ln, -2 * scan_samples - self.standby_samples:- self.standby_samples] = 1
        lasers.append(cam_ind)
        return digital_triggers, switch_trigger, np.asarray(piezo_sequences), lasers

    def update_lightsheet_rolling(self, interval_line_number):
        self.line_interval_samples = int(np.ceil(((
                                                          self.samples_high + self.samples_low) * self.dot_pos.size + self.samples_delay + self.samples_offset + self.ramp_down_samples) / interval_line_number))
        self.line_exposure_samples = (self.samples_high + self.samples_low) * self.dot_pos.size
        self.trigger_delay_samples = 10 * self.line_interval_samples
        return self.line_exposure_samples / self.sample_rate, self.line_interval_samples / self.sample_rate

    def generate_digital_scanning_triggers_rolling(self, lasers, camera):
        cam_ind = camera + 4
        lasers = lasers.copy()
        offset_samples = max(self.trigger_delay_samples + 2, self.galvo_return)
        if 0 in lasers:
            # galvo activation
            ramp_down_act = np.linspace(self.ramp_up_act[-1], self.ramp_up_act[0], num=self.ramp_down_samples_act,
                                        endpoint=True)
            extended_cycle_act = np.concatenate((self.ramp_up_act, ramp_down_act))
            fast_axis_galvo_act = np.tile(extended_cycle_act, self.dot_pos_act.size)
            slow_axis_galvo_act = np.zeros_like(fast_axis_galvo_act)
            indices_act = np.arange(self.ramp_up_samples_act + 1, len(fast_axis_galvo_act), extended_cycle_act.size)
            slow_axis_galvo_act[indices_act] = 1
            slow_axis_galvo_act = np.cumsum(slow_axis_galvo_act) * self.dot_step_y_act + self.dot_starts_act[1]
            slow_axis_galvo_act[-self.ramp_down_samples_act:] = np.linspace(
                slow_axis_galvo_act[-self.ramp_down_samples_act], self.dot_starts_act[1], self.ramp_down_samples_act)
            _sqr_act = np.pad(np.ones(self.samples_high_act), (0, self.samples_low_act), 'constant',
                              constant_values=(0, 0))
            square_wave_act = np.pad(np.tile(_sqr_act, self.dot_pos_act.size),
                                     (self.samples_delay_act, self.samples_offset_act + self.ramp_down_samples_act),
                                     'constant', constant_values=(0, 0))
            laser_trigger_act = np.tile(square_wave_act, self.dot_pos_act.size)
            if 3 in lasers:
                fast_axis_galvo_act = np.pad(fast_axis_galvo_act, (4, 4), 'constant',
                                             constant_values=(self.galvo_starts_act[0], self.galvo_starts[0]))
                slow_axis_galvo_act = np.pad(slow_axis_galvo_act, (4, 4), 'constant',
                                             constant_values=(self.dot_starts_act[1], self.dot_starts[0]))
                laser_trigger_act = np.pad(laser_trigger_act, (4, 4), 'constant', constant_values=(0, 0))
                camera_trigger_act = np.zeros(laser_trigger_act.shape)
            else:
                fast_axis_galvo_act = np.pad(fast_axis_galvo_act, (offset_samples, self.readout_timing_samples),
                                             'constant',
                                             constant_values=(self.galvo_starts_act[0], self.galvo_starts_act[0]))
                slow_axis_galvo_act = np.pad(slow_axis_galvo_act, (offset_samples, self.readout_timing_samples),
                                             'constant',
                                             constant_values=(self.dot_starts_act[1], self.dot_starts_act[1]))
                laser_trigger_act = np.pad(laser_trigger_act, (offset_samples, self.readout_timing_samples), 'constant',
                                           constant_values=(0, 0))
                camera_trigger_act = np.ones(laser_trigger_act.shape, dtype=np.int8)
                camera_trigger_act[:2] = 0
                camera_trigger_act[self.trigger_delay_samples - 2:] = 0
        # galvo read out
        ramp_down = np.linspace(self.ramp_up[-1], self.ramp_up[0], num=self.ramp_down_samples, endpoint=True)
        extended_cycle = np.concatenate((self.ramp_up, ramp_down))
        fast_axis_galvo = np.tile(extended_cycle, self.dot_pos.size)
        slow_axis_galvo = np.zeros_like(fast_axis_galvo)
        indices = np.arange(self.ramp_up_samples + 1, len(fast_axis_galvo), extended_cycle.size)
        slow_axis_galvo[indices] = 1
        slow_axis_galvo = np.cumsum(slow_axis_galvo) * self.dot_step_y + self.dot_starts[1]
        slow_axis_galvo[-self.ramp_down_samples:] = np.linspace(slow_axis_galvo[-self.ramp_down_samples],
                                                                self.dot_starts[1], self.ramp_down_samples)
        _sqr = np.pad(np.ones(self.samples_high), (0, self.samples_low), 'constant', constant_values=(0, 0))
        square_wave = np.pad(np.tile(_sqr, self.dot_pos.size),
                             (self.samples_delay, self.samples_offset + self.ramp_down_samples), 'constant',
                             constant_values=(0, 0))
        laser_trigger = np.tile(square_wave, self.dot_pos.size)
        fast_axis_galvo = np.pad(fast_axis_galvo, (offset_samples, self.readout_timing_samples), 'constant',
                                 constant_values=(self.galvo_starts[0], self.galvo_starts[0]))
        slow_axis_galvo = np.pad(slow_axis_galvo, (offset_samples, self.readout_timing_samples), 'constant',
                                 constant_values=(self.dot_starts[1], self.dot_starts[1]))
        laser_trigger = np.pad(laser_trigger, (offset_samples, self.readout_timing_samples), 'constant',
                               constant_values=(0, 0))
        camera_trigger = np.ones(laser_trigger.shape, dtype=np.int8)
        camera_trigger[:2] = 0
        camera_trigger[self.trigger_delay_samples - 2:] = 0
        # all
        digital_sequences = [np.empty((0,)) for _ in range(len(lasers) + 1)]
        galvo_sequences = [np.empty((0,)) for _ in range(2)]
        for _, las in enumerate(lasers):
            if las == 0:
                trig = laser_trigger_act
                gvf = fast_axis_galvo_act
                gvs = slow_axis_galvo_act
                cm = camera_trigger_act
            if las == 1:
                itl = int(np.ceil(0.0008 * self.sample_rate))
                trig = np.pad(np.ones(self.digital_ends[las] - self.digital_starts[las]), (itl, itl), 'constant',
                              constant_values=(0, 0))
                gvf = np.ones(trig.shape) * fast_axis_galvo[0]
                gvs = np.ones(trig.shape) * slow_axis_galvo[0]
                cm = np.zeros(trig.shape)
            if las == 2:
                itl = int(np.ceil(0.0008 * self.sample_rate))
                trig = np.pad(np.ones(self.digital_ends[las] - self.digital_starts[las]), (itl, itl), 'constant',
                              constant_values=(0, 0))
                gvf = np.ones(trig.shape) * fast_axis_galvo[0]
                gvs = np.ones(trig.shape) * slow_axis_galvo[0]
                cm = np.zeros(trig.shape)
            if las == 3:
                trig = laser_trigger
                gvf = fast_axis_galvo
                gvs = slow_axis_galvo
                cm = camera_trigger
            if (las == 2) and (1 in lasers):
                for i in range(len(lasers)):
                    if lasers[i] == 1:
                        temp = digital_sequences[i]
                    if lasers[i] == las:
                        digital_sequences[i] = temp
            else:
                galvo_sequences[0] = np.append(galvo_sequences[0], gvf)
                galvo_sequences[1] = np.append(galvo_sequences[1], gvs)
                digital_sequences[-1] = np.append(digital_sequences[-1], cm)
                for i in range(len(lasers)):
                    if lasers[i] == las:
                        digital_sequences[i] = np.append(digital_sequences[i], trig)
                    else:
                        digital_sequences[i] = np.append(digital_sequences[i], np.zeros(trig.shape))
        lasers.append(cam_ind)
        return np.asarray(digital_sequences), np.asarray(galvo_sequences), lasers

    def generate_dotscan_resolft_2d_rolling(self, lasers, camera):
        cam_ind = camera + 4
        lasers = lasers.copy()
        # read out galvo
        ramp_down = np.linspace(self.ramp_up[-1], self.ramp_up[0], num=self.ramp_down_samples, endpoint=True)
        extended_cycle = np.concatenate((self.ramp_up, ramp_down))
        fast_axis_galvo = np.tile(extended_cycle, self.dot_pos.size)
        slow_axis_galvo = np.zeros_like(fast_axis_galvo)
        indices = np.arange(self.ramp_up_samples + 1, len(fast_axis_galvo), extended_cycle.size)
        slow_axis_galvo[indices] = 1
        slow_axis_galvo = np.cumsum(slow_axis_galvo) * self.dot_step_y + self.dot_starts[1]
        slow_axis_galvo[-self.ramp_down_samples:] = np.linspace(slow_axis_galvo[-self.ramp_down_samples],
                                                                self.dot_starts[1], self.ramp_down_samples)
        fill_samples = max(0, self.galvo_sw_settle_samples - (self.samples_offset + self.ramp_down_samples))
        fast_axis_galvo = np.pad(fast_axis_galvo, (self.galvo_return, fill_samples), 'constant',
                                 constant_values=(self.galvo_starts[0], self.galvo_starts[0]))
        slow_axis_galvo = np.pad(slow_axis_galvo, (self.galvo_return, fill_samples), 'constant',
                                 constant_values=(self.dot_starts[1], self.dot_starts[1]))
        _sqr = np.pad(np.ones(self.samples_high), (0, self.samples_low), 'constant', constant_values=(0, 0))
        square_wave = np.pad(np.tile(_sqr, self.dot_pos.size),
                             (self.samples_delay, self.samples_offset + self.ramp_down_samples), 'constant',
                             constant_values=(0, 0))
        laser_trigger = np.tile(square_wave, self.dot_pos.size)
        camera_trigger = np.ones(laser_trigger.shape, dtype=np.int8)
        camera_trigger[:self.samples_delay] = 0
        camera_trigger[- self.samples_offset - self.ramp_down_samples:] = 0
        laser_trigger = np.pad(laser_trigger, (self.galvo_return, fill_samples), 'constant', constant_values=(0, 0))
        camera_trigger = np.pad(camera_trigger, (self.galvo_return, fill_samples), 'constant', constant_values=(0, 0))
        tl = self.samples_delay + self.galvo_sw_settle_samples + self.galvo_return
        self.exposure_samples = camera_trigger.shape[0] - tl
        self.exposure_time = self.exposure_samples / self.sample_rate
        # activation galvo
        ramp_down_act = np.linspace(self.ramp_up_act[-1], self.ramp_up_act[0], num=self.ramp_down_samples_act,
                                    endpoint=True)
        extended_cycle_act = np.concatenate((self.ramp_up_act, ramp_down_act))
        fast_axis_galvo_act = np.tile(extended_cycle_act, self.dot_pos_act.size)
        slow_axis_galvo_act = np.zeros_like(fast_axis_galvo_act)
        indices_act = np.arange(self.ramp_up_samples_act + 1, len(fast_axis_galvo_act), extended_cycle_act.size)
        slow_axis_galvo_act[indices_act] = 1
        slow_axis_galvo_act = np.cumsum(slow_axis_galvo_act) * self.dot_step_y_act + self.dot_starts_act[1]
        slow_axis_galvo_act[-self.ramp_down_samples_act:] = np.linspace(
            slow_axis_galvo_act[-self.ramp_down_samples_act], self.dot_starts_act[1], self.ramp_down_samples_act)
        fill_samples_act = max(0, self.galvo_sw_settle_samples - (self.samples_offset_act + self.ramp_down_samples_act))
        fast_axis_galvo_act = np.pad(fast_axis_galvo_act, (self.galvo_return, fill_samples_act), 'constant',
                                     constant_values=(self.galvo_starts_act[0], self.galvo_starts_act[0]))
        slow_axis_galvo_act = np.pad(slow_axis_galvo_act, (self.galvo_return, fill_samples_act), 'constant',
                                     constant_values=(self.dot_starts_act[1], self.dot_starts_act[1]))
        _sqr_act = np.pad(np.ones(self.samples_high_act), (0, self.samples_low_act), 'constant', constant_values=(0, 0))
        square_wave_act = np.pad(np.tile(_sqr_act, self.dot_pos_act.size),
                                 (self.samples_delay_act, self.samples_offset_act + self.ramp_down_samples_act),
                                 'constant', constant_values=(0, 0))
        laser_trigger_act = np.tile(square_wave_act, self.dot_pos_act.size)
        fast_axis_galvo_act[-fill_samples_act:] = self.galvo_starts[0]
        slow_axis_galvo_act[-fill_samples_act:] = self.dot_starts[0]
        laser_trigger_act = np.pad(laser_trigger_act, (self.galvo_return, fill_samples_act), 'constant',
                                   constant_values=(0, 0))
        # all
        digital_sequences = [np.empty((0,)) for _ in range(len(lasers) + 1)]
        galvo_sequences = [np.empty((0,)) for _ in range(3)]
        for _, las in enumerate(lasers):
            if las == 0:
                trig = laser_trigger_act
                gvf = fast_axis_galvo_act
                gvs = slow_axis_galvo_act
                cm = np.zeros(trig.shape)
            elif las == 1:
                itl = int(np.ceil(0.0008 * self.sample_rate))
                trig = np.pad(np.ones(self.digital_ends[las] - self.digital_starts[las]), (itl, itl), 'constant',
                              constant_values=(0, 0))
                gvf = np.ones(trig.shape) * fast_axis_galvo[0]
                gvs = np.ones(trig.shape) * slow_axis_galvo[0]
                cm = np.zeros(trig.shape)
            elif las == 2:
                itl = int(np.ceil(0.0008 * self.sample_rate))
                trig = np.pad(np.ones(self.digital_ends[las] - self.digital_starts[las]), (itl, itl), 'constant',
                              constant_values=(0, 0))
                gvf = np.ones(trig.shape) * fast_axis_galvo[0]
                gvs = np.ones(trig.shape) * slow_axis_galvo[0]
                cm = np.zeros(trig.shape)
            elif las == 3:
                trig = laser_trigger
                gvf = fast_axis_galvo
                gvs = slow_axis_galvo
                cm = camera_trigger
            galvo_sequences[0] = np.append(galvo_sequences[0], gvf)
            galvo_sequences[1] = np.append(galvo_sequences[1], gvs)
            digital_sequences[-1] = np.append(digital_sequences[-1], cm)
            for i in range(len(lasers)):
                if lasers[i] == las:
                    digital_sequences[i] = np.append(digital_sequences[i], trig)
                else:
                    digital_sequences[i] = np.append(digital_sequences[i], np.zeros(trig.shape))
        lasers.append(cam_ind)
        idle_samples = max(self.standby_samples, self.return_samples)
        for i, dtr in enumerate(digital_sequences):
            digital_sequences[i] = np.append(dtr, dtr[-1] * np.ones(idle_samples))
        for i, gtr in enumerate(galvo_sequences):
            galvo_sequences[i] = np.append(gtr, gtr[-1] * np.ones(idle_samples))
        piezo_sequences = [np.empty((0,)) for _ in range(2)]
        piezo_sequences[0] = np.repeat(self.piezo_scan_positions[0], digital_sequences[0].shape[0])
        piezo_sequences[0] = shift_array(piezo_sequences[0], idle_samples, piezo_sequences[0][0], "backward")
        piezo_sequences[0][-idle_samples:] = piezo_sequences[0][0]
        for i, dtr in enumerate(digital_sequences):
            digital_sequences[i] = np.tile(dtr, self.piezo_scan_pos[0])
        for i, gtr in enumerate(galvo_sequences):
            galvo_sequences[i] = np.tile(gtr, self.piezo_scan_pos[0])
        piezo_sequences[0] = np.tile(piezo_sequences[0], self.piezo_scan_pos[1])
        piezo_sequences[1] = np.repeat(self.piezo_scan_positions[1], digital_sequences[0].shape[0])
        piezo_sequences[1] = shift_array(piezo_sequences[1], idle_samples, piezo_sequences[1][0], "backward")
        for i, dtr in enumerate(digital_sequences):
            digital_sequences[i] = np.tile(dtr, self.piezo_scan_pos[1])
        for i, gtr in enumerate(galvo_sequences):
            galvo_sequences[i] = np.tile(gtr, self.piezo_scan_pos[1])
        scan_pos = self.piezo_scan_pos[0] * self.piezo_scan_pos[1]
        self.logg.info("\nGalvo start, and stop: {} \n"
                       "Dot start, step, range, and numbers: {} \n"
                       "Piezo starts: {} \n"
                       "Piezo steps: {} \n"
                       "Piezo ranges: {} \n"
                       "Piezo positions: {}".format([self.galvo_starts, self.galvo_stops],
                                                    [self.dot_starts, [self.dot_step_v, self.dot_step_y],
                                                     self.dot_ranges, self.dot_pos.size], self.piezo_starts,
                                                    self.piezo_steps, self.piezo_ranges, scan_pos))
        return np.asarray(galvo_sequences), np.asarray(piezo_sequences), np.asarray(digital_sequences), lasers, scan_pos


def smooth_ramp(start, end, samples, curve_half=0.02):
    n = int(curve_half * samples)
    x = np.linspace(0, np.pi / 2, n, endpoint=True)
    signal_first_half = np.sin(x) * (end - start) / np.sin(np.pi / 2) + start
    signal_second_half = np.full(samples - n, end)
    return np.concatenate((signal_first_half, signal_second_half), dtype=np.float16)


def shift_array(arr, shift_length, fill=None, direction='backward'):
    if len(arr) == 0 or shift_length == 0:
        return arr
    shifted_array = np.empty_like(arr)
    shift_length = abs(shift_length) % len(arr)
    if fill is not None:
        last_element = fill
    else:
        if direction == 'forward':
            last_element = arr[0]
        elif direction == 'backward':
            last_element = arr[-1]
    if direction == 'forward':
        if shift_length < len(arr):
            shifted_array[shift_length:] = arr[:-shift_length]
        shifted_array[:shift_length] = last_element
    elif direction == 'backward':
        if shift_length < len(arr):
            shifted_array[:-shift_length] = arr[shift_length:]
        shifted_array[-shift_length:] = last_element
    return shifted_array


def safe_divide(numerator, denominator):
    try:
        return numerator / denominator
    except ZeroDivisionError:
        return 0
