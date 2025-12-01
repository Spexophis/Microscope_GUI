# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


from PyQt5 import QtWidgets, QtCore

from miao.utilities import customized_widgets as cw


class ConWidget(QtWidgets.QWidget):
    Signal_galvo_set = QtCore.pyqtSignal(float, float)
    Signal_galvo_scan_update = QtCore.pyqtSignal()
    Signal_set_laser = QtCore.pyqtSignal(list, bool, float)
    # Signal_nucleo_update = QtCore.pyqtSignal(int)
    Signal_nucleo_send = QtCore.pyqtSignal(str)
    Signal_plot_trigger = QtCore.pyqtSignal()
    Signal_focus_finding = QtCore.pyqtSignal()
    Signal_video = QtCore.pyqtSignal(bool, str)
    Signal_fft = QtCore.pyqtSignal(bool)
    Signal_plot_profile = QtCore.pyqtSignal(bool)
    Signal_add_profile = QtCore.pyqtSignal()
    Signal_set_mask = QtCore.pyqtSignal()
    Signal_alignment = QtCore.pyqtSignal()
    Signal_data_acquire = QtCore.pyqtSignal(str, int)
    Signal_save_file = QtCore.pyqtSignal(str)

    def __init__(self, config, logg, path, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.config = config
        self.logg = logg
        self.data_folder = path
        self._setup_ui()
        self.load_spinbox_values()
        self.galvo_scan_presets = self.load_galvo_scan_presets()
        self.digital_timing_presets = self.load_digital_timing_presets()
        self._set_signal_connections()

    def closeEvent(self, event):
        self.save_spinbox_values()
        event.accept()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self._create_docks()
        self._create_widgets()
        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        for name, (dock, group) in self.docks.items():
            splitter.addWidget(dock)
            group.setLayout(self.widgets[name])
        layout.addWidget(splitter)
        self.setLayout(layout)

    def _create_docks(self):
        self.docks = {
            "camera": cw.create_dock("Camera"),
            "position": cw.create_dock("Position"),
            "laser": cw.create_dock("Laser"),
            "daq": cw.create_dock("Daq"),
            "video": cw.create_dock("Live Imaging"),
            "acquisition": cw.create_dock("Data Acquisition")
        }

    def _create_widgets(self):
        self.widgets = {
            "camera": self._create_camera_widgets(),
            "position": self._create_position_widgets(),
            "laser": self._create_laser_widgets(),
            "daq": self._create_daq_widgets(),
            "video": self._create_video_widgets(),
            "acquisition": self._create_acquisition_widgets()
        }

    def _create_camera_widgets(self):
        layout_camera = QtWidgets.QHBoxLayout()

        self.QDoubleSpinBox_thorcam_exposure_time = cw.DoubleSpinBoxWidget(0.001, 10, 0.001, 3, 0.001)
        self.QSpinBox_thorcam_coordinate_x = cw.SpinBoxWidget(0, 2047, 1, 0)
        self.QSpinBox_thorcam_coordinate_y = cw.SpinBoxWidget(0, 2047, 1, 0)
        self.QSpinBox_thorcam_coordinate_nx = cw.SpinBoxWidget(0, 2048, 1, 2048)
        self.QSpinBox_thorcam_coordinate_ny = cw.SpinBoxWidget(0, 2048, 1, 2048)
        self.QSpinBox_thorcam_coordinate_bin = cw.SpinBoxWidget(0, 2048, 1, 1)

        self.thorcam_scroll_area, thorcam_scroll_layout = cw.create_scroll_area()
        thorcam_scroll_layout.addRow(cw.LabelWidget(str('Thorlabs')))
        thorcam_scroll_layout.addRow(cw.FrameWidget())
        thorcam_scroll_layout.addRow(cw.LabelWidget(str('Exposure / s')), self.QDoubleSpinBox_thorcam_exposure_time)
        thorcam_scroll_layout.addRow(cw.LabelWidget(str('X')), self.QSpinBox_thorcam_coordinate_x)
        thorcam_scroll_layout.addRow(cw.LabelWidget(str('Y')), self.QSpinBox_thorcam_coordinate_y)
        thorcam_scroll_layout.addRow(cw.LabelWidget(str('Nx')), self.QSpinBox_thorcam_coordinate_nx)
        thorcam_scroll_layout.addRow(cw.LabelWidget(str('Ny')), self.QSpinBox_thorcam_coordinate_ny)
        thorcam_scroll_layout.addRow(cw.LabelWidget(str('Bin')), self.QSpinBox_thorcam_coordinate_bin)

        self.QDoubleSpinBox_webcam_exposure_time = cw.DoubleSpinBoxWidget(2e-05, 4, 0.0002, 5, 0.0004)
        self.QSpinBox_webcam_coordinate_x = cw.SpinBoxWidget(0, 2448, 1, 0)
        self.QSpinBox_webcam_coordinate_y = cw.SpinBoxWidget(0, 2048, 1, 0)
        self.QSpinBox_webcam_coordinate_nx = cw.SpinBoxWidget(0, 2448, 1, 2448)
        self.QSpinBox_webcam_coordinate_ny = cw.SpinBoxWidget(0, 2048, 1, 2048)
        self.QSpinBox_webcam_coordinate_bin = cw.SpinBoxWidget(0, 2447, 1, 1)

        self.webcam_scroll_area, webcam_scroll_layout = cw.create_scroll_area()
        webcam_scroll_layout.addRow(cw.LabelWidget(str('WebCam')))
        webcam_scroll_layout.addRow(cw.FrameWidget())
        webcam_scroll_layout.addRow(cw.LabelWidget(str('Exposure / s')), self.QDoubleSpinBox_webcam_exposure_time)
        webcam_scroll_layout.addRow(cw.LabelWidget(str('X')), self.QSpinBox_webcam_coordinate_x)
        webcam_scroll_layout.addRow(cw.LabelWidget(str('Y')), self.QSpinBox_webcam_coordinate_y)
        webcam_scroll_layout.addRow(cw.LabelWidget(str('Nx')), self.QSpinBox_webcam_coordinate_nx)
        webcam_scroll_layout.addRow(cw.LabelWidget(str('Ny')), self.QSpinBox_webcam_coordinate_ny)
        webcam_scroll_layout.addRow(cw.LabelWidget(str('Bin')), self.QSpinBox_webcam_coordinate_bin)

        layout_camera.addWidget(self.thorcam_scroll_area)
        layout_camera.addWidget(self.webcam_scroll_area)
        return layout_camera

    def _create_position_widgets(self):
        layout_position = QtWidgets.QHBoxLayout()

        self.QLCDNumber_galvo_frequency = cw.LCDNumberWidget(0, 3)
        self.QDoubleSpinBox_galvo_x = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0)
        self.QDoubleSpinBox_galvo_y = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0)
        self.QDoubleSpinBox_galvo_range_x = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0.4)
        self.QDoubleSpinBox_galvo_range_y = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0.4)
        self.QDoubleSpinBox_dot_range_x = cw.DoubleSpinBoxWidget(0, 10, 0.0001, 5, 0.2)
        self.QDoubleSpinBox_dot_range_y = cw.DoubleSpinBoxWidget(0, 10, 0.0001, 5, 0.2)
        self.QDoubleSpinBox_dot_step_x = cw.DoubleSpinBoxWidget(0, 10, 0.0001, 5, 0.01720)
        self.QSpinBox_dot_step_x = cw.SpinBoxWidget(0, 4000, 1, 88)
        self.QDoubleSpinBox_sample_high = cw.SpinBoxWidget(0, 4000, 1, 1)
        self.QDoubleSpinBox_dot_step_y = cw.DoubleSpinBoxWidget(0, 10, 0.0001, 5, 0.01720)
        self.QDoubleSpinBox_galvo_offset_x = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0.0)
        self.QDoubleSpinBox_galvo_offset_y = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0.0)
        self.QLCDNumber_galvo_frequency_act = cw.LCDNumberWidget(0, 3)
        self.QDoubleSpinBox_galvo_x_act = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0)
        self.QDoubleSpinBox_galvo_y_act = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0)
        self.QDoubleSpinBox_galvo_range_x_act = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0.4)
        self.QDoubleSpinBox_galvo_range_y_act = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0.4)
        self.QDoubleSpinBox_dot_range_x_act = cw.DoubleSpinBoxWidget(0, 10, 0.0001, 5, 0.2)
        self.QDoubleSpinBox_dot_range_y_act = cw.DoubleSpinBoxWidget(0, 10, 0.0001, 5, 0.2)
        self.QDoubleSpinBox_dot_step_x_act = cw.DoubleSpinBoxWidget(0, 10, 0.0001, 5, 0.01720)
        self.QSpinBox_dot_step_x_act = cw.SpinBoxWidget(0, 4000, 1, 88)
        self.QDoubleSpinBox_sample_high_act = cw.SpinBoxWidget(0, 4000, 1, 1)
        self.QDoubleSpinBox_dot_step_y_act = cw.DoubleSpinBoxWidget(0, 10, 0.0001, 5, 0.01720)
        self.QDoubleSpinBox_galvo_offset_x_act = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0.0)
        self.QDoubleSpinBox_galvo_offset_y_act = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0.0)
        self.QComboBox_galvo_scan_presets = cw.ComboBoxWidget(list_items=[])
        self.QPushButton_save_galvo_scan_presets = cw.PushButtonWidget("Save Scan")
        self.QLineEdit_new_galvo_scan_preset = cw.LineEditWidget()
        self.QPushButton_save_new_galvo_scan_preset = cw.PushButtonWidget("New Scan")

        self.galvo_scroll_area, galvo_scroll_layout = cw.create_scroll_area("Grid")
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Galvo Scanner')), 0, 0)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Readout Scan')), 0, 1)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Activate Scan')), 0, 2)
        galvo_scroll_layout.addWidget(cw.FrameWidget(), 1, 0, 1, 3)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Frequency / Hz')), 2, 0)
        galvo_scroll_layout.addWidget(self.QLCDNumber_galvo_frequency, 2, 1)
        galvo_scroll_layout.addWidget(self.QLCDNumber_galvo_frequency_act, 2, 2)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('X / v')), 3, 0)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_galvo_x, 3, 1)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_galvo_x_act, 3, 2)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Scan Range / V')), 4, 0)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_galvo_range_x, 4, 1)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_galvo_range_x_act, 4, 2)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Dot Range / V')), 5, 0)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_dot_range_x, 5, 1)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_dot_range_x_act, 5, 2)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Dot Step / volt')), 6, 0)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_dot_step_x, 6, 1)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_dot_step_x_act, 6, 2)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Dot Step / sample')), 7, 0)
        galvo_scroll_layout.addWidget(self.QSpinBox_dot_step_x, 7, 1)
        galvo_scroll_layout.addWidget(self.QSpinBox_dot_step_x_act, 7, 2)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Offset X / volt')), 8, 0)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_galvo_offset_x, 8, 1)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_galvo_offset_x_act, 8, 2)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Y / v')), 9, 0)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_galvo_y, 9, 1)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_galvo_y_act, 9, 2)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Scan Range / V')), 10, 0)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_galvo_range_y, 10, 1)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_galvo_range_y_act, 10, 2)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Dot Range / V')), 11, 0)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_dot_range_y, 11, 1)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_dot_range_y_act, 11, 2)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Dot Step / volt')), 12, 0)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_dot_step_y, 12, 1)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_dot_step_y_act, 12, 2)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Offset Y / volt')), 13, 0)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_galvo_offset_y, 13, 1)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_galvo_offset_y_act, 13, 2)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('High / sample')), 14, 0)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_sample_high, 14, 1)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_sample_high_act, 14, 2)
        galvo_scroll_layout.addWidget(self.QComboBox_galvo_scan_presets, 15, 0, 1, 2)
        galvo_scroll_layout.addWidget(self.QPushButton_save_galvo_scan_presets, 15, 2)
        galvo_scroll_layout.addWidget(self.QLineEdit_new_galvo_scan_preset, 16, 0)
        galvo_scroll_layout.addWidget(self.QPushButton_save_new_galvo_scan_preset, 16, 1)

        layout_position.addWidget(self.galvo_scroll_area)
        return layout_position

    def _create_laser_widgets(self):
        layout_illumination = QtWidgets.QHBoxLayout()

        self.QRadioButton_laser_405 = cw.RadioButtonWidget('405 nm')
        self.QDoubleSpinBox_laserpower_405 = cw.DoubleSpinBoxWidget(0, 200, 0.1, 1, 0.0)
        self.QPushButton_laser_405 = cw.PushButtonWidget('ON', checkable=True)
        self.QRadioButton_laser_488 = cw.RadioButtonWidget('488 nm')
        self.QDoubleSpinBox_laserpower_488 = cw.DoubleSpinBoxWidget(0, 200, 0.1, 1, 0.0)
        self.QPushButton_laser_488 = cw.PushButtonWidget('ON', checkable=True)

        self.laser_405_scroll_area, laser_405_scroll_layout = cw.create_scroll_area()
        self.laser_488_scroll_area, laser_488_scroll_layout = cw.create_scroll_area()
        laser_405_scroll_layout.addRow(self.QRadioButton_laser_405, self.QDoubleSpinBox_laserpower_405)
        laser_405_scroll_layout.addRow(self.QPushButton_laser_405)
        laser_488_scroll_layout.addRow(self.QRadioButton_laser_488, self.QDoubleSpinBox_laserpower_488)
        laser_488_scroll_layout.addRow(self.QPushButton_laser_488)

        layout_illumination.addWidget(self.laser_405_scroll_area)
        layout_illumination.addWidget(self.laser_488_scroll_area)
        return layout_illumination

    def _create_daq_widgets(self):
        layout_daq = QtWidgets.QGridLayout()

        self.QSpinBox_daq_sample_rate = cw.SpinBoxWidget(100, 1250, 1, 250)
        self.QPushButton_plot_trigger = cw.PushButtonWidget("Plot Triggers")
        self.QComboBox_send_trigger = cw.ComboBoxWidget(list_items=["video", "acquire", "ao"])
        self.QPushButton_send_trigger = cw.PushButtonWidget("Send Triggers")
        self.QDoubleSpinBox_ttl_start_off = cw.DoubleSpinBoxWidget(0, 50, 0.001, 6, 0.000)
        self.QDoubleSpinBox_ttl_stop_off = cw.DoubleSpinBoxWidget(0, 50, 0.001, 6, 0.010)
        self.QDoubleSpinBox_ttl_start_405 = cw.DoubleSpinBoxWidget(0, 50, 0.001, 6, 0.008)
        self.QDoubleSpinBox_ttl_stop_405 = cw.DoubleSpinBoxWidget(0, 50, 0.001, 6, 0.032)
        self.QDoubleSpinBox_ttl_start_488 = cw.DoubleSpinBoxWidget(0, 50, 0.001, 6, 0.008)
        self.QDoubleSpinBox_ttl_stop_488 = cw.DoubleSpinBoxWidget(0, 50, 0.001, 6, 0.032)
        self.QDoubleSpinBox_ttl_start_thorcam = cw.DoubleSpinBoxWidget(0, 50, 0.001, 6, 0.008)
        self.QDoubleSpinBox_ttl_stop_thorcam = cw.DoubleSpinBoxWidget(0, 50, 0.001, 6, 0.032)
        # self.QDoubleSpinBox_ttl_start_webcam = cw.DoubleSpinBoxWidget(0, 50, 0.001, 6, 0.008)
        # self.QDoubleSpinBox_ttl_stop_webcam = cw.DoubleSpinBoxWidget(0, 50, 0.001, 6, 0.032)

        layout_daq.addWidget(cw.LabelWidget(str('From / s')), 1, 0, 1, 1)
        layout_daq.addWidget(cw.LabelWidget(str('To / s')), 2, 0, 1, 1)
        layout_daq.addWidget(cw.LabelWidget(str('OFF')), 0, 1, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_start_off, 1, 1, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_stop_off, 2, 1, 1, 1)
        layout_daq.addWidget(cw.LabelWidget(str('405')), 0, 2, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_start_405, 1, 2, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_stop_405, 2, 2, 1, 1)
        layout_daq.addWidget(cw.LabelWidget(str('488')), 0, 3, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_start_488, 1, 3, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_stop_488, 2, 3, 1, 1)
        layout_daq.addWidget(cw.LabelWidget(str('Kira')), 0, 4, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_start_thorcam, 1, 4, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_stop_thorcam, 2, 4, 1, 1)
        # layout_daq.addWidget(cw.LabelWidget(str('Web')), 0, 5, 1, 1)
        # layout_daq.addWidget(self.QDoubleSpinBox_ttl_start_webcam, 1, 5, 1, 1)
        # layout_daq.addWidget(self.QDoubleSpinBox_ttl_stop_webcam, 2, 5, 1, 1)
        layout_daq.addWidget(cw.FrameWidget(), 3, 0, 1, 5)
        layout_daq.addWidget(cw.LabelWidget(str('Sample Rate / KS/s')), 4, 0, 1, 1)
        layout_daq.addWidget(self.QSpinBox_daq_sample_rate, 4, 1, 1, 1)
        layout_daq.addWidget(self.QPushButton_plot_trigger, 4, 2, 1, 1)
        layout_daq.addWidget(self.QComboBox_send_trigger, 4, 3, 1, 1)
        layout_daq.addWidget(self.QPushButton_send_trigger, 4, 4, 1, 1)
        return layout_daq

    def _create_video_widgets(self):
        layout_video = QtWidgets.QGridLayout()

        self.QComboBox_imaging_camera_selection = cw.ComboBoxWidget(list_items=["Thorlabs", "WebCam"])
        self.QComboBox_live_modes = cw.ComboBoxWidget(list_items=["Wide Field", "Dot Scan"])
        self.QPushButton_video = cw.PushButtonWidget("Video", checkable=True)
        self.QPushButton_fft = cw.PushButtonWidget("FFT", checkable=True, enable=False)
        self.QComboBox_profile_axis = cw.ComboBoxWidget(list_items=["X", "Y"])
        self.QPushButton_plot_profile = cw.PushButtonWidget("Live Profile", checkable=True, enable=False)
        self.QPushButton_add_profile = cw.PushButtonWidget("Plot Profile")
        self.QPushButton_set_mask = cw.PushButtonWidget("Set Mask")
        self.QPushButton_save_live_timing_presets = cw.PushButtonWidget("Save Live TTLs")

        layout_video.addWidget(self.QComboBox_imaging_camera_selection, 0, 0, 1, 1)
        layout_video.addWidget(self.QComboBox_live_modes, 0, 1, 1, 1)
        layout_video.addWidget(self.QPushButton_video, 0, 2, 1, 1)
        layout_video.addWidget(self.QPushButton_fft, 0, 3, 1, 1)
        layout_video.addWidget(self.QComboBox_profile_axis, 1, 0, 1, 1)
        layout_video.addWidget(self.QPushButton_plot_profile, 1, 1, 1, 1)
        layout_video.addWidget(self.QPushButton_add_profile, 1, 2, 1, 1)
        layout_video.addWidget(self.QPushButton_save_live_timing_presets, 1, 3, 1, 1)
        layout_video.addWidget(self.QPushButton_set_mask, 1, 4, 1, 1)
        return layout_video

    def _create_acquisition_widgets(self):
        layout_acquisition = QtWidgets.QGridLayout()

        self.QComboBox_acquisition_modes = cw.ComboBoxWidget(list_items=["Wide Field 2D", "Dot Scan 2D", "Line Scan 2D"])
        self.QSpinBox_acquisition_number = cw.SpinBoxWidget(1, 50000, 1, 1)
        self.QPushButton_acquire = cw.PushButtonWidget('Acquire')
        self.QPushButton_save_acquisition_timing_presets = cw.PushButtonWidget("Save AcqTTLs")

        layout_acquisition.addWidget(cw.LabelWidget(str('Acq Modes')), 0, 0, 1, 1)
        layout_acquisition.addWidget(self.QComboBox_acquisition_modes, 1, 0, 1, 1)
        layout_acquisition.addWidget(cw.LabelWidget(str('Acq Number')), 0, 1, 1, 1)
        layout_acquisition.addWidget(self.QSpinBox_acquisition_number, 1, 1, 1, 1)
        layout_acquisition.addWidget(self.QPushButton_acquire, 1, 2, 1, 1)
        layout_acquisition.addWidget(self.QPushButton_save_acquisition_timing_presets, 1, 3, 1, 1)

        return layout_acquisition

    def _set_signal_connections(self):
        self.QDoubleSpinBox_galvo_x.valueChanged.connect(self.set_galvo_x)
        self.QDoubleSpinBox_galvo_y.valueChanged.connect(self.set_galvo_y)
        self.QSpinBox_dot_step_x.valueChanged.connect(self.update_galvo_scan)
        self.QDoubleSpinBox_dot_step_x.valueChanged.connect(self.update_galvo_scan)
        self.QSpinBox_dot_step_x_act.valueChanged.connect(self.update_galvo_scan)
        self.QDoubleSpinBox_dot_step_x_act.valueChanged.connect(self.update_galvo_scan)
        self.QComboBox_galvo_scan_presets.currentTextChanged.connect(self.load_selected_preset)
        self.QPushButton_save_galvo_scan_presets.clicked.connect(self.save_galvo_scan_preset)
        self.QPushButton_save_new_galvo_scan_preset.clicked.connect(self.create_new_galvo_preset)
        self.QPushButton_laser_488.clicked.connect(self.set_laser_488)
        self.QPushButton_laser_405.clicked.connect(self.set_laser_405)
        # self.QSpinBox_daq_sample_rate.valueChanged.connect(self.update_daq)
        self.QPushButton_plot_trigger.clicked.connect(self.plot_trigger_sequences)
        self.QPushButton_send_trigger.clicked.connect(self.send_trigger_sequences)
        # self.QPushButton_focus_finding.clicked.connect(self.run_focus_finding)
        self.QPushButton_video.clicked.connect(self.run_video)
        self.QPushButton_fft.clicked.connect(self.run_fft)
        self.QPushButton_plot_profile.clicked.connect(self.run_plot_profile)
        self.QPushButton_add_profile.clicked.connect(self.run_add_profile)
        self.QPushButton_set_mask.clicked.connect(self.set_array_mask)
        self.QPushButton_acquire.clicked.connect(self.run_acquisition)
        self.QComboBox_live_modes.currentIndexChanged[str].connect(self.load_selected_digital_timing_presets)
        self.QComboBox_acquisition_modes.currentIndexChanged[str].connect(self.load_selected_digital_timing_presets)
        self.QPushButton_save_live_timing_presets.clicked.connect(lambda: self.save_digital_timing_preset("live"))
        self.QPushButton_save_acquisition_timing_presets.clicked.connect(lambda: self.save_digital_timing_preset("acquisition"))

    @QtCore.pyqtSlot(float)
    def set_galvo_x(self, value: float):
        vy = self.QDoubleSpinBox_galvo_y.value()
        self.Signal_galvo_set.emit(value, vy)

    @QtCore.pyqtSlot(float)
    def set_galvo_y(self, value: float):
        vx = self.QDoubleSpinBox_galvo_x.value()
        self.Signal_galvo_set.emit(vx, value)

    @QtCore.pyqtSlot()
    def update_galvo_scan(self):
        self.Signal_galvo_scan_update.emit()

    @QtCore.pyqtSlot()
    def save_galvo_scan_preset(self):
        set_name = self.QComboBox_galvo_scan_presets.currentText()
        if not set_name:
            return
        self.galvo_scan_presets[set_name] = {
            "QDoubleSpinBox_galvo_x": self.QDoubleSpinBox_galvo_x.value(),
            "QDoubleSpinBox_galvo_y": self.QDoubleSpinBox_galvo_y.value(),
            "QDoubleSpinBox_galvo_range_x": self.QDoubleSpinBox_galvo_range_x.value(),
            "QDoubleSpinBox_galvo_range_y": self.QDoubleSpinBox_galvo_range_y.value(),
            "QDoubleSpinBox_dot_range_x": self.QDoubleSpinBox_dot_range_x.value(),
            "QDoubleSpinBox_dot_range_y": self.QDoubleSpinBox_dot_range_y.value(),
            "QDoubleSpinBox_dot_step_x": self.QDoubleSpinBox_dot_step_x.value(),
            "QSpinBox_dot_step_x": self.QSpinBox_dot_step_x.value(),
            "QDoubleSpinBox_dot_step_y": self.QDoubleSpinBox_dot_step_y.value(),
            "QDoubleSpinBox_galvo_offset_x": self.QDoubleSpinBox_galvo_offset_x.value(),
            "QDoubleSpinBox_galvo_offset_y": self.QDoubleSpinBox_galvo_offset_y.value(),
            "QDoubleSpinBox_galvo_x_act": self.QDoubleSpinBox_galvo_x_act.value(),
            "QDoubleSpinBox_galvo_y_act": self.QDoubleSpinBox_galvo_y_act.value(),
            "QDoubleSpinBox_galvo_range_x_act": self.QDoubleSpinBox_galvo_range_x_act.value(),
            "QDoubleSpinBox_galvo_range_y_act": self.QDoubleSpinBox_galvo_range_y_act.value(),
            "QDoubleSpinBox_dot_range_x_act": self.QDoubleSpinBox_dot_range_x_act.value(),
            "QDoubleSpinBox_dot_range_y_act": self.QDoubleSpinBox_dot_range_y_act.value(),
            "QDoubleSpinBox_dot_step_x_act": self.QDoubleSpinBox_dot_step_x_act.value(),
            "QSpinBox_dot_step_x_act": self.QSpinBox_dot_step_x_act.value(),
            "QDoubleSpinBox_dot_step_y_act": self.QDoubleSpinBox_dot_step_y_act.value(),
            "QDoubleSpinBox_galvo_offset_x_act": self.QDoubleSpinBox_galvo_offset_x_act.value(),
            "QDoubleSpinBox_galvo_offset_y_act": self.QDoubleSpinBox_galvo_offset_y_act.value()
        }
        self.config.write_config(self.galvo_scan_presets, self.config.configs["Galvo Scan Presets"])

    @QtCore.pyqtSlot(str)
    def load_selected_preset(self, set_name: str):
        values = self.galvo_scan_presets.get(set_name, {})
        self.QDoubleSpinBox_galvo_x.setValue(values.get("QDoubleSpinBox_galvo_x", 0))
        self.QDoubleSpinBox_galvo_y.setValue(values.get("QDoubleSpinBox_galvo_y", 0))
        self.QDoubleSpinBox_galvo_range_x.setValue(values.get("QDoubleSpinBox_galvo_range_x", 0))
        self.QDoubleSpinBox_galvo_range_y.setValue(values.get("QDoubleSpinBox_galvo_range_y", 0))
        self.QDoubleSpinBox_dot_range_x.setValue(values.get("QDoubleSpinBox_dot_range_x", 0))
        self.QDoubleSpinBox_dot_range_y.setValue(values.get("QDoubleSpinBox_dot_range_y", 0))
        self.QDoubleSpinBox_dot_step_x.setValue(values.get("QDoubleSpinBox_dot_step_x", 0))
        self.QSpinBox_dot_step_x.setValue(values.get("QSpinBox_dot_step_x", 0))
        self.QDoubleSpinBox_dot_step_y.setValue(values.get("QDoubleSpinBox_dot_step_y", 0))
        self.QDoubleSpinBox_galvo_offset_x.setValue(values.get("QDoubleSpinBox_galvo_offset_x", 0))
        self.QDoubleSpinBox_galvo_offset_y.setValue(values.get("QDoubleSpinBox_galvo_offset_y", 0))
        self.QDoubleSpinBox_galvo_x_act.setValue(values.get("QDoubleSpinBox_galvo_x_act", 0))
        self.QDoubleSpinBox_galvo_y_act.setValue(values.get("QDoubleSpinBox_galvo_y_act", 0))
        self.QDoubleSpinBox_galvo_range_x_act.setValue(values.get("QDoubleSpinBox_galvo_range_x_act", 0))
        self.QDoubleSpinBox_galvo_range_y_act.setValue(values.get("QDoubleSpinBox_galvo_range_y_act", 0))
        self.QDoubleSpinBox_dot_range_x_act.setValue(values.get("QDoubleSpinBox_dot_range_x_act", 0))
        self.QDoubleSpinBox_dot_range_y_act.setValue(values.get("QDoubleSpinBox_dot_range_y_act", 0))
        self.QDoubleSpinBox_dot_step_x_act.setValue(values.get("QDoubleSpinBox_dot_step_x_act", 0))
        self.QDoubleSpinBox_dot_step_y_act.setValue(values.get("QDoubleSpinBox_dot_step_y_act", 0))
        self.QSpinBox_dot_step_x_act.setValue(values.get("QSpinBox_dot_step_x_act", 0))
        self.QDoubleSpinBox_galvo_offset_x_act.setValue(values.get("QDoubleSpinBox_galvo_offset_x_act", 0))
        self.QDoubleSpinBox_galvo_offset_y_act.setValue(values.get("QDoubleSpinBox_galvo_offset_y_act", 0))

    @QtCore.pyqtSlot()
    def create_new_galvo_preset(self):
        new_preset_name = self.QLineEdit_new_galvo_scan_preset.text().strip()
        if new_preset_name and new_preset_name not in self.galvo_scan_presets:
            self.galvo_scan_presets[new_preset_name] = {
                "QDoubleSpinBox_galvo_x": self.QDoubleSpinBox_galvo_x.value(),
                "QDoubleSpinBox_galvo_y": self.QDoubleSpinBox_galvo_y.value(),
                "QDoubleSpinBox_galvo_range_x": self.QDoubleSpinBox_galvo_range_x.value(),
                "QDoubleSpinBox_galvo_range_y": self.QDoubleSpinBox_galvo_range_y.value(),
                "QDoubleSpinBox_dot_range_x": self.QDoubleSpinBox_dot_range_x.value(),
                "QDoubleSpinBox_dot_range_y": self.QDoubleSpinBox_dot_range_y.value(),
                "QDoubleSpinBox_dot_step_x": self.QDoubleSpinBox_dot_step_x.value(),
                "QSpinBox_dot_step_x": self.QSpinBox_dot_step_x.value(),
                "QDoubleSpinBox_dot_step_y": self.QDoubleSpinBox_dot_step_y.value(),
                "QDoubleSpinBox_galvo_offset_x": self.QDoubleSpinBox_galvo_offset_x.value(),
                "QDoubleSpinBox_galvo_offset_y": self.QDoubleSpinBox_galvo_offset_y.value(),
                "QDoubleSpinBox_galvo_x_act": self.QDoubleSpinBox_galvo_x_act.value(),
                "QDoubleSpinBox_galvo_y_act": self.QDoubleSpinBox_galvo_y_act.value(),
                "QDoubleSpinBox_galvo_range_x_act": self.QDoubleSpinBox_galvo_range_x_act.value(),
                "QDoubleSpinBox_galvo_range_y_act": self.QDoubleSpinBox_galvo_range_y_act.value(),
                "QDoubleSpinBox_dot_range_x_act": self.QDoubleSpinBox_dot_range_x_act.value(),
                "QDoubleSpinBox_dot_range_y_act": self.QDoubleSpinBox_dot_range_y_act.value(),
                "QDoubleSpinBox_dot_step_x_act": self.QDoubleSpinBox_dot_step_x_act.value(),
                "QSpinBox_dot_step_x_act": self.QSpinBox_dot_step_x_act.value(),
                "QDoubleSpinBox_dot_step_y_act": self.QDoubleSpinBox_dot_step_y_act.value(),
                "QDoubleSpinBox_galvo_offset_x_act": self.QDoubleSpinBox_galvo_offset_x_act.value(),
                "QDoubleSpinBox_galvo_offset_y_act": self.QDoubleSpinBox_galvo_offset_y_act.value()
            }
            self.config.write_config(self.galvo_scan_presets, self.config.configs["Galvo Scan Presets"])
            self.QComboBox_galvo_scan_presets.addItem(new_preset_name)
            self.QComboBox_galvo_scan_presets.setCurrentText(new_preset_name)
            self.QLineEdit_new_galvo_scan_preset.clear()

    @QtCore.pyqtSlot(bool)
    def set_laser_488(self, checked: bool):
        power = self.QDoubleSpinBox_laserpower_488.value()
        self.Signal_set_laser.emit(["488"], checked, power)

    @QtCore.pyqtSlot(bool)
    def set_laser_405(self, checked: bool):
        power = self.QDoubleSpinBox_laserpower_405.value()
        self.Signal_set_laser.emit(["405"], checked, power)

    # @QtCore.pyqtSlot(int)
    # def update_daq(self, sample_rate: int):
    #     self.Signal_nucleo_update.emit(sample_rate)

    @QtCore.pyqtSlot()
    def plot_trigger_sequences(self):
        self.Signal_plot_trigger.emit()

    @QtCore.pyqtSlot()
    def send_trigger_sequences(self):
        mod = self.QComboBox_send_trigger.currentText()
        self.Signal_nucleo_send.emit(mod)

    @QtCore.pyqtSlot()
    def run_focus_finding(self):
        self.Signal_focus_finding.emit()

    @QtCore.pyqtSlot()
    def run_video(self):
        vm = self.QComboBox_live_modes.currentText()
        if self.QPushButton_video.isChecked():
            self.Signal_video.emit(True, vm)
            self.QPushButton_fft.setEnabled(True)
            self.QPushButton_plot_profile.setEnabled(True)
        else:
            self.Signal_video.emit(False, vm)
            if self.QPushButton_fft.isChecked():
                self.Signal_fft.emit(False)
            self.QPushButton_fft.setEnabled(False)
            self.QPushButton_fft.setChecked(False)
            if self.QPushButton_plot_profile.isChecked():
                self.Signal_plot_profile.emit(False)
            self.QPushButton_plot_profile.setEnabled(False)
            self.QPushButton_plot_profile.setChecked(False)

    @QtCore.pyqtSlot()
    def run_fft(self):
        if self.QPushButton_fft.isChecked():
            self.Signal_fft.emit(True)
        else:
            self.Signal_fft.emit(False)

    @QtCore.pyqtSlot(bool)
    def run_plot_profile(self, checked: bool):
        self.Signal_plot_profile.emit(checked)

    @QtCore.pyqtSlot()
    def run_add_profile(self):
        self.Signal_add_profile.emit()

    @QtCore.pyqtSlot()
    def set_array_mask(self):
        self.Signal_set_mask.emit()

    @QtCore.pyqtSlot()
    def run_acquisition(self):
        acq_mode = self.QComboBox_acquisition_modes.currentText()
        acq_num = self.QSpinBox_acquisition_number.value()
        self.Signal_data_acquire.emit(acq_mode, acq_num)

    @QtCore.pyqtSlot()
    def run_alignment(self):
        self.Signal_alignment.emit()

    @QtCore.pyqtSlot()
    def run_array_scan(self):
        self.Signal_focal_array_scan.emit()

    @QtCore.pyqtSlot(str)
    def load_selected_digital_timing_presets(self, text: str):
        values = self.digital_timing_presets.get(text, {})
        self.QDoubleSpinBox_ttl_start_405.setValue(values.get("QDoubleSpinBox_ttl_start_off", 0))
        self.QDoubleSpinBox_ttl_stop_405.setValue(values.get("QDoubleSpinBox_ttl_stop_off", 0))
        self.QDoubleSpinBox_ttl_start_405.setValue(values.get("QDoubleSpinBox_ttl_start_405", 0))
        self.QDoubleSpinBox_ttl_stop_405.setValue(values.get("QDoubleSpinBox_ttl_stop_405", 0))
        self.QDoubleSpinBox_ttl_start_488.setValue(values.get("QDoubleSpinBox_ttl_start_488", 0))
        self.QDoubleSpinBox_ttl_stop_488.setValue(values.get("QDoubleSpinBox_ttl_stop_488", 0))
        self.QDoubleSpinBox_ttl_start_thorcam.setValue(values.get("QDoubleSpinBox_ttl_start_thorcam", 0))
        self.QDoubleSpinBox_ttl_stop_thorcam.setValue(values.get("QDoubleSpinBox_ttl_stop_thorcam", 0))
        # self.QDoubleSpinBox_ttl_start_webcam.setValue(values.get("QDoubleSpinBox_ttl_start_webcam", 0))
        # self.QDoubleSpinBox_ttl_stop_webcam.setValue(values.get("QDoubleSpinBox_ttl_stop_webcam", 0))

    @QtCore.pyqtSlot(str)
    def save_digital_timing_preset(self, m: str):
        if m == "live":
            set_name = self.QComboBox_live_modes.currentText()
        elif m == "acquisition":
            set_name = self.QComboBox_acquisition_modes.currentText()
        else:
            set_name = None
        if set_name:
            self.digital_timing_presets[set_name] = {
                    "QDoubleSpinBox_ttl_start_off": self.QDoubleSpinBox_ttl_start_off.value(),
                    "QDoubleSpinBox_ttl_stop_off": self.QDoubleSpinBox_ttl_stop_off.value(),
                    "QDoubleSpinBox_ttl_start_405": self.QDoubleSpinBox_ttl_start_405.value(),
                    "QDoubleSpinBox_ttl_stop_405": self.QDoubleSpinBox_ttl_stop_405.value(),
                    "QDoubleSpinBox_ttl_start_488": self.QDoubleSpinBox_ttl_start_488.value(),
                    "QDoubleSpinBox_ttl_stop_488": self.QDoubleSpinBox_ttl_stop_488.value(),
                    "QDoubleSpinBox_ttl_start_thorcam": self.QDoubleSpinBox_ttl_start_thorcam.value(),
                    "QDoubleSpinBox_ttl_stop_thorcam": self.QDoubleSpinBox_ttl_stop_thorcam.value()
                    # "QDoubleSpinBox_ttl_start_webcam": self.QDoubleSpinBox_ttl_start_webcam.value(),
                    # "QDoubleSpinBox_ttl_stop_webcam": self.QDoubleSpinBox_ttl_stop_webcam.value(),
            }
            self.config.write_config(self.digital_timing_presets, self.config.configs["Digital Timing Presets"])
        else:
            return

    def load_digital_timing_presets(self):
        try:
            presets = self.config.load_config(self.config.configs["Digital Timing Presets"])
            return presets
        except FileNotFoundError:
            return {}

    def load_galvo_scan_presets(self):
        try:
            presets = self.config.load_config(self.config.configs["Galvo Scan Presets"])
            for name, value in presets.items():
                self.QComboBox_galvo_scan_presets.addItem(name)
            return presets
        except FileNotFoundError:
            return {}

    def save_spinbox_values(self):
        values = {}
        for name in dir(self):
            obj = getattr(self, name)
            if isinstance(obj, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
                values[name] = obj.value()
        self.config.write_config(values, self.config.configs["ConWidget Path"])

    def load_spinbox_values(self):
        try:
            values = self.config.load_config(self.config.configs["ConWidget Path"])
            for name, value in values.items():
                widget = getattr(self, name, None)
                if widget is not None:
                    widget.setValue(value)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = ConWidget(None, None, None)
    window.show()
    sys.exit(app.exec_())
