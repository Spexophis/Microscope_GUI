from PyQt5 import QtWidgets, QtCore

from miao.utilities import customized_widgets as cw


class ConWidget(QtWidgets.QWidget):
    Signal_check_emccd_temperature = QtCore.pyqtSignal()
    Signal_switch_emccd_cooler = QtCore.pyqtSignal(bool)
    Signal_piezo_move_usb = QtCore.pyqtSignal(str, float, float, float)
    Signal_piezo_move = QtCore.pyqtSignal(str, float, float, float)
    Signal_deck_read_position = QtCore.pyqtSignal()
    Signal_deck_zero_position = QtCore.pyqtSignal()
    Signal_deck_move_single_step = QtCore.pyqtSignal(bool)
    Signal_deck_move_continuous = QtCore.pyqtSignal(bool, int, float)
    Signal_galvo_set = QtCore.pyqtSignal(float, float)
    Signal_galvo_scan_update = QtCore.pyqtSignal()
    Signal_galvo_path_switch = QtCore.pyqtSignal(float)
    Signal_set_laser = QtCore.pyqtSignal(list, bool, float)
    Signal_daq_update = QtCore.pyqtSignal(int)
    Signal_plot_trigger = QtCore.pyqtSignal()
    Signal_focus_finding = QtCore.pyqtSignal()
    Signal_focus_locking = QtCore.pyqtSignal(bool)
    Signal_video = QtCore.pyqtSignal(bool, str)
    Signal_fft = QtCore.pyqtSignal(bool)
    Signal_plot_profile = QtCore.pyqtSignal(bool)
    Signal_add_profile = QtCore.pyqtSignal()
    Signal_set_mask = QtCore.pyqtSignal()
    Signal_focal_array_scan = QtCore.pyqtSignal()
    Signal_grid_pattern_scan = QtCore.pyqtSignal()
    Signal_alignment = QtCore.pyqtSignal()
    Signal_data_acquire = QtCore.pyqtSignal(str, int)
    Signal_save_file = QtCore.pyqtSignal(str)

    def __init__(self, config, logg, path, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.config = config
        self.logg = logg
        self.data_folder = path
        self._setup_ui()
        self._set_signal_connections()
        self.load_spinbox_values()

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

        self.QLCDNumber_ccd_tempetature = cw.LCDNumberWidget(0, 3)
        self.QPushButton_emccd_cooler_check = cw.PushButtonWidget('Check', False, True)
        self.QPushButton_emccd_cooler_switch = cw.PushButtonWidget('Cooler OFF', True, True, True)
        self.QSpinBox_emccd_coordinate_x = cw.SpinBoxWidget(0, 1024, 1, 1)
        self.QSpinBox_emccd_coordinate_y = cw.SpinBoxWidget(0, 1024, 1, 1)
        self.QSpinBox_emccd_coordinate_nx = cw.SpinBoxWidget(0, 1024, 1, 1024)
        self.QSpinBox_emccd_coordinate_ny = cw.SpinBoxWidget(0, 1024, 1, 1024)
        self.QSpinBox_emccd_coordinate_binx = cw.SpinBoxWidget(0, 1024, 1, 1)
        self.QSpinBox_emccd_coordinate_biny = cw.SpinBoxWidget(0, 1024, 1, 1)
        self.QSpinBox_emccd_gain = cw.SpinBoxWidget(0, 300, 1, 0)
        self.QDoubleSpinBox_emccd_t_clean = cw.DoubleSpinBoxWidget(0, 10, 0.001, 3, 0.009)
        self.QDoubleSpinBox_emccd_exposure_time = cw.DoubleSpinBoxWidget(0, 10, 0.001, 3, 0.000)
        self.QDoubleSpinBox_emccd_t_standby = cw.DoubleSpinBoxWidget(0, 10, 0.001, 3, 0.050)
        self.QDoubleSpinBox_emccd_gvs = cw.DoubleSpinBoxWidget(-5., 5., 0.01, 2, 5.)
        self.emccd_scroll_area, emccd_scroll_layout = cw.create_scroll_area()
        emccd_scroll_layout.addRow(cw.LabelWidget(str('EMCCD')))
        emccd_scroll_layout.addRow(cw.FrameWidget())
        emccd_scroll_layout.addRow(cw.LabelWidget(str('Temperature')), self.QLCDNumber_ccd_tempetature)
        emccd_scroll_layout.addRow(self.QPushButton_emccd_cooler_check, self.QPushButton_emccd_cooler_switch)
        emccd_scroll_layout.addRow(cw.LabelWidget(str('X')), self.QSpinBox_emccd_coordinate_x)
        emccd_scroll_layout.addRow(cw.LabelWidget(str('Y')), self.QSpinBox_emccd_coordinate_y)
        emccd_scroll_layout.addRow(cw.LabelWidget(str('Nx')), self.QSpinBox_emccd_coordinate_nx)
        emccd_scroll_layout.addRow(cw.LabelWidget(str('Ny')), self.QSpinBox_emccd_coordinate_ny)
        emccd_scroll_layout.addRow(cw.LabelWidget(str('Binx')), self.QSpinBox_emccd_coordinate_binx)
        emccd_scroll_layout.addRow(cw.LabelWidget(str('Biny')), self.QSpinBox_emccd_coordinate_biny)
        emccd_scroll_layout.addRow(cw.LabelWidget(str('EMGain')), self.QSpinBox_emccd_gain)
        emccd_scroll_layout.addRow(cw.LabelWidget(str('Clean / s')), self.QDoubleSpinBox_emccd_t_clean)
        emccd_scroll_layout.addRow(cw.LabelWidget(str('Exposure / s')), self.QDoubleSpinBox_emccd_exposure_time)
        emccd_scroll_layout.addRow(cw.LabelWidget(str('Standby / s')), self.QDoubleSpinBox_emccd_t_standby)
        emccd_scroll_layout.addRow(cw.LabelWidget(str('GalvoSW')), self.QDoubleSpinBox_emccd_gvs)

        self.QComboBox_scmos_sensor_modes = cw.ComboBoxWidget(list_items=["Normal", "LightSheet"])
        self.QDoubleSpinBox_scmos_line_exposure = cw.DoubleSpinBoxWidget(1e-5, 10, 0.001, 6, 0.001)
        self.QDoubleSpinBox_scmos_line_interval = cw.DoubleSpinBoxWidget(1e-5, 0.1, 0.001, 6, 0.001)
        self.QDoubleSpinBox_scmos_interval_lines = cw.DoubleSpinBoxWidget(0, 2048, 0.1, 2, 10.5)
        self.QSpinBox_scmos_coordinate_x = cw.SpinBoxWidget(0, 2048, 1, 0)
        self.QSpinBox_scmos_coordinate_y = cw.SpinBoxWidget(0, 2048, 1, 0)
        self.QSpinBox_scmos_coordinate_nx = cw.SpinBoxWidget(0, 2048, 1, 2048)
        self.QSpinBox_scmos_coordinate_ny = cw.SpinBoxWidget(0, 2048, 1, 2048)
        self.QSpinBox_scmos_coordinate_binx = cw.SpinBoxWidget(0, 2048, 1, 1)
        self.QSpinBox_scmos_coordinate_biny = cw.SpinBoxWidget(0, 2048, 1, 1)
        self.QDoubleSpinBox_scmos_gvs = cw.DoubleSpinBoxWidget(-5., 5., 0.01, 2, -2.)
        self.scmos_scroll_area, scmos_scroll_layout = cw.create_scroll_area()
        scmos_scroll_layout.addRow(cw.LabelWidget(str('sCMOS')))
        scmos_scroll_layout.addRow(cw.FrameWidget())
        scmos_scroll_layout.addRow(cw.LabelWidget(str('Readout Mode')), self.QComboBox_scmos_sensor_modes)
        scmos_scroll_layout.addRow(cw.LabelWidget(str('Line Exposure / s')), self.QDoubleSpinBox_scmos_line_exposure)
        scmos_scroll_layout.addRow(cw.LabelWidget(str('Line Interval / s')), self.QDoubleSpinBox_scmos_line_interval)
        scmos_scroll_layout.addRow(cw.LabelWidget(str('Interval Lines')), self.QDoubleSpinBox_scmos_interval_lines)
        scmos_scroll_layout.addRow(cw.LabelWidget(str('X')), self.QSpinBox_scmos_coordinate_x)
        scmos_scroll_layout.addRow(cw.LabelWidget(str('Y')), self.QSpinBox_scmos_coordinate_y)
        scmos_scroll_layout.addRow(cw.LabelWidget(str('Nx')), self.QSpinBox_scmos_coordinate_nx)
        scmos_scroll_layout.addRow(cw.LabelWidget(str('Ny')), self.QSpinBox_scmos_coordinate_ny)
        scmos_scroll_layout.addRow(cw.LabelWidget(str('Binx')), self.QSpinBox_scmos_coordinate_binx)
        scmos_scroll_layout.addRow(cw.LabelWidget(str('Biny')), self.QSpinBox_scmos_coordinate_biny)
        scmos_scroll_layout.addRow(cw.LabelWidget(str('GalvoSW')), self.QDoubleSpinBox_scmos_gvs)

        self.QDoubleSpinBox_thorcam_exposure_time = cw.DoubleSpinBoxWidget(0, 10, 0.005, 3, 0.01)
        self.QSpinBox_thorcam_coordinate_x = cw.SpinBoxWidget(0, 2447, 1, 0)
        self.QSpinBox_thorcam_coordinate_y = cw.SpinBoxWidget(0, 2047, 1, 0)
        self.QSpinBox_thorcam_coordinate_nx = cw.SpinBoxWidget(0, 2448, 1, 2448)
        self.QSpinBox_thorcam_coordinate_ny = cw.SpinBoxWidget(0, 2048, 1, 2048)
        self.QSpinBox_thorcam_coordinate_binx = cw.SpinBoxWidget(0, 2447, 1, 1)
        self.QSpinBox_thorcam_coordinate_biny = cw.SpinBoxWidget(0, 2047, 1, 1)
        self.QDoubleSpinBox_thorcam_gvs = cw.DoubleSpinBoxWidget(-5., 5., 0.01, 2, 0.)
        self.thorcam_scroll_area, thorcam_scroll_layout = cw.create_scroll_area()
        thorcam_scroll_layout.addRow(cw.LabelWidget(str('Thorlabs')))
        thorcam_scroll_layout.addRow(cw.FrameWidget())
        thorcam_scroll_layout.addRow(cw.LabelWidget(str('Exposure / s')), self.QDoubleSpinBox_thorcam_exposure_time)
        thorcam_scroll_layout.addRow(cw.LabelWidget(str('X')), self.QSpinBox_thorcam_coordinate_x)
        thorcam_scroll_layout.addRow(cw.LabelWidget(str('Y')), self.QSpinBox_thorcam_coordinate_y)
        thorcam_scroll_layout.addRow(cw.LabelWidget(str('Nx')), self.QSpinBox_thorcam_coordinate_nx)
        thorcam_scroll_layout.addRow(cw.LabelWidget(str('Ny')), self.QSpinBox_thorcam_coordinate_ny)
        thorcam_scroll_layout.addRow(cw.LabelWidget(str('Binx')), self.QSpinBox_thorcam_coordinate_binx)
        thorcam_scroll_layout.addRow(cw.LabelWidget(str('Biny')), self.QSpinBox_thorcam_coordinate_biny)
        thorcam_scroll_layout.addRow(cw.LabelWidget(str('GalvoSW')), self.QDoubleSpinBox_thorcam_gvs)

        self.QDoubleSpinBox_tis_exposure_time = cw.DoubleSpinBoxWidget(2e-05, 4, 0.0002, 5, 0.0004)
        self.QSpinBox_tis_coordinate_x = cw.SpinBoxWidget(0, 2448, 1, 0)
        self.QSpinBox_tis_coordinate_y = cw.SpinBoxWidget(0, 2048, 1, 0)
        self.QSpinBox_tis_coordinate_nx = cw.SpinBoxWidget(0, 2448, 1, 2448)
        self.QSpinBox_tis_coordinate_ny = cw.SpinBoxWidget(0, 2048, 1, 2048)
        self.QSpinBox_tis_coordinate_binx = cw.SpinBoxWidget(0, 2447, 1, 1)
        self.QSpinBox_tis_coordinate_biny = cw.SpinBoxWidget(0, 2047, 1, 1)
        self.tis_scroll_area, tis_scroll_layout = cw.create_scroll_area()
        tis_scroll_layout.addRow(cw.LabelWidget(str('TIS')))
        tis_scroll_layout.addRow(cw.FrameWidget())
        tis_scroll_layout.addRow(cw.LabelWidget(str('Exposure / s')), self.QDoubleSpinBox_tis_exposure_time)
        tis_scroll_layout.addRow(cw.LabelWidget(str('X')), self.QSpinBox_tis_coordinate_x)
        tis_scroll_layout.addRow(cw.LabelWidget(str('Y')), self.QSpinBox_tis_coordinate_y)
        tis_scroll_layout.addRow(cw.LabelWidget(str('Nx')), self.QSpinBox_tis_coordinate_nx)
        tis_scroll_layout.addRow(cw.LabelWidget(str('Ny')), self.QSpinBox_tis_coordinate_ny)
        tis_scroll_layout.addRow(cw.LabelWidget(str('Binx')), self.QSpinBox_tis_coordinate_binx)
        tis_scroll_layout.addRow(cw.LabelWidget(str('Biny')), self.QSpinBox_tis_coordinate_biny)

        layout_camera.addWidget(self.emccd_scroll_area)
        layout_camera.addWidget(self.scmos_scroll_area)
        layout_camera.addWidget(self.thorcam_scroll_area)
        layout_camera.addWidget(self.tis_scroll_area)
        return layout_camera

    def _create_position_widgets(self):
        layout_position = QtWidgets.QHBoxLayout()

        self.QLCDNumber_deck_position = cw.LCDNumberWidget()
        self.QPushButton_deck_position = cw.PushButtonWidget('Read')
        self.QPushButton_deck_position_zero = cw.PushButtonWidget('Zero')
        self.QPushButton_move_deck_up = cw.PushButtonWidget('Up')
        self.QPushButton_move_deck_down = cw.PushButtonWidget('Down')
        self.QSpinBox_deck_direction = cw.SpinBoxWidget(-1, 1, 2, 1)
        self.QDoubleSpinBox_deck_velocity = cw.DoubleSpinBoxWidget(0.02, 1.50, 0.02, 2, 0.02)
        self.QPushButton_move_deck = cw.PushButtonWidget('Move', checkable=True)
        self.mad_deck_scroll_area, mad_deck_scroll_layout = cw.create_scroll_area()
        mad_deck_scroll_layout.addRow(cw.LabelWidget(str('Mad Deck')))
        mad_deck_scroll_layout.addRow(cw.FrameWidget())
        mad_deck_scroll_layout.addRow(cw.LabelWidget(str('Position (mm)')), self.QLCDNumber_deck_position)
        mad_deck_scroll_layout.addRow(self.QPushButton_deck_position, self.QPushButton_deck_position_zero)
        mad_deck_scroll_layout.addRow(cw.LabelWidget(str('Direction (+up)')), self.QSpinBox_deck_direction)
        mad_deck_scroll_layout.addRow(cw.LabelWidget(str('Velocity (mm)')), self.QDoubleSpinBox_deck_velocity)
        mad_deck_scroll_layout.addRow(self.QPushButton_move_deck)
        mad_deck_scroll_layout.addRow(cw.LabelWidget(str('Single step')))
        mad_deck_scroll_layout.addRow(self.QPushButton_move_deck_up, self.QPushButton_move_deck_down)

        self.QDoubleSpinBox_stage_x_usb = cw.DoubleSpinBoxWidget(0, 100, 0.020, 3, 20.000)
        self.QLCDNumber_piezo_position_x = cw.LCDNumberWidget()
        self.QDoubleSpinBox_stage_x = cw.DoubleSpinBoxWidget(0, 100, 0.020, 3, 30.000)
        self.QDoubleSpinBox_step_x = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.030)
        self.QDoubleSpinBox_range_x = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.780)
        self.QDoubleSpinBox_stage_y_usb = cw.DoubleSpinBoxWidget(0, 100, 0.020, 3, 20.000)
        self.QLCDNumber_piezo_position_y = cw.LCDNumberWidget()
        self.QDoubleSpinBox_stage_y = cw.DoubleSpinBoxWidget(0, 100, 0.020, 3, 30.000)
        self.QDoubleSpinBox_step_y = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.030)
        self.QDoubleSpinBox_range_y = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.780)
        self.QDoubleSpinBox_stage_z_usb = cw.DoubleSpinBoxWidget(0, 100, 0.04, 2, 20.00)
        self.QLCDNumber_piezo_position_z = cw.LCDNumberWidget()
        self.QDoubleSpinBox_stage_z = cw.DoubleSpinBoxWidget(0, 100, 0.04, 2, 30.00)
        self.QDoubleSpinBox_step_z = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.160)
        self.QDoubleSpinBox_range_z = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 4.80)
        self.QDoubleSpinBox_piezo_return_time = cw.DoubleSpinBoxWidget(0, 50, 0.01, 2, 0.06)
        self.QPushButton_focus_finding = cw.PushButtonWidget('Find Focus')
        self.QPushButton_focus_locking = cw.PushButtonWidget('Lock Focus', checkable=True)
        self.QDoubleSpinBox_pid_kp = cw.DoubleSpinBoxWidget(0, 100, 0.01, 2, 0.5)
        self.QDoubleSpinBox_pid_ki = cw.DoubleSpinBoxWidget(0, 100, 0.01, 2, 0.5)
        self.QDoubleSpinBox_pid_kd = cw.DoubleSpinBoxWidget(0, 100, 0.01, 2, 0.0)
        self.mcl_piezo_scroll_area, mcl_piezo_scroll_layout = cw.create_scroll_area("Grid")
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('MCL Piezo')), 0, 0)
        mcl_piezo_scroll_layout.addWidget(cw.FrameWidget(), 1, 0, 1, 3)
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('X (um)')), 2, 0)
        mcl_piezo_scroll_layout.addWidget(self.QDoubleSpinBox_stage_x_usb, 2, 1)
        mcl_piezo_scroll_layout.addWidget(self.QLCDNumber_piezo_position_x, 2, 2)
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('Origin / um')), 3, 0)
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('Step / um')), 3, 1)
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('Range / um')), 3, 2)
        mcl_piezo_scroll_layout.addWidget(self.QDoubleSpinBox_stage_x, 4, 0)
        mcl_piezo_scroll_layout.addWidget(self.QDoubleSpinBox_step_x, 4, 1)
        mcl_piezo_scroll_layout.addWidget(self.QDoubleSpinBox_range_x, 4, 2)
        mcl_piezo_scroll_layout.addWidget(cw.FrameWidget(), 5, 0, 1, 3)
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('Y (um)')), 6, 0)
        mcl_piezo_scroll_layout.addWidget(self.QDoubleSpinBox_stage_y_usb, 6, 1)
        mcl_piezo_scroll_layout.addWidget(self.QLCDNumber_piezo_position_y, 6, 2)
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('Origin / um')), 7, 0)
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('Step / um')), 7, 1)
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('Range / um')), 7, 2)
        mcl_piezo_scroll_layout.addWidget(self.QDoubleSpinBox_stage_y, 8, 0)
        mcl_piezo_scroll_layout.addWidget(self.QDoubleSpinBox_step_y, 8, 1)
        mcl_piezo_scroll_layout.addWidget(self.QDoubleSpinBox_range_y, 8, 2)
        mcl_piezo_scroll_layout.addWidget(cw.FrameWidget(), 9, 0, 1, 3)
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('Z (um)')), 10, 0)
        mcl_piezo_scroll_layout.addWidget(self.QDoubleSpinBox_stage_z_usb, 10, 1)
        mcl_piezo_scroll_layout.addWidget(self.QLCDNumber_piezo_position_z, 10, 2)
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('Origin / um')), 11, 0)
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('Step / um')), 11, 1)
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('Range / um')), 11, 2)
        mcl_piezo_scroll_layout.addWidget(self.QDoubleSpinBox_stage_z, 12, 0)
        mcl_piezo_scroll_layout.addWidget(self.QDoubleSpinBox_step_z, 12, 1)
        mcl_piezo_scroll_layout.addWidget(self.QDoubleSpinBox_range_z, 12, 2)
        mcl_piezo_scroll_layout.addWidget(cw.FrameWidget(), 13, 0, 1, 3)
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('Piezo Return / s')), 14, 0)
        mcl_piezo_scroll_layout.addWidget(self.QDoubleSpinBox_piezo_return_time, 14, 1)
        mcl_piezo_scroll_layout.addWidget(cw.FrameWidget(), 15, 0, 1, 3)
        mcl_piezo_scroll_layout.addWidget(self.QPushButton_focus_finding, 16, 0)
        mcl_piezo_scroll_layout.addWidget(self.QPushButton_focus_locking, 16, 1)
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('PID - kP')), 17, 0)
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('PID - kI')), 17, 1)
        mcl_piezo_scroll_layout.addWidget(cw.LabelWidget(str('PID - kD')), 17, 2)
        mcl_piezo_scroll_layout.addWidget(self.QDoubleSpinBox_pid_kp, 18, 0)
        mcl_piezo_scroll_layout.addWidget(self.QDoubleSpinBox_pid_ki, 18, 1)
        mcl_piezo_scroll_layout.addWidget(self.QDoubleSpinBox_pid_kd, 18, 2)

        self.QLCDNumber_galvo_frequency = cw.LCDNumberWidget(0, 3)
        self.QDoubleSpinBox_galvo_x = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0)
        self.QDoubleSpinBox_galvo_y = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0)
        self.QDoubleSpinBox_galvo_range_x = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0.4)
        self.QDoubleSpinBox_galvo_range_y = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0.4)
        self.QDoubleSpinBox_dot_range_x = cw.DoubleSpinBoxWidget(0, 20, 0.0001, 5, 0.2)
        self.QDoubleSpinBox_dot_range_y = cw.DoubleSpinBoxWidget(0, 20, 0.0001, 5, 0.2)
        self.QDoubleSpinBox_dot_step_x = cw.DoubleSpinBoxWidget(0, 20, 0.0001, 5, 0.01720)
        self.QSpinBox_dot_step_x = cw.SpinBoxWidget(0, 4000, 1, 88)
        self.QDoubleSpinBox_dot_step_y = cw.DoubleSpinBoxWidget(0, 20, 0.0001, 5, 0.01720)
        self.QLCDNumber_galvo_frequency_act = cw.LCDNumberWidget(0, 3)
        self.QDoubleSpinBox_galvo_x_act = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0)
        self.QDoubleSpinBox_galvo_y_act = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0)
        self.QDoubleSpinBox_galvo_range_x_act = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0.4)
        self.QDoubleSpinBox_galvo_range_y_act = cw.DoubleSpinBoxWidget(-10, 10, 0.0001, 5, 0.4)
        self.QDoubleSpinBox_dot_range_x_act = cw.DoubleSpinBoxWidget(0, 20, 0.0001, 5, 0.2)
        self.QDoubleSpinBox_dot_range_y_act = cw.DoubleSpinBoxWidget(0, 20, 0.0001, 5, 0.2)
        self.QDoubleSpinBox_dot_step_x_act = cw.DoubleSpinBoxWidget(0, 20, 0.0001, 5, 0.01720)
        self.QSpinBox_dot_step_x_act = cw.SpinBoxWidget(0, 4000, 1, 88)
        self.QDoubleSpinBox_dot_step_y_act = cw.DoubleSpinBoxWidget(0, 20, 0.0001, 5, 0.01720)
        self.QDoubleSpinBox_path_switch_galvo = cw.DoubleSpinBoxWidget(-5.0, 5.0, 0.1, 4, 5)
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
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Y / v')), 8, 0)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_galvo_y, 8, 1)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_galvo_y_act, 8, 2)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Scan Range / V')), 9, 0)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_galvo_range_y, 9, 1)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_galvo_range_y_act, 9, 2)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Dot Range / V')), 10, 0)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_dot_range_y, 10, 1)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_dot_range_y_act, 10, 2)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Dot Step / volt')), 11, 0)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_dot_step_y, 11, 1)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_dot_step_y_act, 11, 2)
        galvo_scroll_layout.addWidget(cw.LabelWidget(str('Path Switch')), 12, 0)
        galvo_scroll_layout.addWidget(self.QDoubleSpinBox_path_switch_galvo, 12, 1)
        layout_position.addWidget(self.mad_deck_scroll_area)
        layout_position.addWidget(self.mcl_piezo_scroll_area)
        layout_position.addWidget(self.galvo_scroll_area)
        return layout_position

    def _create_laser_widgets(self):
        layout_illumination = QtWidgets.QHBoxLayout()

        self.QRadioButton_laser_405 = cw.RadioButtonWidget('405 nm')
        self.QDoubleSpinBox_laserpower_405 = cw.DoubleSpinBoxWidget(0, 200, 0.1, 1, 0.0)
        self.QPushButton_laser_405 = cw.PushButtonWidget('ON', checkable=True)
        self.QRadioButton_laser_488_0 = cw.RadioButtonWidget('488 nm #0')
        self.QDoubleSpinBox_laserpower_488_0 = cw.DoubleSpinBoxWidget(0, 200, 0.1, 1, 0.0)
        self.QPushButton_laser_488_0 = cw.PushButtonWidget('ON', checkable=True)
        self.QRadioButton_laser_488_1 = cw.RadioButtonWidget('488 nm #1')
        self.QDoubleSpinBox_laserpower_488_1 = cw.DoubleSpinBoxWidget(0, 200, 0.1, 1, 0.0)
        self.QPushButton_laser_488_1 = cw.PushButtonWidget('ON', checkable=True)
        self.QRadioButton_laser_488_2 = cw.RadioButtonWidget('488 nm #2')
        self.QDoubleSpinBox_laserpower_488_2 = cw.DoubleSpinBoxWidget(0, 200, 0.1, 1, 0.0)
        self.QPushButton_laser_488_2 = cw.PushButtonWidget('ON', checkable=True)
        self.laser_405_scroll_area, laser_405_scroll_layout = cw.create_scroll_area()
        self.laser_488_0_scroll_area, laser_488_0_scroll_layout = cw.create_scroll_area()
        self.laser_488_1_scroll_area, laser_488_1_scroll_layout = cw.create_scroll_area()
        self.laser_488_2_scroll_area, laser_488_2_scroll_layout = cw.create_scroll_area()
        laser_405_scroll_layout.addRow(self.QRadioButton_laser_405, self.QDoubleSpinBox_laserpower_405)
        laser_405_scroll_layout.addRow(self.QPushButton_laser_405)
        laser_488_0_scroll_layout.addRow(self.QRadioButton_laser_488_0, self.QDoubleSpinBox_laserpower_488_0)
        laser_488_0_scroll_layout.addRow(self.QPushButton_laser_488_0)
        laser_488_1_scroll_layout.addRow(self.QRadioButton_laser_488_1, self.QDoubleSpinBox_laserpower_488_1)
        laser_488_1_scroll_layout.addRow(self.QPushButton_laser_488_1)
        laser_488_2_scroll_layout.addRow(self.QRadioButton_laser_488_2, self.QDoubleSpinBox_laserpower_488_2)
        laser_488_2_scroll_layout.addRow(self.QPushButton_laser_488_2)

        layout_illumination.addWidget(self.laser_405_scroll_area)
        layout_illumination.addWidget(self.laser_488_0_scroll_area)
        layout_illumination.addWidget(self.laser_488_1_scroll_area)
        layout_illumination.addWidget(self.laser_488_2_scroll_area)
        return layout_illumination

    def _create_daq_widgets(self):
        layout_daq = QtWidgets.QGridLayout()

        self.QSpinBox_daq_sample_rate = cw.SpinBoxWidget(100, 1250, 1, 250)
        self.QPushButton_plot_trigger = cw.PushButtonWidget("Plot Triggers")
        self.QDoubleSpinBox_ttl_start_on_405 = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.008)
        self.QDoubleSpinBox_ttl_stop_on_405 = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.032)
        self.QDoubleSpinBox_ttl_start_off_488_0 = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.008)
        self.QDoubleSpinBox_ttl_stop_off_488_0 = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.032)
        self.QDoubleSpinBox_ttl_start_off_488_1 = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.008)
        self.QDoubleSpinBox_ttl_stop_off_488_1 = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.032)
        self.QDoubleSpinBox_ttl_start_read_488_2 = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.008)
        self.QDoubleSpinBox_ttl_stop_read_488_2 = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.032)
        self.QDoubleSpinBox_ttl_start_emccd = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.008)
        self.QDoubleSpinBox_ttl_stop_emccd = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.032)
        self.QDoubleSpinBox_ttl_start_scmos = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.008)
        self.QDoubleSpinBox_ttl_stop_scmos = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.032)
        self.QDoubleSpinBox_ttl_start_thorcam = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.008)
        self.QDoubleSpinBox_ttl_stop_thorcam = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.032)
        self.QDoubleSpinBox_ttl_start_tis = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.008)
        self.QDoubleSpinBox_ttl_stop_tis = cw.DoubleSpinBoxWidget(0, 50, 0.001, 3, 0.032)
        layout_daq.addWidget(cw.LabelWidget(str('Sample Rate / KS/s')), 0, 0, 1, 1)
        layout_daq.addWidget(self.QSpinBox_daq_sample_rate, 1, 0, 1, 1)
        layout_daq.addWidget(self.QPushButton_plot_trigger, 2, 0, 1, 1)
        layout_daq.addWidget(cw.LabelWidget(str('From / s')), 1, 1, 1, 1)
        layout_daq.addWidget(cw.LabelWidget(str('To / s')), 2, 1, 1, 1)
        layout_daq.addWidget(cw.LabelWidget(str('DO#0 - L405')), 0, 2, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_start_on_405, 1, 2, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_stop_on_405, 2, 2, 1, 1)
        layout_daq.addWidget(cw.LabelWidget(str('DO#1 - L488')), 0, 3, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_start_off_488_0, 1, 3, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_stop_off_488_0, 2, 3, 1, 1)
        layout_daq.addWidget(cw.LabelWidget(str('DO#2 - L488')), 0, 4, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_start_off_488_1, 1, 4, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_stop_off_488_1, 2, 4, 1, 1)
        layout_daq.addWidget(cw.LabelWidget(str('DO#3 - L488')), 0, 5, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_start_read_488_2, 1, 5, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_stop_read_488_2, 2, 5, 1, 1)
        layout_daq.addWidget(cw.LabelWidget(str('DO#4 - iXon')), 0, 6, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_start_emccd, 1, 6, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_stop_emccd, 2, 6, 1, 1)
        layout_daq.addWidget(cw.LabelWidget(str('DO#5 - ORCA')), 0, 7, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_start_scmos, 1, 7, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_stop_scmos, 2, 7, 1, 1)
        layout_daq.addWidget(cw.LabelWidget(str('DO#6 - Kira')), 0, 8, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_start_thorcam, 1, 8, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_stop_thorcam, 2, 8, 1, 1)
        layout_daq.addWidget(cw.LabelWidget(str('DO#7 - DMK')), 0, 9, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_start_tis, 1, 9, 1, 1)
        layout_daq.addWidget(self.QDoubleSpinBox_ttl_stop_tis, 2, 9, 1, 1)
        return layout_daq

    def _create_video_widgets(self):
        layout_video = QtWidgets.QHBoxLayout()
        self.QComboBox_imaging_camera_selection = cw.ComboBoxWidget(list_items=["EMCCD", "SCMOS", "Thorlabs", "TIS"])
        self.QComboBox_live_modes = cw.ComboBoxWidget(list_items=["Wide Field", "Dot Scan", "Focus Lock", "Scan Calib"])
        self.QPushButton_video = cw.PushButtonWidget("Video", checkable=True)
        self.QPushButton_fft = cw.PushButtonWidget("FFT", checkable=True, enable=False)
        self.QComboBox_profile_axis = cw.ComboBoxWidget(list_items=["X", "Y"])
        self.QPushButton_plot_profile = cw.PushButtonWidget("Live Profile", checkable=True, enable=False)
        self.QPushButton_add_profile = cw.PushButtonWidget("Plot Profile")
        self.QPushButton_set_mask = cw.PushButtonWidget("Set Mask")
        layout_video.addWidget(self.QComboBox_imaging_camera_selection)
        layout_video.addWidget(self.QComboBox_live_modes)
        layout_video.addWidget(self.QPushButton_video)
        layout_video.addWidget(self.QPushButton_fft)
        layout_video.addWidget(self.QComboBox_profile_axis)
        layout_video.addWidget(self.QPushButton_plot_profile)
        layout_video.addWidget(self.QPushButton_add_profile)
        layout_video.addWidget(self.QPushButton_set_mask)
        return layout_video

    def _create_acquisition_widgets(self):
        layout_acquisition = QtWidgets.QGridLayout()
        self.QComboBox_acquisition_modes = cw.ComboBoxWidget(list_items=["Wide Field 2D", "Wide Field 3D",
                                                                         "Monalisa Scan 2D", "Monalisa Scan 3D",
                                                                         "Dot Scan 2D", "Dot Scan 3D"])
        self.QSpinBox_acquisition_number = cw.SpinBoxWidget(1, 50000, 1, 1)
        self.QPushButton_alignment = cw.PushButtonWidget('Alignment')
        self.QPushButton_acquire = cw.PushButtonWidget('Acquire')
        self.QPushButton_focal_array_scan = cw.PushButtonWidget('FocalArray Scan')
        self.QPushButton_grid_pattern_scan = cw.PushButtonWidget('GridPattern Scan')
        layout_acquisition.addWidget(cw.LabelWidget(str('Acq Modes')), 0, 0, 1, 1)
        layout_acquisition.addWidget(self.QComboBox_acquisition_modes, 1, 0, 1, 1)
        layout_acquisition.addWidget(cw.LabelWidget(str('Acq Number')), 0, 1, 1, 1)
        layout_acquisition.addWidget(self.QSpinBox_acquisition_number, 1, 1, 1, 1)
        layout_acquisition.addWidget(self.QPushButton_alignment, 0, 2, 1, 1)
        layout_acquisition.addWidget(self.QPushButton_acquire, 1, 2, 1, 1)
        layout_acquisition.addWidget(self.QPushButton_grid_pattern_scan, 0, 3, 1, 1)
        layout_acquisition.addWidget(self.QPushButton_focal_array_scan, 1, 3, 1, 1)
        return layout_acquisition

    def _set_signal_connections(self):
        self.QPushButton_emccd_cooler_check.clicked.connect(self.check_emccd_temperature)
        self.QPushButton_emccd_cooler_switch.clicked.connect(self.switch_emccd_cooler)
        self.QDoubleSpinBox_stage_x.valueChanged.connect(self.set_piezo_x)
        self.QDoubleSpinBox_stage_y.valueChanged.connect(self.set_piezo_y)
        self.QDoubleSpinBox_stage_z.valueChanged.connect(self.set_piezo_z)
        self.QDoubleSpinBox_stage_x_usb.valueChanged.connect(self.set_piezo_x_usb)
        self.QDoubleSpinBox_stage_y_usb.valueChanged.connect(self.set_piezo_y_usb)
        self.QDoubleSpinBox_stage_z_usb.valueChanged.connect(self.set_piezo_z_usb)
        self.QPushButton_deck_position.clicked.connect(self.read_deck)
        self.QPushButton_deck_position_zero.clicked.connect(self.zero_deck)
        self.QPushButton_move_deck_up.clicked.connect(self.deck_move_up)
        self.QPushButton_move_deck_down.clicked.connect(self.deck_move_down)
        self.QPushButton_move_deck.clicked.connect(self.deck_move_range)
        self.QDoubleSpinBox_galvo_x.valueChanged.connect(self.set_galvo_x)
        self.QDoubleSpinBox_galvo_y.valueChanged.connect(self.set_galvo_y)
        self.QDoubleSpinBox_path_switch_galvo.valueChanged.connect(self.set_path_switch_galvo)
        self.QSpinBox_dot_step_x.valueChanged.connect(self.update_galvo_scan)
        self.QDoubleSpinBox_dot_step_x.valueChanged.connect(self.update_galvo_scan)
        self.QSpinBox_dot_step_x_act.valueChanged.connect(self.update_galvo_scan)
        self.QDoubleSpinBox_dot_step_x_act.valueChanged.connect(self.update_galvo_scan)
        self.QPushButton_laser_488_0.clicked.connect(self.set_laser_488_0)
        self.QPushButton_laser_488_1.clicked.connect(self.set_laser_488_1)
        self.QPushButton_laser_488_2.clicked.connect(self.set_laser_488_2)
        self.QPushButton_laser_405.clicked.connect(self.set_laser_405)
        self.QSpinBox_daq_sample_rate.valueChanged.connect(self.update_daq)
        self.QPushButton_plot_trigger.clicked.connect(self.plot_trigger_sequence)
        self.QPushButton_focus_finding.clicked.connect(self.run_focus_finding)
        self.QPushButton_focus_locking.clicked.connect(self.run_focus_locking)
        self.QPushButton_video.clicked.connect(self.run_video)
        self.QPushButton_fft.clicked.connect(self.run_fft)
        self.QPushButton_plot_profile.clicked.connect(self.run_plot_profile)
        self.QPushButton_add_profile.clicked.connect(self.run_add_profile)
        self.QPushButton_set_mask.clicked.connect(self.set_array_mask)
        self.QPushButton_acquire.clicked.connect(self.run_acquisition)
        self.QPushButton_alignment.clicked.connect(self.run_alignment)
        self.QPushButton_focal_array_scan.clicked.connect(self.run_array_scan)
        self.QPushButton_grid_pattern_scan.clicked.connect(self.run_pattern_scan)
        self.QComboBox_live_modes.currentIndexChanged[str].connect(self.update_live_parameter_sets)
        self.QComboBox_acquisition_modes.currentIndexChanged[str].connect(self.update_acquisition_parameter_sets)

    @QtCore.pyqtSlot()
    def check_emccd_temperature(self):
        self.Signal_check_emccd_temperature.emit()

    @QtCore.pyqtSlot(bool)
    def switch_emccd_cooler(self, checked: bool):
        self.Signal_switch_emccd_cooler.emit(checked)
        if checked:
            self.QPushButton_emccd_cooler_switch.setText("Cooler ON")
        else:
            self.QPushButton_emccd_cooler_switch.setText("Cooler OFF")

    @QtCore.pyqtSlot(float)
    def set_piezo_x(self, pos_x: float):
        pos_y = self.QDoubleSpinBox_stage_y.value()
        pos_z = self.QDoubleSpinBox_stage_z.value()
        self.Signal_piezo_move.emit("x", pos_x, pos_y, pos_z)

    @QtCore.pyqtSlot(float)
    def set_piezo_y(self, pos_y: float):
        pos_x = self.QDoubleSpinBox_stage_x.value()
        pos_z = self.QDoubleSpinBox_stage_z.value()
        self.Signal_piezo_move.emit("y", pos_x, pos_y, pos_z)

    @QtCore.pyqtSlot(float)
    def set_piezo_z(self, pos_z: float):
        pos_x = self.QDoubleSpinBox_stage_x.value()
        pos_y = self.QDoubleSpinBox_stage_y.value()
        self.Signal_piezo_move.emit("z", pos_x, pos_y, pos_z)

    @QtCore.pyqtSlot(float)
    def set_piezo_x_usb(self, pos_x: float):
        pos_y = self.QDoubleSpinBox_stage_y.value()
        pos_z = self.QDoubleSpinBox_stage_z.value()
        self.Signal_piezo_move_usb.emit("x", pos_x, pos_y, pos_z)

    @QtCore.pyqtSlot(float)
    def set_piezo_y_usb(self, pos_y: float):
        pos_x = self.QDoubleSpinBox_stage_x.value()
        pos_z = self.QDoubleSpinBox_stage_z.value()
        self.Signal_piezo_move_usb.emit("y", pos_x, pos_y, pos_z)

    @QtCore.pyqtSlot(float)
    def set_piezo_z_usb(self, pos_z: float):
        pos_x = self.QDoubleSpinBox_stage_x.value()
        pos_y = self.QDoubleSpinBox_stage_y.value()
        self.Signal_piezo_move_usb.emit("z", pos_x, pos_y, pos_z)

    @QtCore.pyqtSlot()
    def read_deck(self):
        self.Signal_deck_read_position.emit()

    @QtCore.pyqtSlot()
    def zero_deck(self):
        self.Signal_deck_zero_position.emit()

    @QtCore.pyqtSlot()
    def deck_move_up(self):
        self.Signal_deck_move_single_step.emit(True)

    @QtCore.pyqtSlot()
    def deck_move_down(self):
        self.Signal_deck_move_single_step.emit(False)

    @QtCore.pyqtSlot(bool)
    def deck_move_range(self, checked: bool):
        distance = self.QSpinBox_deck_direction.value()
        velocity = self.QDoubleSpinBox_deck_velocity.value()
        self.Signal_deck_move_continuous.emit(checked, distance, velocity)

    @QtCore.pyqtSlot(float)
    def set_galvo_x(self, value: float):
        vy = self.QDoubleSpinBox_galvo_y.value()
        self.Signal_galvo_set.emit(value, vy)

    @QtCore.pyqtSlot(float)
    def set_galvo_y(self, value: float):
        vx = self.QDoubleSpinBox_galvo_x.value()
        self.Signal_galvo_set.emit(vx, value)

    @QtCore.pyqtSlot(float)
    def set_path_switch_galvo(self, value: float):
        self.Signal_galvo_path_switch.emit(value)

    @QtCore.pyqtSlot()
    def update_galvo_scan(self):
        self.Signal_galvo_scan_update.emit()

    @QtCore.pyqtSlot(bool)
    def set_laser_488_0(self, checked: bool):
        power = self.QDoubleSpinBox_laserpower_488_0.value()
        self.Signal_set_laser.emit(["488_0"], checked, power)

    @QtCore.pyqtSlot(bool)
    def set_laser_488_1(self, checked: bool):
        power = self.QDoubleSpinBox_laserpower_488_1.value()
        self.Signal_set_laser.emit(["488_1"], checked, power)

    @QtCore.pyqtSlot(bool)
    def set_laser_488_2(self, checked: bool):
        power = self.QDoubleSpinBox_laserpower_488_2.value()
        self.Signal_set_laser.emit(["488_2"], checked, power)

    @QtCore.pyqtSlot(bool)
    def set_laser_405(self, checked: bool):
        power = self.QDoubleSpinBox_laserpower_405.value()
        self.Signal_set_laser.emit(["405"], checked, power)

    @QtCore.pyqtSlot(int)
    def update_daq(self, sample_rate: int):
        self.Signal_daq_update.emit(sample_rate)

    @QtCore.pyqtSlot()
    def plot_trigger_sequence(self):
        self.Signal_plot_trigger.emit()

    @QtCore.pyqtSlot()
    def run_focus_finding(self):
        self.Signal_focus_finding.emit()

    @QtCore.pyqtSlot()
    def run_focus_locking(self):
        if self.QPushButton_focus_locking.isChecked():
            self.Signal_focus_locking.emit(True)
        else:
            self.Signal_focus_locking.emit(False)

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

    @QtCore.pyqtSlot()
    def run_pattern_scan(self):
        self.Signal_grid_pattern_scan.emit()

    @QtCore.pyqtSlot(str)
    def update_live_parameter_sets(self, text: str):
        if text == "Wide Field":
            self.QDoubleSpinBox_ttl_start_on_405.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_on_405.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_off_488_0.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_off_488_0.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_off_488_1.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_off_488_1.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_read_488_2.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_read_488_2.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_emccd.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_emccd.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_scmos.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_scmos.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_tis.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_tis.setValue(0.032)
        if text == "Dot Scan":
            self.QDoubleSpinBox_ttl_start_on_405.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_on_405.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_off_488_0.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_off_488_0.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_off_488_1.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_off_488_1.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_read_488_2.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_read_488_2.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_emccd.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_emccd.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_scmos.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_scmos.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_tis.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_tis.setValue(0.032)

    @QtCore.pyqtSlot(str)
    def update_acquisition_parameter_sets(self, text: str):
        if text == "Wide Field 2D":
            self.QDoubleSpinBox_step_x.setValue(0.030)
            self.QDoubleSpinBox_step_y.setValue(0.030)
            self.QDoubleSpinBox_step_z.setValue(0.160)
            self.QDoubleSpinBox_range_x.setValue(0.000)
            self.QDoubleSpinBox_range_y.setValue(0.000)
            self.QDoubleSpinBox_range_z.setValue(0.000)
            self.QDoubleSpinBox_ttl_start_on_405.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_on_405.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_off_488_0.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_off_488_0.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_off_488_1.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_off_488_1.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_read_488_2.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_read_488_2.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_emccd.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_emccd.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_scmos.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_scmos.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_tis.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_tis.setValue(0.032)
        if text == "Wide Field 3D":
            self.QDoubleSpinBox_step_x.setValue(0.030)
            self.QDoubleSpinBox_step_y.setValue(0.030)
            self.QDoubleSpinBox_step_z.setValue(0.160)
            self.QDoubleSpinBox_range_x.setValue(0.000)
            self.QDoubleSpinBox_range_y.setValue(0.000)
            self.QDoubleSpinBox_range_z.setValue(4.800)
            self.QDoubleSpinBox_ttl_start_on_405.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_on_405.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_off_488_0.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_off_488_0.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_off_488_1.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_off_488_1.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_read_488_2.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_read_488_2.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_emccd.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_emccd.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_scmos.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_scmos.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_tis.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_tis.setValue(0.032)
        if text == "Dot Scan 2D":
            self.QDoubleSpinBox_step_x.setValue(0.030)
            self.QDoubleSpinBox_step_y.setValue(0.030)
            self.QDoubleSpinBox_step_z.setValue(0.160)
            self.QDoubleSpinBox_range_x.setValue(0.780)
            self.QDoubleSpinBox_range_y.setValue(0.780)
            self.QDoubleSpinBox_range_z.setValue(0.000)
            self.QDoubleSpinBox_ttl_start_on_405.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_on_405.setValue(0.012)
            self.QDoubleSpinBox_ttl_start_off_488_0.setValue(0.016)
            self.QDoubleSpinBox_ttl_stop_off_488_0.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_off_488_1.setValue(0.016)
            self.QDoubleSpinBox_ttl_stop_off_488_1.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_read_488_2.setValue(0.040)
            self.QDoubleSpinBox_ttl_stop_read_488_2.setValue(0.064)
            self.QDoubleSpinBox_ttl_start_emccd.setValue(0.040)
            self.QDoubleSpinBox_ttl_stop_emccd.setValue(0.064)
            self.QDoubleSpinBox_ttl_start_scmos.setValue(0.040)
            self.QDoubleSpinBox_ttl_stop_scmos.setValue(0.064)
            self.QDoubleSpinBox_ttl_start_tis.setValue(0.040)
            self.QDoubleSpinBox_ttl_stop_tis.setValue(0.064)
        if text == "Dot Scan 3D":
            self.QDoubleSpinBox_step_x.setValue(0.030)
            self.QDoubleSpinBox_step_y.setValue(0.030)
            self.QDoubleSpinBox_step_z.setValue(0.160)
            self.QDoubleSpinBox_range_x.setValue(0.780)
            self.QDoubleSpinBox_range_y.setValue(0.780)
            self.QDoubleSpinBox_range_z.setValue(3.200)
            self.QDoubleSpinBox_ttl_start_on_405.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_on_405.setValue(0.012)
            self.QDoubleSpinBox_ttl_start_off_488_0.setValue(0.016)
            self.QDoubleSpinBox_ttl_stop_off_488_0.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_off_488_1.setValue(0.016)
            self.QDoubleSpinBox_ttl_stop_off_488_1.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_read_488_2.setValue(0.040)
            self.QDoubleSpinBox_ttl_stop_read_488_2.setValue(0.064)
            self.QDoubleSpinBox_ttl_start_emccd.setValue(0.040)
            self.QDoubleSpinBox_ttl_stop_emccd.setValue(0.064)
            self.QDoubleSpinBox_ttl_start_scmos.setValue(0.040)
            self.QDoubleSpinBox_ttl_stop_scmos.setValue(0.064)
            self.QDoubleSpinBox_ttl_start_tis.setValue(0.040)
            self.QDoubleSpinBox_ttl_stop_tis.setValue(0.064)
        if text == "Monalisa Scan 2D":
            self.QDoubleSpinBox_step_x.setValue(0.030)
            self.QDoubleSpinBox_step_y.setValue(0.030)
            self.QDoubleSpinBox_step_z.setValue(0.160)
            self.QDoubleSpinBox_range_x.setValue(0.780)
            self.QDoubleSpinBox_range_y.setValue(0.780)
            self.QDoubleSpinBox_range_z.setValue(0.000)
            self.QDoubleSpinBox_ttl_start_on_405.setValue(0.008)
            self.QDoubleSpinBox_ttl_stop_on_405.setValue(0.012)
            self.QDoubleSpinBox_ttl_start_off_488_0.setValue(0.016)
            self.QDoubleSpinBox_ttl_stop_off_488_0.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_off_488_1.setValue(0.016)
            self.QDoubleSpinBox_ttl_stop_off_488_1.setValue(0.032)
            self.QDoubleSpinBox_ttl_start_read_488_2.setValue(0.040)
            self.QDoubleSpinBox_ttl_stop_read_488_2.setValue(0.064)
            self.QDoubleSpinBox_ttl_start_emccd.setValue(0.040)
            self.QDoubleSpinBox_ttl_stop_emccd.setValue(0.064)
            self.QDoubleSpinBox_ttl_start_scmos.setValue(0.040)
            self.QDoubleSpinBox_ttl_stop_scmos.setValue(0.064)
            self.QDoubleSpinBox_ttl_start_tis.setValue(0.040)
            self.QDoubleSpinBox_ttl_stop_tis.setValue(0.064)

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
