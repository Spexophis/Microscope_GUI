# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


class ConController:

    def __init__(self, view):
        self.v = view

    def get_emccd_roi(self):
        return (self.v.QSpinBox_emccd_coordinate_x.value(), self.v.QSpinBox_emccd_coordinate_y.value(),
                self.v.QSpinBox_emccd_coordinate_nx.value(), self.v.QSpinBox_emccd_coordinate_ny.value(),
                self.v.QSpinBox_emccd_coordinate_binx.value(), self.v.QSpinBox_emccd_coordinate_biny.value())

    def get_emccd_gain(self):
        return self.v.QSpinBox_emccd_gain.value()

    def get_emccd_expo(self):
        return self.v.QDoubleSpinBox_emccd_t_expos.value()

    def get_ccd_clean(self):
        return self.v.QDoubleSpinBox_emccd_t_clean.value()

    def display_camera_temperature(self, temperature):
        self.v.QLCDNumber_ccd_tempetature.display(temperature)

    def display_emccd_timings(self, clean=None, exposure=None, standby=None):
        if clean is not None:
            self.v.QDoubleSpinBox_emccd_t_clean.setValue(clean)
        if exposure is not None:
            self.v.QDoubleSpinBox_emccd_t_expos.setValue(exposure)
        if standby is not None:
            self.v.QDoubleSpinBox_emccd_t_standby.setValue(standby)

    def get_scmos_roi(self):
        return (self.v.QSpinBox_scmos_coordinate_x.value(), self.v.QSpinBox_scmos_coordinate_y.value(),
                self.v.QSpinBox_scmos_coordinate_nx.value(), self.v.QSpinBox_scmos_coordinate_ny.value(),
                self.v.QSpinBox_scmos_coordinate_binx.value(), self.v.QSpinBox_scmos_coordinate_biny.value())

    def get_scmos_expo(self):
        return self.v.QDoubleSpinBox_scmos_t_expos.value()

    def display_scmos_timings(self, clean=None, exposure=None, standby=None):
        if clean is not None:
            self.v.QDoubleSpinBox_scmos_t_clean.setValue(clean)
        if exposure is not None:
            self.v.QDoubleSpinBox_scmos_t_expos.setValue(exposure)
        if standby is not None:
            self.v.QDoubleSpinBox_scmos_t_standby.setValue(standby)

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

    def get_lasers(self):
        lasers = []
        if self.v.QRadioButton_laser_405.isChecked():
            lasers.append(0)
        if self.v.QRadioButton_laser_488_w.isChecked():
            lasers.append(1)
        if self.v.QRadioButton_laser_488.isChecked():
            lasers.append(2)
        return lasers

    def get_cobolt_laser_power(self, laser):
        if laser == "405":
            return [self.v.QDoubleSpinBox_laserpower_405.value()]
        elif laser == "488_W":
            return [self.v.QDoubleSpinBox_laserpower_488_w.value()]
        elif laser == "488":
            return [self.v.QDoubleSpinBox_laserpower_488.value()]
        elif laser == "all":
            return [self.v.QDoubleSpinBox_laserpower_405.value(),
                    self.v.QDoubleSpinBox_laserpower_488_w.value(),
                    self.v.QDoubleSpinBox_laserpower_488.value()]
        else:
            return None

    def get_imaging_camera(self):
        detection_device = self.v.QComboBox_imaging_camera_selection.currentIndex()
        return detection_device

    def get_digital_parameters(self):
        digital_starts = [self.v.QDoubleSpinBox_ttl_start_on_405.value(),
                          self.v.QDoubleSpinBox_ttl_start_off_488.value(),
                          self.v.QDoubleSpinBox_ttl_start_read_488.value(),
                          self.v.QDoubleSpinBox_ttl_start_emccd.value(),
                          self.v.QDoubleSpinBox_ttl_start_scmos.value()]
        digital_ends = [self.v.QDoubleSpinBox_ttl_stop_on_405.value(),
                        self.v.QDoubleSpinBox_ttl_stop_off_488.value(),
                        self.v.QDoubleSpinBox_ttl_stop_read_488.value(),
                        self.v.QDoubleSpinBox_ttl_stop_emccd.value(),
                        self.v.QDoubleSpinBox_ttl_stop_scmos.value()]
        return digital_starts, digital_ends

    def get_piezo_scan_parameters(self):
        axis_lengths = [self.v.QDoubleSpinBox_range_x.value(), self.v.QDoubleSpinBox_range_y.value(),
                        self.v.QDoubleSpinBox_range_z.value()]
        step_sizes = [self.v.QDoubleSpinBox_step_x.value(), self.v.QDoubleSpinBox_step_y.value(),
                      self.v.QDoubleSpinBox_step_z.value()]
        return axis_lengths, step_sizes

    def get_piezo_return_time(self):
        return self.v.QDoubleSpinBox_piezo_return_time.value()

    def get_galvo_switch_parameters(self):
        swx = [self.v.QDoubleSpinBox_emccd_gvs.value(), self.v.QDoubleSpinBox_scmos_gvs.value(),
               self.v.QDoubleSpinBox_tis_gvs.value()]
        return swx

    def get_profile_axis(self):
        return self.v.QComboBox_profile_axis.currentText()

    def get_live_mode(self):
        return self.v.QComboBox_live_modes.currentText()

    def get_acquisition_mode(self):
        return self.v.QComboBox_acquisition_modes.currentText()

    def get_slm_sequence(self):
        return self.v.QComboBox_slm_sequence.currentText()

    def display_deck_position(self, mdposz):
        self.v.QLCDNumber_deck_position.display(mdposz)

    def display_piezo_position_x(self, ps):
        self.v.QLCDNumber_piezo_position_x.display(ps)

    def display_piezo_position_y(self, ps):
        self.v.QLCDNumber_piezo_position_y.display(ps)

    def display_piezo_position_z(self, ps):
        self.v.QLCDNumber_piezo_position_z.display(ps)
