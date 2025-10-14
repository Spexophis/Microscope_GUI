class ConController:

    def __init__(self, view):
        self.v = view

    def get_thorcam_expo(self):
        return self.v.QDoubleSpinBox_thorcam_exposure_time.value()

    def get_thorcam_roi(self):
        return [self.v.QSpinBox_thorcam_coordinate_x.value(), self.v.QSpinBox_thorcam_coordinate_y.value(),
                self.v.QSpinBox_thorcam_coordinate_nx.value(), self.v.QSpinBox_thorcam_coordinate_ny.value(),
                self.v.QSpinBox_thorcam_coordinate_bin.value()]

    def get_webcam_expo(self):
        return self.v.QDoubleSpinBox_webcam_exposure_time.value()

    def get_webcam_roi(self):
        return [self.v.QSpinBox_webcam_coordinate_x.value(), self.v.QSpinBox_webcam_coordinate_y.value(),
                self.v.QSpinBox_webcam_coordinate_nx.value(), self.v.QSpinBox_webcam_coordinate_ny.value(),
                self.v.QSpinBox_webcam_coordinate_bin.value()]

    def get_galvo_positions(self):
        return [self.v.QDoubleSpinBox_galvo_x.value(), self.v.QDoubleSpinBox_galvo_y.value()]

    def get_lasers(self):
        lasers = []
        if self.v.QRadioButton_laser_405.isChecked():
            lasers.append(0)
        if self.v.QRadioButton_laser_488.isChecked():
            lasers.append(1)
        return lasers

    def get_cobolt_laser_power(self, laser):
        if laser == "405":
            return [self.v.QDoubleSpinBox_laserpower_405.value()]
        if laser == "488":
            return [self.v.QDoubleSpinBox_laserpower_488.value()]
        if laser == "all":
            return [self.v.QDoubleSpinBox_laserpower_405.value(), self.v.QDoubleSpinBox_laserpower_488.value()]

    def get_imaging_camera(self):
        detection_device = self.v.QComboBox_imaging_camera_selection.currentIndex()
        return detection_device

    def get_digital_parameters(self):
        digital_starts = [self.v.QDoubleSpinBox_ttl_start_off.value(),
                          self.v.QDoubleSpinBox_ttl_start_405.value(),
                          self.v.QDoubleSpinBox_ttl_start_488.value(),
                          self.v.QDoubleSpinBox_ttl_start_thorcam.value()]
        digital_ends = [self.v.QDoubleSpinBox_ttl_stop_off.value(),
                        self.v.QDoubleSpinBox_ttl_stop_405.value(),
                        self.v.QDoubleSpinBox_ttl_stop_488.value(),
                        self.v.QDoubleSpinBox_ttl_stop_thorcam.value()]
        return digital_starts, digital_ends

    def get_piezo_scan_parameters(self):
        axis_lengths = [self.v.QDoubleSpinBox_range_x.value(), self.v.QDoubleSpinBox_range_y.value(),
                        self.v.QDoubleSpinBox_range_z.value()]
        step_sizes = [self.v.QDoubleSpinBox_step_x.value(), self.v.QDoubleSpinBox_step_y.value(),
                      self.v.QDoubleSpinBox_step_z.value()]
        return axis_lengths, step_sizes

    def get_piezo_return_time(self):
        return self.v.QDoubleSpinBox_piezo_return_time.value()

    def get_galvo_scan_parameters(self):
        galvo_positions = [self.v.QDoubleSpinBox_galvo_x.value(), self.v.QDoubleSpinBox_galvo_y.value()]
        galvo_ranges = [[self.v.QDoubleSpinBox_galvo_range_x.value(), self.v.QDoubleSpinBox_galvo_range_y.value()],
                        [self.v.QDoubleSpinBox_dot_range_x.value(), self.v.QDoubleSpinBox_dot_range_y.value()]]
        dot_pos = [self.v.QSpinBox_dot_step_x.value(), self.v.QDoubleSpinBox_dot_step_x.value(),
                   self.v.QDoubleSpinBox_dot_step_y.value()]
        offsets = [self.v.QDoubleSpinBox_galvo_offset_x.value(), self.v.QDoubleSpinBox_galvo_offset_y.value()]
        high_samples = self.v.QDoubleSpinBox_sample_high.value()
        galvo_positions_act = [self.v.QDoubleSpinBox_galvo_x_act.value(), self.v.QDoubleSpinBox_galvo_y_act.value()]
        galvo_ranges_act = [
            [self.v.QDoubleSpinBox_galvo_range_x_act.value(), self.v.QDoubleSpinBox_galvo_range_y_act.value()],
            [self.v.QDoubleSpinBox_dot_range_x_act.value(), self.v.QDoubleSpinBox_dot_range_y_act.value()]]
        dot_pos_act = [self.v.QSpinBox_dot_step_x_act.value(), self.v.QDoubleSpinBox_dot_step_x_act.value(),
                       self.v.QDoubleSpinBox_dot_step_y_act.value()]
        offsets_act = [self.v.QDoubleSpinBox_galvo_offset_x_act.value(), self.v.QDoubleSpinBox_galvo_offset_y_act.value()]
        high_samples_act = self.v.QDoubleSpinBox_sample_high_act.value()
        return (galvo_positions, galvo_ranges, dot_pos, offsets, high_samples,
                galvo_positions_act, galvo_ranges_act, dot_pos_act, offsets_act, high_samples_act)

    def change_galvo_scan(self, x=None, y=None):
        if x is not None:
            self.v.QDoubleSpinBox_galvo_x.setValue(x)
        if y is not None:
            self.v.QDoubleSpinBox_galvo_y.setValue(y)

    def display_frequency(self, dsv, dsv_act):
        self.v.QLCDNumber_galvo_frequency.display(dsv)
        self.v.QLCDNumber_galvo_frequency_act.display(dsv_act)

    def get_profile_axis(self):
        return self.v.QComboBox_profile_axis.currentText()

    def get_live_mode(self):
        return self.v.QComboBox_live_modes.currentText()

    def get_acquisition_mode(self):
        return self.v.QComboBox_acquisition_modes.currentText()
