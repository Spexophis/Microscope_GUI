import numpy as np


class TriggerSequence:
    class TriggerParameters:
        def __init__(self, sample_rate=2.5e5):
            # daq
            self.sample_rate = sample_rate  # Hz
            # digital triggers
            self.digital_starts = [0.000000, 0.010100, 0.010140, 0.010100]
            self.digital_ends = [0.010000, 0.010104, 0.010640, 0.011100]
            self.digital_starts = [int(digital_start * self.sample_rate) for digital_start in self.digital_starts]
            self.digital_ends = [int(digital_end * self.sample_rate) for digital_end in self.digital_ends]
            # galvo scanner
            self.galvo_step_response = int(3.2e-4 * self.sample_rate)  # ~320 us
            self.galvo_return = int(8e-4 * self.sample_rate)  # ~800 us
            self.ramp_down_fraction = 0.02
            self.ramp_down_offset = 50  # samples
            # galvo scan for read out
            self.galvo_origins = [1.0, 1.465]  # V
            self.galvo_ranges = [4.0, 4]  # V
            self.galvo_offsets = [0.000, 0.000]  # V
            self.galvo_starts = [o_ - r_ / 2 for (o_, r_) in zip(self.galvo_origins, self.galvo_ranges)]
            self.dot_ranges = [2.0, 0.45]  # V
            self.galvo_stops = [o_ + r_ / 2 for (o_, r_) in zip(self.galvo_origins, self.dot_ranges)]
            self.dot_starts = [o_ - r_ / 2 for (o_, r_) in zip(self.galvo_origins, self.dot_ranges)]
            self.dot_step_s = 15  # samples
            self.dot_step_v = 1.0  # volts
            self.dot_step_y = 0.03  # volts
            self.up_rate = self.dot_step_v / self.dot_step_s
            self.dot_pos = np.arange(self.dot_starts[0], self.galvo_stops[0], self.dot_step_v)
            # sawtooth wave for read out
            self.ramp_up = np.arange(self.galvo_starts[0], self.galvo_stops[0] + self.dot_step_v, self.up_rate)
            self.ramp_up_samples = self.ramp_up.size
            self.ramp_down_samples = int(np.ceil(self.ramp_up_samples * self.ramp_down_fraction))
            self.frequency = int(self.sample_rate / self.ramp_up_samples)  # Hz
            # square wave for read out
            self.samples_high = 1
            self.samples_low = self.dot_step_s - self.samples_high
            self.samples_delay = int(np.abs(self.dot_starts[0] - self.galvo_starts[0]) / self.up_rate)
            self.samples_offset = self.ramp_up_samples - (self.samples_delay + self.dot_step_s * self.dot_pos.size)
            # galvo scan for activation
            self.galvo_origins_act = [1.2, 1.6]  # V
            self.galvo_ranges_act = [0.4, 0.4]  # V
            self.galvo_offsets_act = [0.0, 0.0]  # V
            self.galvo_starts_act = [o_ - r_ / 2 for (o_, r_) in zip(self.galvo_origins_act, self.galvo_ranges_act)]
            self.dot_ranges_act = [0.24, 0.24]  # V
            self.galvo_stops_act = [o_ + r_ / 2 for (o_, r_) in zip(self.galvo_origins_act, self.dot_ranges_act)]
            self.dot_starts_act = [o_ - r_ / 2 for (o_, r_) in zip(self.galvo_origins_act, self.dot_ranges_act)]
            self.dot_step_s_act = 120  # samples
            self.dot_step_v_act = 0.0185  # volts
            self.dot_step_y_act = 0.0185  # volts
            self.up_rate_act = self.dot_step_v_act / self.dot_step_s_act
            self.dot_pos_act = np.arange(self.dot_starts_act[0], self.galvo_stops_act[0], self.dot_step_v_act)
            # sawtooth wave for activation
            self.ramp_up_act = np.arange(self.galvo_starts_act[0], self.galvo_stops_act[0] + self.dot_step_v_act,
                                         self.up_rate_act)
            self.ramp_up_samples_act = self.ramp_up_act.size
            self.ramp_down_samples_act = int(np.ceil(self.ramp_up_samples_act * self.ramp_down_fraction))
            self.frequency_act = int(self.sample_rate / self.ramp_up_samples_act)  # Hz
            # square wave for activation
            self.samples_high_act = 1
            self.samples_low_act = self.dot_step_s_act - self.samples_high_act
            self.samples_delay_act = int(np.abs(self.dot_starts_act[0] - self.galvo_starts_act[0]) / self.up_rate_act)
            self.samples_offset_act = self.ramp_up_samples_act - self.samples_delay_act - self.dot_step_s_act * self.dot_pos_act.size
            # camera
            self.frame_rate = 30
            self.cycle_samples_min = int(np.ceil(self.sample_rate / self.frame_rate))
            self.initial_time = 0.001  # s
            self.initial_samples = int(np.ceil(self.initial_time * self.sample_rate))
            self.standby_time = 0.002  # s
            self.standby_samples = int(np.ceil(self.standby_time * self.sample_rate))
            self.exposure_time = 0.001  # s
            self.exposure_samples = int(np.ceil(self.exposure_time / self.sample_rate))
            self.trigger_pulse_width = 50e-6  # s
            self.trigger_pulse_samples = int(np.ceil(self.trigger_pulse_width * self.sample_rate))

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

    def update_galvo_scan_parameters(self, origins=None, ranges=None, foci=None, offsets=None, samples_high=None,
                                     origins_act=None, ranges_act=None, foci_act=None, offsets_act=None, samples_high_act=None):
        original_values = {"frequency": self.frequency, "galvo_origins": self.galvo_origins,
                           "galvo_ranges": self.galvo_ranges, "galvo_starts": self.galvo_starts,
                           "galvo_stops": self.galvo_stops, "galvo_offset": self.galvo_offsets,
                           "dot_ranges": self.dot_ranges, "dot_starts": self.dot_starts, "dot_step_v": self.dot_step_v,
                           "dot_step_s": self.dot_step_s, "dot_step_y": self.dot_step_y, "dot_pos": self.dot_pos,
                           "samples_low": self.samples_low, "samples_delay": self.samples_delay,
                           "samples_offset": self.samples_offset, "samples_high": self.samples_high,
                           "frequency_act": self.frequency_act, "galvo_origins_act": self.galvo_origins_act,
                           "galvo_ranges_act": self.galvo_ranges_act, "galvo_starts_act": self.galvo_starts_act,
                           "galvo_stops_act": self.galvo_stops_act, "galvo_offset_act": self.galvo_offsets_act,
                           "dot_ranges_act": self.dot_ranges_act, "dot_starts_act": self.dot_starts_act,
                           "dot_step_v_act": self.dot_step_v_act, "dot_step_s_act": self.dot_step_s_act,
                           "dot_step_y_act": self.dot_step_y_act, "dot_pos_act": self.dot_pos_act,
                           "samples_low_act": self.samples_low_act, "samples_delay_act": self.samples_delay_act,
                           "samples_offset_act": self.samples_offset_act, "samples_high_act": self.samples_high_act}
        try:
            if origins is not None:
                self.galvo_origins = origins
            if ranges is not None:
                self.galvo_ranges, self.dot_ranges = ranges
            if foci is not None:
                [self.dot_step_s, self.dot_step_v, self.dot_step_y] = foci
            if offsets is not None:
                self.galvo_offsets = offsets
            if samples_high is not None:
                self.samples_high = samples_high

            self.samples_low = self.dot_step_s - self.samples_high
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
            if offsets_act is not None:
                self.galvo_offsets_act = offsets_act
            if samples_high_act is not None:
                self.samples_high_act = samples_high_act

            self.samples_low_act = self.dot_step_s_act - self.samples_high_act
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

    def update_camera_parameters(self, initial_time=None, standby_time=None):
        if initial_time is not None:
            self.initial_time = initial_time
            self.initial_samples = int(np.ceil(self.initial_time * self.sample_rate))
        if standby_time is not None:
            self.standby_time = standby_time
            self.standby_samples = int(np.ceil(self.standby_time * self.sample_rate))

    def generate_digital_triggers(self, lasers, camera):
        cam_ind = camera + 2
        digital_channels = lasers.copy()
        digital_channels.append(cam_ind)
        interval_samples = self.initial_samples
        if interval_samples > self.digital_starts[cam_ind]:
            offset_samples = interval_samples - self.digital_starts[cam_ind]
            self.digital_starts = [(_start + offset_samples) for _start in self.digital_starts]
            self.digital_ends = [(_end + offset_samples) for _end in self.digital_ends]
        cycle_samples = max(self.digital_ends[-1] + self.standby_samples + 2,
                            max([self.digital_ends[i] for i in digital_channels]))
        cycle_samples = max(self.cycle_samples_min, cycle_samples)
        digital_trigger = np.zeros((len(digital_channels), cycle_samples), dtype=np.uint8)
        for ln, ch in enumerate(digital_channels):
            digital_trigger[ln, self.digital_starts[ch + 1]:self.digital_ends[ch + 1]] = 1
        if len(digital_channels) == 3 and 1 in lasers:
            digital_trigger[1, self.digital_starts[0]:self.digital_ends[0]] = 1
        for i in range(len(digital_channels)):
            digital_trigger[i][-1] = 0
        galvo_channels = [0, 1]
        galvo_sequences = np.ones((len(galvo_channels), cycle_samples), dtype=np.uint16)
        galvo_sequences[0] *= int(self.galvo_origins[0] * 4096 / 3.3)
        galvo_sequences[1] *= int(self.galvo_origins[1] * 4096 / 3.3)
        return digital_trigger, digital_channels, galvo_sequences, galvo_channels

    def generate_dot_scanning_triggers(self, lasers, camera):
        cam_ind = camera + 2
        lasers = lasers.copy()
        if 0 in lasers:
            # offset ramp for activation
            ramp_up_offset_act = np.linspace(0, self.galvo_offsets_act[0], self.ramp_up_samples_act + 1,
                                             dtype=np.float16, endpoint=True)
            ramp_down_offset_act = np.zeros(self.ramp_down_samples_act - 1, dtype=np.float16)
            ramp_offset_act = np.concatenate((ramp_up_offset_act, ramp_down_offset_act))
            slow_axis_offset_act = np.tile(ramp_offset_act, self.dot_pos_act.size)
            # galvo activation
            ramp_down_act = smooth_ramp(self.ramp_up_act[-1], self.ramp_up_act[0], self.ramp_down_samples_act)
            extended_cycle_act = np.concatenate((self.ramp_up_act, ramp_down_act))
            fast_axis_galvo_act = np.tile(extended_cycle_act, self.dot_pos_act.size)
            fast_axis_offset_act = np.linspace(0, self.galvo_offsets_act[1], fast_axis_galvo_act.size,
                                               dtype=np.float16, endpoint=True)
            fast_axis_galvo_act += np.repeat(fast_axis_offset_act[::extended_cycle_act.size], extended_cycle_act.size)
            slow_axis_galvo_act = np.zeros_like(fast_axis_galvo_act)
            indices_act = np.arange(self.ramp_up_samples_act + 1, len(fast_axis_galvo_act), extended_cycle_act.size)
            slow_axis_galvo_act[indices_act] = 1
            slow_axis_galvo_act = np.cumsum(slow_axis_galvo_act) * self.dot_step_y_act + self.dot_starts_act[
                1] + slow_axis_offset_act
            slow_axis_galvo_act[-self.ramp_down_samples_act:] = np.linspace(
                slow_axis_galvo_act[-self.ramp_down_samples_act], self.dot_starts_act[1], self.ramp_down_samples_act)
            fill_samples_act = 1
            fast_axis_galvo_act = np.pad(fast_axis_galvo_act, (self.galvo_return, fill_samples_act), 'constant',
                                         constant_values=(self.galvo_starts_act[0], self.galvo_starts_act[0]))
            slow_axis_galvo_act = np.pad(slow_axis_galvo_act, (self.galvo_return, fill_samples_act), 'constant',
                                         constant_values=(self.dot_starts_act[1], self.dot_starts_act[1]))
            _sqr_act = np.pad(np.ones(self.samples_high_act), (0, self.samples_low_act), 'constant',
                              constant_values=(0, 0))
            square_wave_act = np.pad(np.tile(_sqr_act, self.dot_pos_act.size),
                                     (self.samples_delay_act, self.samples_offset_act + self.ramp_down_samples_act),
                                     'constant', constant_values=(0, 0))
            laser_trigger_act = np.tile(square_wave_act, self.dot_pos_act.size - 1)
            laser_trigger_act = np.concatenate((np.zeros(square_wave_act.size), laser_trigger_act))
            if 1 in lasers:
                fast_axis_galvo_act[-fill_samples_act:] = self.galvo_starts[0]
                slow_axis_galvo_act[-fill_samples_act:] = self.dot_starts[1]
                laser_trigger_act = np.pad(laser_trigger_act, (self.galvo_return, fill_samples_act), 'constant',
                                           constant_values=(0, 0))
                camera_trigger_act = np.zeros(laser_trigger_act.shape)
            else:
                camera_trigger_act = np.ones(laser_trigger_act.shape, dtype=np.int8)
                camera_trigger_act[:self.samples_delay_act + square_wave_act.size] = 0
                camera_trigger_act[- self.samples_offset_act - self.ramp_down_samples_act:] = 0
                laser_trigger_act = np.pad(laser_trigger_act, (self.galvo_return, fill_samples_act), 'constant',
                                           constant_values=(0, 0))
                camera_trigger_act = np.pad(camera_trigger_act, (self.galvo_return, fill_samples_act), 'constant',
                                            constant_values=(0, 0))
        # offset ramp
        ramp_up_offset = np.linspace(0, self.galvo_offsets[0], self.ramp_up_samples + 1, dtype=np.float16,
                                     endpoint=True)
        ramp_down_offset = np.zeros(self.ramp_down_samples - 1, dtype=np.float16)
        ramp_offset = np.concatenate((ramp_up_offset, ramp_down_offset))
        slow_axis_offset = np.tile(ramp_offset, self.dot_pos.size)
        # galvo read out
        ramp_down = smooth_ramp(self.ramp_up[-1], self.ramp_up[0], self.ramp_down_samples)
        extended_cycle = np.concatenate((self.ramp_up, ramp_down))
        fast_axis_galvo = np.tile(extended_cycle, self.dot_pos.size)
        fast_axis_offset = np.linspace(0, self.galvo_offsets[1], fast_axis_galvo.size, dtype=np.float16,
                                       endpoint=True)
        fast_axis_galvo += np.repeat(fast_axis_offset[::extended_cycle.size], extended_cycle.size)
        slow_axis_galvo = np.zeros_like(fast_axis_galvo)
        indices = np.arange(self.ramp_up_samples + 1, len(fast_axis_galvo), extended_cycle.size)
        slow_axis_galvo[indices] = 1
        slow_axis_galvo = np.cumsum(slow_axis_galvo) * self.dot_step_y + self.dot_starts[1] + slow_axis_offset
        slow_axis_galvo[-self.ramp_down_samples:] = np.linspace(slow_axis_galvo[-self.ramp_down_samples],
                                                                self.dot_starts[1], self.ramp_down_samples)
        fill_samples = 0
        fast_axis_galvo = np.pad(fast_axis_galvo, (self.galvo_return, fill_samples), 'constant',
                                 constant_values=(self.galvo_starts[0], self.galvo_starts[0]))
        slow_axis_galvo = np.pad(slow_axis_galvo, (self.galvo_return, fill_samples), 'constant',
                                 constant_values=(self.dot_starts[1], self.dot_starts[1]))
        _sqr = np.pad(np.ones(self.samples_high), (0, self.samples_low), 'constant', constant_values=(0, 0))
        square_wave = np.pad(np.tile(_sqr, self.dot_pos.size),
                             (self.samples_delay, self.samples_offset + self.ramp_down_samples), 'constant',
                             constant_values=(0, 0))
        laser_trigger = np.tile(square_wave, self.dot_pos.size - 1)
        laser_trigger = np.concatenate((np.zeros(square_wave.size), laser_trigger))
        camera_trigger = np.ones(laser_trigger.shape, dtype=np.int8)
        camera_trigger[:self.samples_delay + square_wave.size] = 0
        camera_trigger[- self.samples_offset - self.ramp_down_samples:] = 0
        laser_trigger = np.pad(laser_trigger, (self.galvo_return, fill_samples), 'constant', constant_values=(0, 0))
        camera_trigger = np.pad(camera_trigger, (self.galvo_return, fill_samples), 'constant', constant_values=(0, 0))
        # all
        digital_sequences = [np.empty((0,)) for _ in range(len(lasers) + 1)]
        galvo_sequences = [np.empty((0,)) for _ in range(2)]
        for _, las in enumerate(lasers):
            if las == 0:
                trig = laser_trigger_act
                gvf = fast_axis_galvo_act
                gvs = slow_axis_galvo_act
                cm = camera_trigger_act
            elif las == 1:
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
        for i, dtr in enumerate(digital_sequences):
            digital_sequences[i] = np.append(dtr, dtr[-1] * np.ones(self.standby_samples))
        for i, gtr in enumerate(galvo_sequences):
            galvo_sequences[i] = np.append(gtr, gtr[-1] * np.ones(self.standby_samples))
        for i in range(2):
            galvo_sequences[i] = np.round(galvo_sequences[i] * 4096 / 3.3).astype(np.uint16)
        return np.asarray(digital_sequences), np.asarray(galvo_sequences), lasers

    def generate_line_scanning_triggers(self, lasers, camera):
        digital_trigger, digital_channels, galvo_steps, galvo_channels = self.generate_digital_triggers(lasers, camera)
        x_pos = np.arange(self.dot_starts[0], self.galvo_stops[0] + 0.0001, self.dot_step_v)
        y_pos = np.arange(self.dot_starts[1], self.galvo_stops[1], self.dot_step_y)
        step_length = digital_trigger.shape[1]
        if self.galvo_step_response > self.standby_samples:
            offset = self.galvo_step_response - self.standby_samples
        galvo_start = self.digital_ends[-1] + int(32e-6 * self.sample_rate)
        pos = x_pos.shape[0] * y_pos.shape[0]
        digital_triggers = np.tile(digital_trigger, (1, pos))
        galvo_sequences = np.ones((len(galvo_channels), digital_triggers.shape[1]), dtype=np.float16)
        galvo_sequences[0] = np.repeat(x_pos, step_length)
        galvo_sequences[1] = np.repeat(y_pos, step_length)
        shifts = step_length - galvo_start
        galvo_sequences[0] = shift_array(galvo_sequences[0], shifts, fill=None, direction='backward')
        galvo_sequences[1] = shift_array(galvo_sequences[1], shifts, fill=None, direction='backward')
        return digital_triggers, digital_channels, galvo_sequences, galvo_channels, pos


def convert_list(arrays):
    if len(arrays) == 1:
        return arrays[0]
    else:
        return np.array(arrays)


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
