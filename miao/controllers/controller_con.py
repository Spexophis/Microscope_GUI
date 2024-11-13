class ConController:

    def __init__(self, view):
        self.v = view

    def get_emccd_roi(self):
        return [self.v.QSpinBox_emccd_coordinate_x.value(), self.v.QSpinBox_emccd_coordinate_y.value(),
                self.v.QSpinBox_emccd_coordinate_nx.value(), self.v.QSpinBox_emccd_coordinate_ny.value(),
                self.v.QSpinBox_emccd_coordinate_binx.value(), self.v.QSpinBox_emccd_coordinate_biny.value()]

    def get_emccd_gain(self):
        return self.v.QSpinBox_emccd_gain.value()

    def get_emccd_expo(self):
        return self.v.QDoubleSpinBox_emccd_exposure_time.value()

    def set_emccd_expo(self, t):
        self.v.QDoubleSpinBox_emccd_exposure_time.setValue(t)

    def get_ccd_clean(self):
        return self.v.QDoubleSpinBox_emccd_t_clean.value()

    def get_scmos_roi(self):
        return [self.v.QSpinBox_scmos_coordinate_x.value(), self.v.QSpinBox_scmos_coordinate_y.value(),
                self.v.QSpinBox_scmos_coordinate_nx.value(), self.v.QSpinBox_scmos_coordinate_ny.value(),
                self.v.QSpinBox_scmos_coordinate_binx.value(), self.v.QSpinBox_scmos_coordinate_biny.value()]

    def get_scmos_mode(self):
        return self.v.QComboBox_scmos_sensor_modes.currentText()

    def get_scmos_expo(self):
        return [self.v.QDoubleSpinBox_scmos_line_exposure.value(), self.v.QDoubleSpinBox_scmos_line_interval.value(),
                self.v.QDoubleSpinBox_scmos_interval_lines.value()]

    def set_scmos_expo(self, t):
        self.v.QDoubleSpinBox_scmos_exposure_time.setValue(t)

    def get_thorcam_roi(self):
        return [self.v.QSpinBox_thorcam_coordinate_x.value(), self.v.QSpinBox_thorcam_coordinate_y.value(),
                self.v.QSpinBox_thorcam_coordinate_nx.value(), self.v.QSpinBox_thorcam_coordinate_ny.value(),
                self.v.QSpinBox_thorcam_coordinate_binx.value(), self.v.QSpinBox_thorcam_coordinate_biny.value()]

    def get_tis_expo(self):
        return self.v.QDoubleSpinBox_tis_exposure_time.value()

    def get_tis_roi(self):
        return [self.v.QSpinBox_tis_coordinate_x.value(), self.v.QSpinBox_tis_coordinate_y.value(),
                self.v.QSpinBox_tis_coordinate_nx.value(), self.v.QSpinBox_tis_coordinate_ny.value(),
                self.v.QSpinBox_tis_coordinate_binx.value(), self.v.QSpinBox_tis_coordinate_biny.value()]

    def get_deck_movement(self):
        return [self.v.QDoubleSpinBox_deck_movement.value(), self.v.QDoubleSpinBox_deck_velocity.value()]

    def get_piezo_positions(self):
        return [[self.v.QDoubleSpinBox_stage_x_usb.value(), self.v.QDoubleSpinBox_stage_x.value()],
                [self.v.QDoubleSpinBox_stage_y_usb.value(), self.v.QDoubleSpinBox_stage_y.value()],
                [self.v.QDoubleSpinBox_stage_z_usb.value(), self.v.QDoubleSpinBox_stage_z.value()]]

    def get_pid_parameters(self):
        return (self.v.QDoubleSpinBox_pid_kp.value(),
                self.v.QDoubleSpinBox_pid_ki.value(),
                self.v.QDoubleSpinBox_pid_kd.value())

    def get_galvo_positions(self):
        return [self.v.QDoubleSpinBox_galvo_x.value(), self.v.QDoubleSpinBox_galvo_y.value()]

    def get_lasers(self):
        lasers = []
        if self.v.QRadioButton_laser_405.isChecked():
            lasers.append(0)
        if self.v.QRadioButton_laser_488_0.isChecked():
            lasers.append(1)
        if self.v.QRadioButton_laser_488_1.isChecked():
            lasers.append(2)
        if self.v.QRadioButton_laser_488_2.isChecked():
            lasers.append(3)
        return lasers

    def get_cobolt_laser_power(self, laser):
        if laser == "405":
            return [self.v.QDoubleSpinBox_laserpower_405.value()]
        if laser == "488_0":
            return [self.v.QDoubleSpinBox_laserpower_488_0.value()]
        if laser == "488_1":
            return [self.v.QDoubleSpinBox_laserpower_488_1.value()]
        if laser == "488_2":
            return [self.v.QDoubleSpinBox_laserpower_488_2.value()]
        if laser == "all":
            return [self.v.QDoubleSpinBox_laserpower_405.value(), self.v.QDoubleSpinBox_laserpower_488_0.value(),
                    self.v.QDoubleSpinBox_laserpower_488_1.value(), self.v.QDoubleSpinBox_laserpower_488_2.value()]

    def get_imaging_camera(self):
        detection_device = self.v.QComboBox_imaging_camera_selection.currentIndex()
        return detection_device

    def get_digital_parameters(self):
        digital_starts = [self.v.QDoubleSpinBox_ttl_start_on_405.value(),
                          self.v.QDoubleSpinBox_ttl_start_off_488_0.value(),
                          self.v.QDoubleSpinBox_ttl_start_off_488_1.value(),
                          self.v.QDoubleSpinBox_ttl_start_read_488_2.value(),
                          self.v.QDoubleSpinBox_ttl_start_emccd.value(),
                          self.v.QDoubleSpinBox_ttl_start_scmos.value(),
                          self.v.QDoubleSpinBox_ttl_start_thorcam.value()]
        digital_ends = [self.v.QDoubleSpinBox_ttl_stop_on_405.value(),
                        self.v.QDoubleSpinBox_ttl_stop_off_488_0.value(),
                        self.v.QDoubleSpinBox_ttl_stop_off_488_1.value(),
                        self.v.QDoubleSpinBox_ttl_stop_read_488_2.value(),
                        self.v.QDoubleSpinBox_ttl_stop_emccd.value(),
                        self.v.QDoubleSpinBox_ttl_stop_scmos.value(),
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
        galvo_positions_act = [self.v.QDoubleSpinBox_galvo_x_act.value(), self.v.QDoubleSpinBox_galvo_y_act.value()]
        galvo_ranges_act = [
            [self.v.QDoubleSpinBox_galvo_range_x_act.value(), self.v.QDoubleSpinBox_galvo_range_y_act.value()],
            [self.v.QDoubleSpinBox_dot_range_x_act.value(), self.v.QDoubleSpinBox_dot_range_y_act.value()]]
        dot_pos_act = [self.v.QSpinBox_dot_step_x_act.value(), self.v.QDoubleSpinBox_dot_step_x_act.value(),
                       self.v.QDoubleSpinBox_dot_step_y_act.value()]
        offsets_act = [self.v.QDoubleSpinBox_galvo_offset_x_act.value(), self.v.QDoubleSpinBox_galvo_offset_y_act.value()]
        sws = [self.v.QDoubleSpinBox_emccd_gvs.value(), self.v.QDoubleSpinBox_scmos_gvs.value(),
               self.v.QDoubleSpinBox_thorcam_gvs.value()]
        return (galvo_positions, galvo_ranges, dot_pos, offsets,
                galvo_positions_act, galvo_ranges_act, dot_pos_act, offsets_act, sws)

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

    def display_camera_temperature(self, temperature):
        self.v.QLCDNumber_ccd_tempetature.display(temperature)

    def display_camera_timings(self, clean=None, exposure=None, standby=None):
        if clean is not None:
            self.v.QDoubleSpinBox_emccd_t_clean.setValue(clean)
        if exposure is not None:
            self.v.QDoubleSpinBox_emccd_exposure_time.setValue(exposure)
        if standby is not None:
            self.v.QDoubleSpinBox_emccd_t_standby.setValue(standby)

    def display_cmos_rolling_timings(self, line_exposure, line_interval):
        self.v.QDoubleSpinBox_scmos_line_exposure.setValue(line_exposure)
        self.v.QDoubleSpinBox_scmos_line_interval.setValue(line_interval)

    def display_deck_position(self, mdposz):
        self.v.QLCDNumber_deck_position.display(mdposz)

    def display_piezo_position_x(self, ps):
        self.v.QLCDNumber_piezo_position_x.display(ps)

    def display_piezo_position_y(self, ps):
        self.v.QLCDNumber_piezo_position_y.display(ps)

    def display_piezo_position_z(self, ps):
        self.v.QLCDNumber_piezo_position_z.display(ps)

    def get_file_name(self):
        return self.v.QLineEdit_filename.text()
