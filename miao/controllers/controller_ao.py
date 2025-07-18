class AOController:

    def __init__(self, view):
        self.v = view

    def get_wfs_camera(self):
        return self.v.QComboBox_wfs_camera_selection.currentIndex()

    def display_img_wf_properties(self, properties):
        self.v.lcdNumber_wfmin_img.display(properties[0])
        self.v.lcdNumber_wfmax_img.display(properties[1])
        self.v.lcdNumber_wfrms_img.display(properties[2])

    def get_parameters_img(self):
        return self.v.QSpinBox_base_xcenter_img.value(), self.v.QSpinBox_base_ycenter_img.value(), \
            self.v.QSpinBox_offset_xcenter_img.value(), self.v.QSpinBox_offset_ycenter_img.value(), \
            self.v.QSpinBox_n_lenslets_x_img.value(), self.v.QSpinBox_n_lenslets_y_img.value(), \
            self.v.QSpinBox_spacing_img.value(), self.v.QSpinBox_radius_img.value(), \
            self.v.QDoubleSpinBox_img_background.value()

    def get_gradient_method_img(self):
        return self.v.QComboBox_wfrmd_img.currentText()

    def get_img_wfs_method(self):
        return self.v.QComboBox_wfsmd.currentText()

    def get_actuator(self):
        return self.v.QSpinBox_actuator.value(), self.v.QDoubleSpinBox_actuator_push.value()

    def get_zernike_mode(self):
        return self.v.QSpinBox_zernike_mode.value(), self.v.QDoubleSpinBox_zernike_mode_amp.value()

    def get_dm_selection(self):
        return self.v.QComboBox_dms.currentText()

    def get_cmd_index(self):
        return self.v.QComboBox_cmd.currentText()

    def update_cmd_index(self, wst=True):
        item = '{}'.format(self.v.QComboBox_cmd.count())
        self.v.QComboBox_cmd.addItem(item)
        if wst:
            self.v.QComboBox_cmd.setCurrentIndex(self.v.QComboBox_cmd.count() - 1)

    def get_ao_iteration(self):
        return self.v.QSpinBox_zernike_mode_start.value(), self.v.QSpinBox_zernike_mode_stop.value(), \
            self.v.QDoubleSpinBox_zernike_mode_amps_start.value(), self.v.QDoubleSpinBox_zernike_mode_amps_step.value(), \
            self.v.QSpinBox_zernike_mode_amps_stepnum.value()

    def get_ao_parameters(self):
        return self.v.QDoubleSpinBox_lpf.value(), self.v.QDoubleSpinBox_hpf.value(), \
            self.v.QDoubleSpinBox_select_frequency.value(), self.v.QComboBox_metric.currentText(), \
            self.v.QRadioButton_sensorless_error.isChecked()
