import os
import time
import traceback
import uuid

import numpy as np
import pandas as pd
import tifffile as tf
from PyQt5 import QtCore

from miao.controllers import controller_ao, controller_con, controller_view
from miao.tools import tool_improc as ipr
from miao.tools import tool_zernike as tz


class MainController(QtCore.QObject):
    sada = QtCore.pyqtSignal(str, np.ndarray, list, list)
    sazf = QtCore.pyqtSignal(list, np.ndarray)
    sig_plt = QtCore.pyqtSignal(list, list)

    def __init__(self, view, module, process, config, logg, path, parent=None):
        super().__init__(parent)

        self.v = view
        self.m = module
        self.p = process
        self.config = config
        self.logg = logg.error_log
        self.data_folder = path
        self.view_controller = controller_view.ViewController(self.v.view_view)
        self.con_controller = controller_con.ConController(self.v.con_view)
        self.ao_controller = controller_ao.AOController(self.v.ao_view)
        self._setup_threads()
        self._set_signal_connections()
        self._initial_setup()
        self.lasers = []
        self.cameras = {"imaging": 0, "wfs": 1, "focus_lock": 3}
        # dedicated thread pool for tasks
        self.task_worker = None
        self.task_thread = QtCore.QThread()

    def _setup_threads(self):
        # video thread
        self.videoWorker = LoopWorker(dt=100)
        self.videoWorker.signal_loop.connect(self.imshow_main)
        self.thread_video = QtCore.QThread()
        self.videoWorker.moveToThread(self.thread_video)
        self.thread_video.started.connect(self.videoWorker.start)
        self.thread_video.finished.connect(self.videoWorker.stop)
        # image process thread
        self.fftWorker = LoopWorker(dt=250)
        self.fftWorker.signal_loop.connect(self.imshow_fft)
        self.thread_fft = QtCore.QThread()
        self.fftWorker.moveToThread(self.thread_fft)
        self.thread_fft.started.connect(self.fftWorker.start)
        self.thread_fft.finished.connect(self.fftWorker.stop)
        # focus lock thread
        self.flocWorker = LoopWorker(dt=2000)
        self.flocWorker.signal_loop.connect(self.focus_locking)
        self.thread_floc = QtCore.QThread()
        self.flocWorker.moveToThread(self.thread_floc)
        self.thread_floc.started.connect(self.flocWorker.start)
        self.thread_floc.finished.connect(self.flocWorker.stop)
        # plot thread
        self.plotWorker = LoopWorker(dt=250)
        self.plotWorker.signal_loop.connect(self.profile_plot)
        self.thread_plot = QtCore.QThread()
        self.plotWorker.moveToThread(self.thread_plot)
        self.thread_plot.started.connect(self.plotWorker.start)
        self.thread_plot.finished.connect(self.plotWorker.stop)
        # wavefront sensor thread
        self.wfsWorker = LoopWorker(dt=125)
        self.wfsWorker.signal_loop.connect(self.imshow_img_wfs)
        self.thread_wfs = QtCore.QThread()
        self.wfsWorker.moveToThread(self.thread_wfs)
        self.thread_wfs.started.connect(self.wfsWorker.start)
        self.thread_wfs.finished.connect(self.wfsWorker.stop)

    def _set_signal_connections(self):
        self.v.Signal_interrupt.connect(self.interrupt_thread)
        self.sada.connect(self.save_data)
        self.sazf.connect(self.save_zernike_coeffs)
        self.sig_plt.connect(self.plot_)
        # MCL Piezo
        self.v.con_view.Signal_piezo_move_usb.connect(self.set_piezo_positions_usb)
        self.v.con_view.Signal_piezo_move.connect(self.set_piezo_positions)
        self.v.con_view.Signal_focus_finding.connect(self.run_focus_finding)
        self.v.con_view.Signal_focus_locking.connect(self.run_focus_locking)
        # MCL Mad Deck
        self.v.con_view.Signal_deck_read_position.connect(self.deck_read_position)
        self.v.con_view.Signal_deck_zero_position.connect(self.deck_zero_position)
        self.v.con_view.Signal_deck_move_single_step.connect(self.move_deck_single_step)
        self.v.con_view.Signal_deck_move_continuous.connect(self.move_deck_continuous)
        # Galvo Scanners
        self.v.con_view.Signal_galvo_set.connect(self.set_galvo)
        self.v.con_view.Signal_galvo_scan_update.connect(self.update_galvo_scanner)
        self.v.con_view.Signal_galvo_path_switch.connect(self.set_switch)
        # Cobolt Lasers
        self.v.con_view.Signal_set_laser.connect(self.set_laser)
        # Main Image Control
        self.v.con_view.Signal_check_emccd_temperature.connect(self.check_emdccd_temperature)
        self.v.con_view.Signal_switch_emccd_cooler.connect(self.switch_emdccd_cooler)
        self.v.con_view.Signal_plot_trigger.connect(self.plot_trigger)
        self.v.con_view.Signal_video.connect(self.video)
        self.v.con_view.Signal_fft.connect(self.fft)
        self.v.con_view.Signal_plot_profile.connect(self.plot_live)
        self.v.con_view.Signal_add_profile.connect(self.plot_add)
        self.v.con_view.Signal_set_mask.connect(self.set_array_mask)
        # NIDAQ
        self.v.con_view.Signal_daq_update.connect(self.update_daq_sample_rate)
        self.v.con_view.Signal_daq_reset.connect(self.reset_daq_channels)
        # Main Data Recording
        self.v.con_view.Signal_focal_array_scan.connect(self.run_focal_array_scan)
        self.v.con_view.Signal_grid_pattern_scan.connect(self.run_grid_pattern_scan)
        self.v.con_view.Signal_alignment.connect(self.run_pattern_alignment)
        self.v.con_view.Signal_data_acquire.connect(self.data_acquisition)
        # DM
        self.v.ao_view.Signal_dm_selection.connect(self.select_dm)
        self.v.ao_view.Signal_push_actuator.connect(self.push_actuator)
        self.v.ao_view.Signal_set_zernike.connect(self.set_zernike)
        self.v.ao_view.Signal_set_dm.connect(self.set_dm)
        self.v.ao_view.Signal_load_dm.connect(self.load_dm)
        self.v.ao_view.Signal_update_cmd.connect(self.update_dm)
        self.v.ao_view.Signal_save_dm.connect(self.save_dm)
        self.v.ao_view.Signal_set_dm_flat.connect(self.set_dm_flat)
        self.v.ao_view.Signal_influence_function.connect(self.run_influence_function)
        # WFS
        self.v.ao_view.Signal_img_shwfs_base.connect(self.set_reference_wf)
        self.v.ao_view.Signal_img_wfs.connect(self.img_wfs)
        self.v.ao_view.Signal_img_shwfr_run.connect(self.run_img_wfr)
        self.v.ao_view.Signal_img_shwfs_compute_wf.connect(self.run_compute_img_wf)
        self.v.ao_view.Signal_img_shwfs_save_wf.connect(self.save_img_wf)
        self.v.ao_view.Signal_img_shwfs_acquisition.connect(self.run_shwfs_acquisition)
        # AO
        self.v.ao_view.Signal_img_shwfs_correct_wf.connect(self.run_close_loop_correction)
        self.v.ao_view.Signal_sensorlessAO_run.connect(self.run_sensorless_iteration)
        self.v.ao_view.Signal_sensorlessAO_auto.connect(self.run_auto_sensorless)
        self.v.ao_view.Signal_sensorlessAO_metric_acquisition.connect(self.run_sensorless_metric_acquisition)
        self.v.ao_view.Signal_sensorlessAO_ml_acquisition.connect(self.run_sensorless_ml_acquisition)

    def _initial_setup(self):
        try:

            self.loop_flag = True

            p = self.m.md.get_position_steps_taken(3)
            self.con_controller.display_deck_position(p)

            self.reset_piezo_positions()
            self.reset_galvo_positions()
            self.update_galvo_scanner()

            self.laser_lists = ["405", "488_0", "488_1", "488_2"]

            self.pixel_sizes = [0., 0., 0., 0.]
            self.pixel_sizes[0] = 0.068783

            self.dm_cmd_ind = {}
            for key in self.m.dm.keys():
                self.v.ao_view.QComboBox_dms.addItem(key)
                self.dm_cmd_ind[key] = self.m.dm[key].current_cmd
            self.dfm = self.m.dm[self.v.ao_view.QComboBox_dms.currentText()]
            self.logg.info("Finish setting up controllers")
        except Exception as e:
            self.logg.error(f"Initial setup Error: {e}")

    def run_task(self, task, iteration=1, parent=None, callback=None):
        if self.task_worker is not None:
            self.task_worker = None
        self.task_thread = QtCore.QThread()
        self.task_worker = TaskWorker(task=task, n=iteration, parent=parent)
        self.task_worker.moveToThread(self.task_thread)
        self.task_thread.started.connect(self.task_worker.run)
        self.task_worker.signals.finished.connect(self.task_finish)
        if callback is not None:
            self.task_worker.signals.finished.connect(callback)
        self.task_thread.start()

    def task_finish(self):
        self.task_thread.quit()
        self.task_thread.wait()
        self.v.dialog.close()

    @QtCore.pyqtSlot()
    def interrupt_thread(self):
        self.loop_flag = False

    @QtCore.pyqtSlot()
    def deck_read_position(self):
        self.con_controller.display_deck_position(self.m.md.position)

    @QtCore.pyqtSlot()
    def deck_zero_position(self):
        self.m.md.position = 0
        self.con_controller.display_deck_position(self.m.md.position)

    @QtCore.pyqtSlot(bool)
    def move_deck_single_step(self, direction: bool):
        if direction:
            self.move_deck_up()
        else:
            self.move_deck_down()

    def move_deck_up(self):
        try:
            _moving = self.m.md.is_moving()
            if _moving:
                self.logg.info("MadDeck is moving")
            else:
                self.m.md.move_relative(3, 0.000762, velocity=0.8)
                self.con_controller.display_deck_position(self.m.md.position)
        except Exception as e:
            self.logg.error(f"MadDeck Error: {e}")

    def move_deck_down(self):
        try:
            _moving = self.m.md.is_moving()
            if _moving:
                self.logg.info("MadDeck is moving")
            else:
                self.m.md.move_relative(3, -0.000762, velocity=0.8)
                self.con_controller.display_deck_position(self.m.md.position)
        except Exception as e:
            self.logg.error(f"MadDeck Error: {e}")

    @QtCore.pyqtSlot(bool, int, float)
    def move_deck_continuous(self, moving: bool, direction: int, velocity: float):
        if moving:
            self.m.md.move_deck(direction, velocity)
        else:
            self.m.md.stop_deck()

    def reset_piezo_positions(self):
        pos_x, pos_y, pos_z = self.con_controller.get_piezo_positions()
        self.set_piezo_position_x(pos_x[0], port="software")
        self.set_piezo_position_y(pos_y[0], port="software")
        self.set_piezo_position_z(pos_z[0], port="software")
        self.set_piezo_position_x(pos_x[1], port="analog")
        self.set_piezo_position_y(pos_y[1], port="analog")
        self.set_piezo_position_z(pos_z[1], port="analog")
        self.con_controller.display_piezo_position_x(self.m.pz.read_position(0))
        self.con_controller.display_piezo_position_y(self.m.pz.read_position(1))
        self.con_controller.display_piezo_position_z(self.m.pz.read_position(2))

    @QtCore.pyqtSlot(str, float, float, float)
    def set_piezo_positions_usb(self, axis: str, value_x: float, value_y: float, value_z: float):
        if axis == "x":
            self.set_piezo_position_x(value_x, port="software")
        if axis == "y":
            self.set_piezo_position_y(value_y, port="software")
        if axis == "z":
            self.set_piezo_position_z(value_z, port="software")

    @QtCore.pyqtSlot(str, float, float, float)
    def set_piezo_positions(self, axis: str, value_x: float, value_y: float, value_z: float):
        if axis == "x":
            self.set_piezo_position_x(value_x, port="analog")
        if axis == "y":
            self.set_piezo_position_y(value_y, port="analog")
        if axis == "z":
            self.set_piezo_position_z(value_z, port="analog")

    def set_piezo_position_x(self, pos_x, port="analog"):
        try:
            if port == "software":
                self.m.pz.move_position(0, pos_x)
                time.sleep(0.1)
                self.con_controller.display_piezo_position_x(self.m.pz.read_position(0))
            else:
                self.m.daq.set_piezo_position([pos_x / 10.], [0])
                time.sleep(0.1)
                self.con_controller.display_piezo_position_x(self.m.pz.read_position(0))
        except Exception as e:
            self.logg.error(f"MCL Piezo Error: {e}")

    def set_piezo_position_y(self, pos_y, port="analog"):
        try:
            if port == "software":
                self.m.pz.move_position(1, pos_y)
                time.sleep(0.1)
                self.con_controller.display_piezo_position_y(self.m.pz.read_position(1))
            else:
                self.m.daq.set_piezo_position([pos_y / 10.], [1])
                time.sleep(0.1)
                self.con_controller.display_piezo_position_y(self.m.pz.read_position(1))
        except Exception as e:
            self.logg.error(f"MCL Piezo Error: {e}")

    def set_piezo_position_z(self, pos_z, port="analog"):
        try:
            if port == "software":
                self.m.pz.move_position(2, pos_z)
                time.sleep(0.1)
                self.con_controller.display_piezo_position_z(self.m.pz.read_position(2))
            else:
                self.m.daq.set_piezo_position([pos_z / 10.], [2])
                time.sleep(0.1)
                self.con_controller.display_piezo_position_z(self.m.pz.read_position(2))
        except Exception as e:
            self.logg.error(f"MCL Piezo Error: {e}")

    def reset_galvo_positions(self):
        g_x, g_y = self.con_controller.get_galvo_positions()
        try:
            self.m.daq.set_galvo_position([g_x, g_y], [0, 1])
            self.m.daq.set_switch_position(0.)
        except Exception as e:
            self.logg.error(f"Galvo Error: {e}")

    @QtCore.pyqtSlot(float, float)
    def set_galvo(self, voltx: float, volty: float):
        try:
            self.m.daq.set_galvo_position([voltx, volty], [0, 1])
        except Exception as e:
            self.logg.error(f"Galvo Error: {e}")

    @QtCore.pyqtSlot(float)
    def set_switch(self, volt: float):
        try:
            self.m.daq.set_switch_position(volt)
        except Exception as e:
            self.logg.error(f"Galvo Error: {e}")

    @QtCore.pyqtSlot(list, bool, float)
    def set_laser(self, laser: list, sw: bool, pw: float):
        if sw:
            try:
                self.m.laser.set_constant_power(laser, [pw])
                self.m.laser.laser_on(laser)
            except Exception as e:
                self.logg.error(f"Cobolt Laser Error: {e}")
        else:
            try:
                self.m.laser.laser_off(laser)
            except Exception as e:
                self.logg.error(f"Cobolt Laser Error: {e}")

    def set_lasers(self, lasers):
        pws = self.con_controller.get_cobolt_laser_power("all")
        ln = []
        pw = []
        for ls in lasers:
            ln.append(self.laser_lists[ls])
            pw.append(pws[ls])
        try:
            self.m.laser.set_modulation_mode(ln, pw)
            self.m.laser.laser_on(ln)
        except Exception as e:
            self.logg.error(f"Cobolt Laser Error: {e}")

    def lasers_off(self):
        try:
            self.m.laser.laser_off("all")
        except Exception as e:
            self.logg.error(f"Cobolt Laser Error: {e}")

    @QtCore.pyqtSlot()
    def check_emdccd_temperature(self):
        try:
            self.m.ccdcam.get_ccd_temperature()
            self.con_controller.display_camera_temperature(self.m.ccdcam.temperature)
        except Exception as e:
            self.logg.error(f"CCD Camera Error: {e}")

    @QtCore.pyqtSlot(bool)
    def switch_emdccd_cooler(self, sw: bool):
        if sw:
            self.switch_emdccd_cooler_on()
        else:
            self.switch_emdccd_cooler_off()

    def switch_emdccd_cooler_on(self):
        try:
            self.m.ccdcam.cooler_on()
        except Exception as e:
            self.logg.error(f"CCD Camera Error: {e}")

    def switch_emdccd_cooler_off(self):
        try:
            self.m.ccdcam.cooler_off()
        except Exception as e:
            self.logg.error(f"CCD Camera Error: {e}")

    def set_camera_roi(self, key="imaging"):
        try:
            if self.cameras[key] == 0:
                x, y, nx, ny, bx, by = self.con_controller.get_emccd_roi()
                self.m.cam_set[0].bin_h, self.m.cam_set[0].bin_v = bx, by
                self.m.cam_set[0].start_h, self.m.cam_set[0].end_h = x, x + nx - 1
                self.m.cam_set[0].start_v, self.m.cam_set[0].end_v = y, y + ny - 1
                self.m.cam_set[0].gain = self.con_controller.get_emccd_gain()
                self.m.cam_set[0].t_exposure = self.con_controller.get_emccd_expo()
            if self.cameras[key] == 1:
                x, y, nx, ny, bx, by = self.con_controller.get_scmos_roi()
                self.m.cam_set[1].set_roi(bx, by, x, nx, y, ny)
            if self.cameras[key] == 2:
                x, y, nx, ny, bx, by = self.con_controller.get_thorcam_roi()
                self.m.cam_set[2].set_roi(x, y, x + nx - 1, y + ny - 1)
            if self.cameras[key] == 3:
                expo = self.con_controller.get_tis_expo()
                self.m.cam_set[3].set_exposure(expo)
                x, y, nx, ny, bx, by = self.con_controller.get_tis_roi()
                self.m.cam_set[3].set_roi(x, y, nx, ny)
        except Exception as e:
            self.logg.error(f"Camera Error: {e}")

    @QtCore.pyqtSlot(int)
    def update_daq_sample_rate(self, sr: int):
        self.p.trigger.update_nidaq_parameters(sr * 1000)
        self.update_galvo_scanner()
        self.m.daq.sample_rate = sr * 1000

    @QtCore.pyqtSlot()
    def reset_daq_channels(self):
        self.m.daq.stop_triggers()

    @QtCore.pyqtSlot()
    def update_galvo_scanner(self):
        galvo_positions, galvo_ranges, dot_pos, offset, galvo_positions_act, galvo_ranges_act, dot_pos_act, offset_act, sws = self.con_controller.get_galvo_scan_parameters()
        self.p.trigger.update_galvo_scan_parameters(origins=galvo_positions, ranges=galvo_ranges,
                                                    foci=dot_pos, offsets=offset,
                                                    origins_act=galvo_positions_act, ranges_act=galvo_ranges_act,
                                                    foci_act=dot_pos_act, offsets_act=offset_act, sws=sws)
        self.con_controller.display_frequency(self.p.trigger.frequency, self.p.trigger.frequency_act)

    def update_trigger_parameters(self, cam_key):
        """Ensure that the camera acquisition is fully set up before executing this function."""
        try:
            digital_starts, digital_ends = self.con_controller.get_digital_parameters()
            self.p.trigger.update_digital_parameters(digital_starts, digital_ends)
            self.update_galvo_scanner()
            axis_lengths, step_sizes = self.con_controller.get_piezo_scan_parameters()
            pos_x, pos_y, pos_z = self.con_controller.get_piezo_positions()
            positions = [pos_x[1], pos_y[1], pos_z[1]]
            return_time = self.con_controller.get_piezo_return_time()
            self.p.trigger.update_piezo_scan_parameters(axis_lengths, step_sizes, positions, return_time)
            self.p.trigger.update_camera_parameters(initial_time=self.m.cam_set[self.cameras[cam_key]].t_clean,
                                                    standby_time=self.m.cam_set[self.cameras[cam_key]].t_readout,
                                                    cycle_time=self.m.cam_set[self.cameras[cam_key]].t_kinetic)
            if self.cameras[cam_key] == 0:
                self.con_controller.display_camera_timings(standby=self.m.cam_set[self.cameras[cam_key]].t_kinetic)
            self.logg.info(f"Trigger Updated")
        except Exception as e:
            self.logg.error(f"Trigger Error: {e}")

    def generate_live_triggers(self, cam_key):
        self.update_trigger_parameters(cam_key)
        return self.p.trigger.generate_digital_triggers(self.lasers, self.cameras[cam_key])

    def prepare_video(self, vd_mod):
        self.lasers = self.con_controller.get_lasers()
        self.set_lasers(self.lasers)
        self.cameras["imaging"] = self.con_controller.get_imaging_camera()
        self.set_camera_roi("imaging")
        if self.cameras["imaging"] == 0:
            self.m.cam_set[self.cameras["imaging"]].prepare_live()
            self.update_trigger_parameters("imaging")
        if self.cameras["imaging"] == 1:
            self.m.cam_set[self.cameras["imaging"]].mode = self.con_controller.get_scmos_mode()
            if self.m.cam_set[self.cameras["imaging"]].mode == "LightSheet":
                self.update_trigger_parameters("imaging")
                _, _, interval_lines = self.con_controller.get_scmos_expo()
                line_exposure, line_interval = self.p.trigger.update_lightsheet_rolling(interval_lines)
                self.m.cam_set[self.cameras["imaging"]].line_exposure = line_exposure
                self.m.cam_set[self.cameras["imaging"]].line_interval = line_interval
                self.con_controller.display_cmos_rolling_timings(line_exposure, line_interval)
                self.m.cam_set[self.cameras["imaging"]].prepare_live()
            if self.m.cam_set[self.cameras["imaging"]].mode == "Normal":
                self.m.cam_set[self.cameras["imaging"]].prepare_live()
                self.update_trigger_parameters("imaging")
        if vd_mod == "Wide Field":
            self.set_switch(self.p.trigger.galvo_sw_states[self.cameras["imaging"]])
            dtr, sw, chs = self.p.trigger.generate_digital_triggers(self.lasers, self.cameras["imaging"])
            self.m.daq.write_triggers(digital_sequences=dtr, digital_channels=chs, finite=False)
            self.con_controller.display_camera_timings(exposure=self.p.trigger.exposure_time,
                                                       clean=self.p.trigger.initial_time,
                                                       standby=self.p.trigger.standby_time)
        if vd_mod == "Dot Scan":
            if self.cameras["imaging"] == 1:
                if self.m.cam_set[self.cameras["imaging"]].mode == "LightSheet":
                    self.set_switch(self.p.trigger.galvo_sw_states[self.cameras["imaging"]])
                    dtr, gtr, chs = self.p.trigger.generate_digital_scanning_triggers_rolling(self.lasers,
                                                                                              self.cameras["imaging"])
                    self.m.daq.write_triggers(galvo_sequences=gtr, galvo_channels=[0, 1],
                                              digital_sequences=dtr, digital_channels=chs, finite=False)
                else:
                    dtr, gtr, chs = self.p.trigger.generate_digital_scanning_triggers(self.lasers,
                                                                                      self.cameras["imaging"])
                    self.m.daq.write_triggers(galvo_sequences=gtr, galvo_channels=[0, 1, 2],
                                              digital_sequences=dtr, digital_channels=chs, finite=False)
            else:
                dtr, gtr, chs = self.p.trigger.generate_digital_scanning_triggers(self.lasers, self.cameras["imaging"])
                self.m.daq.write_triggers(galvo_sequences=gtr, galvo_channels=[0, 1, 2],
                                          digital_sequences=dtr, digital_channels=chs, finite=False)
                self.con_controller.display_camera_timings(exposure=self.p.trigger.exposure_time,
                                                           clean=self.p.trigger.initial_time,
                                                           standby=self.p.trigger.standby_time)
        if vd_mod == "Scan Calib":
            self.set_switch(self.p.trigger.galvo_sw_states[self.cameras["imaging"]])
            dtr, sw, ptr, dch, pch = self.p.trigger.generate_piezo_line_scan(self.lasers, self.cameras["imaging"])
            self.m.daq.write_triggers(piezo_sequences=ptr, piezo_channels=pch,
                                      digital_sequences=dtr, digital_channels=dch, finite=False)
        if vd_mod == "Focus Lock":
            self.logg.info(f"Focus Lock live")

    def start_video(self, vm):
        try:
            self.prepare_video(vm)
        except Exception as e:
            self.logg.error(f"Error preparing imaging video: {e}")
            self.m.daq.stop_triggers()
            self.lasers_off()
            return
        try:
            self.m.cam_set[self.cameras["imaging"]].start_live()
            if self.cameras["imaging"] != self.cameras["focus_lock"]:
                self.m.daq.run_triggers()
            self.thread_video.start()
        except Exception as e:
            self.logg.error(f"Error starting imaging video: {e}")
            self.stop_video(vm)
            return

    def stop_video(self, vm):
        try:
            if self.thread_video.isRunning():
                self.thread_video.quit()
                self.thread_video.wait()
            self.m.daq.stop_triggers()
            self.m.cam_set[self.cameras["imaging"]].stop_live()
            self.lasers_off()
            if vm == "Dot Scan":
                self.reset_galvo_positions()
            elif vm == "Scan Calib":
                self.reset_piezo_positions()
        except Exception as e:
            self.logg.error(f"Error stopping imaging video: {e}")

    @QtCore.pyqtSlot(bool, str)
    def video(self, sw: bool, md: str):
        if sw:
            self.start_video(md)
        else:
            self.stop_video(md)

    @QtCore.pyqtSlot()
    def imshow_main(self):
        try:
            self.view_controller.plot_main(self.m.cam_set[self.cameras["imaging"]].get_last_image(),
                                           layer=self.cameras["imaging"])
        except Exception as e:
            self.logg.error(f"Error showing imaging video: {e}")

    @QtCore.pyqtSlot(bool)
    def fft(self, sw: bool):
        if sw:
            self.run_fft()
        else:
            self.stop_fft()

    def run_fft(self):
        try:
            self.thread_fft.start()
        except Exception as e:
            self.logg.error(f"Error starting fft: {e}")

    def stop_fft(self):
        try:
            if self.thread_fft.isRunning():
                self.thread_fft.quit()
                self.thread_fft.wait()
        except Exception as e:
            self.logg.error(f"Error stopping fft: {e}")

    @QtCore.pyqtSlot()
    def imshow_fft(self):
        try:
            self.view_controller.plot_fft(
                ipr.fourier_transform(self.view_controller.get_image_data(layer=self.cameras["imaging"])))
        except Exception as e:
            self.logg.error(f"Error showing fft: {e}")

    @QtCore.pyqtSlot(bool)
    def plot_live(self, sw: bool):
        if sw:
            self.start_plot_live()
        else:
            self.stop_plot_live()

    def start_plot_live(self):
        try:
            self.thread_plot.start()
        except Exception as e:
            self.logg.error(f"Error starting plot: {e}")

    def stop_plot_live(self):
        try:
            if self.thread_plot.isRunning():
                self.thread_plot.quit()
                self.thread_plot.wait()
        except Exception as e:
            self.logg.error(f"Error stopping plot: {e}")

    @QtCore.pyqtSlot()
    def profile_plot(self):
        try:
            ax = self.con_controller.get_profile_axis()
            self.view_controller.plot_update(
                ipr.get_profile(self.view_controller.get_image_data(layer=self.cameras["imaging"]), ax, norm=True))
        except Exception as e:
            self.logg.error(f"Error plotting profile: {e}")

    @QtCore.pyqtSlot()
    def plot_add(self):
        try:
            ax = self.con_controller.get_profile_axis()
            self.view_controller.plot(
                ipr.get_profile(self.view_controller.get_image_data(layer=self.cameras["imaging"]), ax, norm=True))
        except Exception as e:
            self.logg.error(f"Error plotting profile: {e}")

    @QtCore.pyqtSlot()
    def plot_trigger(self):
        try:
            dtr, sw, dch = self.generate_live_triggers("imaging")
            self.view_controller.plot_update(dtr[0])
            for i in range(dtr.shape[0] - 1):
                self.view_controller.plot(dtr[i + 1] + i + 1)
        except Exception as e:
            self.logg.error(f"Error plotting digital triggers: {e}")

    @QtCore.pyqtSlot(list, list)
    def plot_(self, x, d):
        try:
            self.view_controller.plot_update(data=d, x=x)
            self.v.refresh_gui()
        except Exception as e:
            self.logg.error(f"Error plotting profile: {e}")

    @QtCore.pyqtSlot(str, int)
    def data_acquisition(self, acq_mod: str, acq_num: int):
        if acq_mod == "Wide Field 2D":
            self.run_widefield_zstack(acq_num)
        elif acq_mod == "Wide Field 3D":
            self.run_widefield_zstack(acq_num)
        elif acq_mod == "Monalisa Scan 2D":
            self.run_monalisa_scan(acq_num)
        elif acq_mod == "Dot Scan 2D":
            self.run_dot_scan(acq_num)
        elif acq_mod == "Point Scan 2D":
            self.run_point_scan(acq_num)
        else:
            self.logg.error(f"Invalid video mode")

    @QtCore.pyqtSlot(str, np.ndarray, list, list)
    def save_data(self, tm: str, d: np.ndarray, idx: list, pos: list):
        fn = self.v.get_file_dialog()
        if fn is not None:
            fd = os.path.join(self.data_folder, tm + '_' + fn)
        else:
            fd = os.path.join(self.data_folder, tm)
        pixel_size = self.pixel_sizes[self.cameras["imaging"]]
        tf.imwrite(str(fd + r".tif"), data=d, metadata={"pixel_size": (pixel_size, pixel_size)})
        with pd.ExcelWriter(str(fd + r"_metadata.xlsx"), engine="openpyxl") as writer:
            if idx is not None:
                df_idx = pd.DataFrame(idx, columns=["acquisition_sequence"])
                df_idx.to_excel(writer, sheet_name="acquisition_sequence", index=False)
            if pos is not None:
                for i, arr in enumerate(pos):
                    df_pos = pd.DataFrame(arr, columns=[f"axis_{i}"])
                    df_pos.to_excel(writer, sheet_name=f"axis_{i}", index=False)

    def prepare_focus_finding(self):
        self.lasers = self.con_controller.get_lasers()
        self.set_lasers(self.lasers)
        self.cameras["imaging"] = self.con_controller.get_imaging_camera()
        self.set_camera_roi("imaging")
        self.m.cam_set[self.cameras["imaging"]].prepare_live()
        dtr, sw, dch = self.generate_live_triggers("imaging")
        self.set_switch(self.p.trigger.galvo_sw_states[self.cameras["imaging"]])
        self.m.daq.write_triggers(digital_sequences=dtr, digital_channels=dch)
        self.con_controller.display_camera_timings(exposure=self.p.trigger.exposure_time,
                                                   clean=self.p.trigger.initial_time,
                                                   standby=self.p.trigger.standby_time)
        self.m.cam_set[self.cameras["focus_lock"]].set_exposure(self.con_controller.get_tis_expo())
        self.m.cam_set[self.cameras["focus_lock"]].prepare_live()

    def focus_finding(self):
        try:
            self.prepare_focus_finding()
        except Exception as e:
            self.logg.error(f"Error starting focus finding: {e}")
            return
        try:
            pos_x, pos_y, pos_z = self.con_controller.get_piezo_positions()
            center_pos, axis_length, step_size = pos_z[0], 0.8, 0.08
            start = center_pos - axis_length
            end = center_pos + axis_length
            zps = np.arange(start, end + step_size, step_size)
            data = []
            data_calib = []
            pzs = []
            self.m.cam_set[self.cameras["imaging"]].start_live()
            self.m.cam_set[self.cameras["focus_lock"]].start_live()
            for i, z in enumerate(zps):
                self.set_piezo_position_z(z, port="software")
                time.sleep(0.1)
                self.m.daq.run_triggers()
                time.sleep(0.04)
                temp = self.m.cam_set[self.cameras["imaging"]].get_last_image()
                data.append(temp)
                self.m.daq.stop_triggers(_close=False)
                data_calib.append(self.m.cam_set[self.cameras["focus_lock"]].get_last_image())
                pzs.append(ipr.calculate_focus_measure_with_sobel(temp - temp.min()))
            fd = os.path.join(self.data_folder, time.strftime("%Y%m%d%H%M%S") + '_widefield_zstack.tif')
            tf.imwrite(fd, np.asarray(data), imagej=True, resolution=(
                1 / self.pixel_sizes[self.cameras["imaging"]], 1 / self.pixel_sizes[self.cameras["imaging"]]),
                       metadata={'unit': 'um',
                                 'indices': list(self.m.cam_set[self.cameras["imaging"]].data.ind_list)})
            self.view_controller.plot_update(pzs, x=zps)
            fp = ipr.peak_find(zps, pzs)
            self.v.con_view.QDoubleSpinBox_stage_z_usb.setValue(fp)
            time.sleep(0.06)
            data_calib.append(self.m.cam_set[self.cameras["focus_lock"]].get_last_image())
            fd = os.path.join(self.data_folder, time.strftime("%Y%m%d%H%M%S") + '_focus_calibration_stack.tif')
            tf.imwrite(fd, np.asarray(data_calib), imagej=True, resolution=(
                1 / self.pixel_sizes[self.cameras["focus_lock"]], 1 / self.pixel_sizes[self.cameras["focus_lock"]]),
                       metadata={'unit': 'um'})
            self.p.foc_ctrl.calibrate(np.append(zps, fp), np.asarray(data_calib))
        except Exception as e:
            self.finish_focus_finding()
            self.logg.error(f"Error running focus finding: {e}")
            return
        self.finish_focus_finding()

    def finish_focus_finding(self):
        try:
            self.m.cam_set[self.cameras["imaging"]].stop_live()
            self.m.cam_set[self.cameras["focus_lock"]].stop_live()
            self.lasers_off()
            self.m.daq.stop_triggers()
            self.reset_piezo_positions()
            self.logg.info("Focus finding stack acquired")
        except Exception as e:
            self.logg.error(f"Error stopping focus finding: {e}")

    @QtCore.pyqtSlot()
    def run_focus_finding(self):
        self.v.get_dialog()
        self.run_task(task=self.focus_finding)

    def prepare_focus_locking(self):
        p = self.con_controller.get_pid_parameters()
        self.p.foc_ctrl.update_pid(p)
        z = self.v.con_view.QDoubleSpinBox_stage_z_usb.value()
        self.p.foc_ctrl.initiate(z)
        self.m.cam_set[self.cameras["focus_lock"]].set_exposure(self.con_controller.get_tis_expo())
        self.m.cam_set[self.cameras["focus_lock"]].prepare_live()
        self.m.cam_set[self.cameras["focus_lock"]].start_live()
        time.sleep(0.1)
        self.p.foc_ctrl.set_focus(self.m.cam_set[self.cameras["focus_lock"]].get_last_image())
        self.m.cam_set[self.cameras["focus_lock"]].stop_live()

    def lock_focus(self):
        try:
            self.prepare_focus_locking()
        except Exception as e:
            self.logg.error(f"Error preparing focus locking: {e}")
            self.release_focus()
            return
        try:
            self.m.cam_set[self.cameras["focus_lock"]].start_live()
            self.thread_floc.start()
        except Exception as e:
            self.logg.error(f"Error starting focus locking: {e}")
            self.release_focus()
            return

    def release_focus(self):
        try:
            if self.thread_floc.isRunning():
                self.thread_floc.quit()
                self.thread_floc.wait()
            self.m.cam_set[self.cameras["focus_lock"]].stop_live()
        except Exception as e:
            self.logg.error(f"Error stopping imaging video: {e}")

    def focus_locking(self):
        self.p.foc_ctrl.update(self.m.cam_set[self.cameras["focus_lock"]].get_last_image())
        self.v.con_view.QDoubleSpinBox_stage_z_usb.setValue(self.p.foc_ctrl.ctd.data_list[-1])
        self.view_controller.plot_update(self.p.foc_ctrl.ctd.data_list, s=self.p.foc_ctrl.pid.set_point)

    @QtCore.pyqtSlot(bool)
    def run_focus_locking(self, sw: bool):
        if sw:
            self.lock_focus()
        else:
            self.release_focus()

    def prepare_widefield_zstack(self):
        self.lasers = self.con_controller.get_lasers()
        self.set_lasers(self.lasers)
        self.cameras["imaging"] = self.con_controller.get_imaging_camera()
        self.set_camera_roi("imaging")
        self.m.cam_set[self.cameras["imaging"]].prepare_data_acquisition()
        self.update_trigger_parameters("imaging")
        self.set_switch(self.p.trigger.galvo_sw_states[self.cameras["imaging"]])
        dtr, sw, ptr, dch, pch, pos = self.p.trigger.generate_piezo_scan(self.lasers, self.cameras["imaging"])
        self.m.daq.set_piezo_position(pos=[ptr[0]], indices=[2])
        self.m.cam_set[self.cameras["imaging"]].acq_num = pos
        self.m.daq.write_triggers(piezo_sequences=ptr, piezo_channels=pch, digital_sequences=dtr, digital_channels=dch,
                                  finite=True)
        self.con_controller.display_camera_timings(exposure=self.p.trigger.exposure_time,
                                                   clean=self.p.trigger.initial_time,
                                                   standby=self.p.trigger.standby_time)

    def widefield_zstack(self):
        try:
            self.prepare_widefield_zstack()
        except Exception as e:
            self.logg.error(f"Error preparing widefield zstack: {e}")
            return
        try:
            self.m.cam_set[self.cameras["imaging"]].start_data_acquisition()
            self.m.daq.run_triggers()
            time.sleep(0.2)
            self.sada.emit(time.strftime("%Y%m%d%H%M%S") + '_widefield_zstack',
                           self.m.cam_set[self.cameras["imaging"]].get_data(),
                           list(self.m.cam_set[self.cameras["imaging"]].data.ind_list),
                           self.p.trigger.piezo_scan_positions)
        except Exception as e:
            self.finish_widefield_zstack()
            self.logg.error(f"Error running widefield zstack: {e}")
            return
        self.finish_widefield_zstack()

    def finish_widefield_zstack(self):
        try:
            self.m.cam_set[self.cameras["imaging"]].stop_data_acquisition()
            self.lasers_off()
            self.m.daq.stop_triggers()
            self.reset_piezo_positions()
            self.logg.info("Widefield image stack acquired")
        except Exception as e:
            self.logg.error(f"Error stopping widefield zstack: {e}")

    def run_widefield_zstack(self, n: int):
        self.v.get_dialog()
        self.run_task(task=self.widefield_zstack, iteration=n)

    def prepare_monalisa_scan_2d(self):
        self.lasers = self.con_controller.get_lasers()
        self.set_lasers(self.lasers)
        self.cameras["imaging"] = self.con_controller.get_imaging_camera()
        self.set_camera_roi("imaging")
        self.m.cam_set[self.cameras["imaging"]].prepare_data_acquisition()
        self.update_trigger_parameters("imaging")
        dtr, sw, ptr, dch, pch, pos = self.p.trigger.generate_piezo_scan(self.lasers, self.cameras["imaging"])
        self.m.daq.set_piezo_position(pos=list(np.swapaxes(ptr, 0, 1)[0]), indices=pch)
        self.m.cam_set[self.cameras["imaging"]].acq_num = pos
        self.m.daq.write_triggers(piezo_sequences=ptr, piezo_channels=pch,
                                  digital_sequences=dtr, digital_channels=dch)
        self.con_controller.display_camera_timings(exposure=self.p.trigger.exposure_time,
                                                   clean=self.p.trigger.initial_time,
                                                   standby=self.p.trigger.standby_time)

    def monalisa_scan_2d(self):
        try:
            self.prepare_monalisa_scan_2d()
        except Exception as e:
            self.logg.error(f"Error preparing monalisa scanning: {e}")
            return
        try:
            self.m.cam_set[self.cameras["imaging"]].start_data_acquisition()
            time.sleep(0.02)
            self.m.daq.run_triggers()
            time.sleep(1.)
            self.sada.emit(time.strftime("%Y%m%d%H%M%S") + '_monalisa_scanning',
                           self.m.cam_set[self.cameras["imaging"]].get_data(),
                           list(self.m.cam_set[self.cameras["imaging"]].data.ind_list),
                           self.p.trigger.piezo_scan_positions)
        except Exception as e:
            self.finish_monalisa_scan()
            self.logg.error(f"Error running monalisa scanning: {e}")
            return
        self.finish_monalisa_scan()

    def finish_monalisa_scan(self):
        try:
            self.m.cam_set[self.cameras["imaging"]].stop_data_acquisition()
            self.m.daq.stop_triggers()
            self.lasers_off()
            self.reset_piezo_positions()
            self.logg.info("Monalisa scanning image acquired")
        except Exception as e:
            self.logg.error(f"Error stopping monalisa scanning: {e}")

    def run_monalisa_scan(self, n: int):
        self.v.get_dialog()
        self.run_task(task=self.monalisa_scan_2d, iteration=n)

    def prepare_point_scan(self):
        self.lasers = self.con_controller.get_lasers()
        self.set_lasers(self.lasers)
        self.cameras["imaging"] = self.con_controller.get_imaging_camera()
        self.set_camera_roi("imaging")
        self.m.cam_set[self.cameras["imaging"]].prepare_data_acquisition()
        self.update_trigger_parameters("imaging")
        ptr, sw, dtr, dch, pch, gch, pos = self.p.trigger.generate_piezo_point_scan_2d(self.lasers,
                                                                                       self.cameras["imaging"])
        self.m.cam_set[self.cameras["imaging"]].acq_num = pos
        self.m.daq.write_triggers(piezo_sequences=ptr, piezo_channels=pch,
                                  digital_sequences=dtr, digital_channels=dch)
        self.con_controller.display_camera_timings(exposure=self.p.trigger.exposure_time,
                                                   clean=self.p.trigger.initial_time,
                                                   standby=self.p.trigger.standby_time)

    def point_scan(self):
        try:
            self.prepare_point_scan()
        except Exception as e:
            self.logg.error(f"Error preparing point scanning: {e}")
            return
        try:
            self.m.cam_set[self.cameras["imaging"]].start_data_acquisition()
            time.sleep(0.02)
            self.m.daq.run_triggers()
            time.sleep(1.)
            fd = os.path.join(self.data_folder, time.strftime("%Y%m%d%H%M%S") + '_piezo_scanning.tif')
            tf.imwrite(fd, self.m.cam_set[self.cameras["imaging"]].get_data(), imagej=True, resolution=(
                1 / self.pixel_sizes[self.cameras["imaging"]], 1 / self.pixel_sizes[self.cameras["imaging"]]),
                       metadata={'unit': 'um', 'indices': list(self.m.cam_set[self.cameras["imaging"]].data.ind_list)})
        except Exception as e:
            self.finish_monalisa_scan()
            self.logg.error(f"Error running point scanning: {e}")
            return
        self.finish_monalisa_scan()

    def finish_point_scan(self):
        try:
            self.m.cam_set[self.cameras["imaging"]].stop_data_acquisition()
            self.m.daq.stop_triggers()
            self.lasers_off()
            self.reset_piezo_positions()
            self.logg.info("Point scanning image acquired")
        except Exception as e:
            self.logg.error(f"Error stopping point scanning: {e}")

    def run_point_scan(self, n: int):
        self.v.get_dialog()
        self.run_task(task=self.point_scan, iteration=n)

    def prepare_dot_scan(self):
        self.lasers = self.con_controller.get_lasers()
        self.set_lasers(self.lasers)
        self.cameras["imaging"] = self.con_controller.get_imaging_camera()
        self.set_camera_roi("imaging")
        self.m.cam_set[self.cameras["imaging"]].prepare_data_acquisition()
        self.update_trigger_parameters("imaging")
        gtr, ptr, dtr, chs, pos = self.p.trigger.generate_dotscan_resolft_2d(self.lasers, self.cameras["imaging"])
        self.m.cam_set[self.cameras["imaging"]].acq_num = pos
        self.m.daq.write_triggers(piezo_sequences=ptr, piezo_channels=[0, 1],
                                  galvo_sequences=gtr, galvo_channels=[0, 1, 2],
                                  digital_sequences=dtr, digital_channels=chs)
        self.con_controller.display_camera_timings(exposure=self.p.trigger.exposure_time,
                                                   clean=self.p.trigger.initial_time,
                                                   standby=self.p.trigger.standby_time)

    def dot_scan(self):
        try:
            self.prepare_dot_scan()
        except Exception as e:
            self.logg.error(f"Error preparing galvo scanning: {e}")
            return
        try:
            self.m.cam_set[self.cameras["imaging"]].start_data_acquisition()
            time.sleep(0.02)
            self.m.daq.run_triggers()
            time.sleep(1.)
            fd = os.path.join(self.data_folder, time.strftime("%Y%m%d%H%M%S") + '_dot_scanning.tif')
            for key in self.dm_cmd_ind.keys():
                self.dm_cmd_ind[key] = self.m.dm[key].current_cmd
            tf.imwrite(fd, self.m.cam_set[self.cameras["imaging"]].get_data(), imagej=True, resolution=(
                1 / self.pixel_sizes[self.cameras["imaging"]], 1 / self.pixel_sizes[self.cameras["imaging"]]),
                       metadata={'unit': 'um', 'indices': list(self.m.cam_set[self.cameras["imaging"]].data.ind_list),
                                 'DM cmd': self.dm_cmd_ind})
        except Exception as e:
            self.finish_dot_scan()
            self.logg.error(f"Error running dot scanning: {e}")
            return
        self.finish_dot_scan()

    def finish_dot_scan(self):
        try:
            self.m.cam_set[self.cameras["imaging"]].stop_data_acquisition()
            self.m.daq.stop_triggers()
            self.lasers_off()
            self.reset_piezo_positions()
            self.logg.info("Dot scanning image acquired")
        except Exception as e:
            self.logg.error(f"Error stopping dot scanning: {e}")

    def run_dot_scan(self, n: int):
        self.v.get_dialog()
        self.run_task(task=self.dot_scan, iteration=n)

    def pattern_alignment(self):
        ax = self.con_controller.get_profile_axis()

        try:
            # grid pattern
            self.lasers = [1]
            self.set_lasers(self.lasers)
            self.cameras["imaging"] = self.con_controller.get_imaging_camera()
            self.set_camera_roi("imaging")
            self.m.cam_set[self.cameras["imaging"]].prepare_live()
            self.update_trigger_parameters("imaging")
            self.set_switch(self.p.trigger.galvo_sw_states[self.cameras["imaging"]])
            dtr, sw, chs = self.p.trigger.generate_digital_triggers(self.lasers, self.cameras["imaging"])
            self.m.daq.write_triggers(digital_sequences=dtr, digital_channels=chs, finite=True)
            self.m.cam_set[self.cameras["imaging"]].start_live()
            time.sleep(0.1)
            data = []
            for i in range(10):
                self.m.daq.run_triggers()
                time.sleep(0.08)
                data.append(self.m.cam_set[self.cameras["imaging"]].get_last_image())
                self.m.daq.stop_triggers(_close=False)
            self.m.daq.stop_triggers()
            self.m.cam_set[self.cameras["imaging"]].stop_live()
            self.view_controller.plot_update(ipr.get_profile(np.average(np.asarray(data), axis=0), ax, norm=True))
            # dot array
            self.lasers = [3]
            self.set_lasers(self.lasers)
            self.cameras["imaging"] = self.con_controller.get_imaging_camera()
            self.set_camera_roi("imaging")
            self.m.cam_set[self.cameras["imaging"]].prepare_live()
            self.update_trigger_parameters("imaging")
            dtr, gtr, chs = self.p.trigger.generate_digital_scanning_triggers(self.lasers, self.cameras["imaging"])
            self.m.daq.write_triggers(galvo_sequences=gtr, galvo_channels=[0, 1, 2],
                                      digital_sequences=dtr, digital_channels=chs, finite=True)
            self.m.cam_set[self.cameras["imaging"]].start_live()
            time.sleep(0.1)
            data = []
            for i in range(10):
                self.m.daq.run_triggers()
                time.sleep(0.08)
                data.append(self.m.cam_set[self.cameras["imaging"]].get_last_image())
                self.m.daq.stop_triggers(_close=False)
            self.view_controller.plot(ipr.get_profile(np.average(np.asarray(data), axis=0), ax, norm=True))
        except Exception as e:
            self.finish_pattern_alignment()
            self.logg.error(f"Error running pattern alignment: {e}")
            return
        self.finish_pattern_alignment()

    def finish_pattern_alignment(self):
        try:
            self.m.cam_set[self.cameras["imaging"]].stop_live()
            self.m.daq.stop_triggers()
            self.lasers_off()
            self.logg.info("Pattern alignment finished")
        except Exception as e:
            self.logg.error(f"Error stopping pattern alignment: {e}")

    def run_pattern_alignment(self):
        self.v.get_dialog()
        self.run_task(task=self.pattern_alignment)

    def prepare_focal_array_scan(self):
        self.lasers = self.con_controller.get_lasers()
        self.set_lasers(self.lasers)
        self.cameras["imaging"] = self.con_controller.get_imaging_camera()
        self.set_camera_roi("imaging")
        self.m.cam_set[self.cameras["imaging"]].prepare_live()
        self.update_trigger_parameters("imaging")

    def focal_array_scan(self):
        try:
            self.prepare_focal_array_scan()
        except Exception as e:
            self.logg.error(f"Error preparing focal array scanning: {e}")
            return
        try:
            scan_x = self.p.trigger.galvo_origins[0] + np.linspace(-1.2 * self.p.trigger.dot_step_v,
                                                                   1.2 * self.p.trigger.dot_step_v, 10,
                                                                   endpoint=False, dtype=float)
            scan_y = self.p.trigger.galvo_origins[1] + np.linspace(-1.2 * self.p.trigger.dot_step_y,
                                                                   1.2 * self.p.trigger.dot_step_y, 10,
                                                                   endpoint=False, dtype=float)
            sx, sy = scan_x.shape[0], scan_y.shape[0]
            data = []
            mx = np.zeros((sy, sx))
            self.m.cam_set[self.cameras["imaging"]].start_live()
            time.sleep(0.2)
            for j in range(sy):
                for i in range(sx):
                    self.p.trigger.update_galvo_scan_parameters(origins=[scan_x[i], scan_y[j]])
                    dtr, gtr, chs = self.p.trigger.generate_digital_scanning_triggers(self.lasers,
                                                                                      self.cameras["imaging"])
                    self.m.daq.write_triggers(galvo_sequences=gtr, galvo_channels=[0, 1, 2],
                                              digital_sequences=dtr, digital_channels=chs)
                    self.m.daq.run_triggers()
                    time.sleep(0.2)
                    temp = self.m.cam_set[self.cameras["imaging"]].get_last_image()
                    self.m.daq.stop_triggers()
                    data.append(temp)
                    mx[j, i] = np.mean(temp)
            fd = os.path.join(self.data_folder, time.strftime("%Y%m%d%H%M%S") + '_focal_array_scan.tif')
            tf.imwrite(fd, np.asarray(data), imagej=True,
                       resolution=(1 / self.pixel_sizes[self.cameras["imaging"]],
                                   1 / self.pixel_sizes[self.cameras["imaging"]]),
                       metadata={'unit': 'um'})
            fd = os.path.join(self.data_folder, time.strftime("%Y%m%d%H%M%S") + '_focal_array_scan_recon.tif')
            tf.imwrite(fd, mx)
            self.v.view_view.plot_image(data=mx, axis_arrays=[scan_x, scan_y], axis_labels=None)
        except Exception as e:
            self.finish_focal_array_scan()
            self.logg.error(f"Error running focal array scanning: {e}")
            return
        self.finish_focal_array_scan()

    def finish_focal_array_scan(self):
        try:
            self.m.cam_set[self.cameras["imaging"]].stop_live()
            self.m.daq.stop_triggers()
            self.lasers_off()
            self.logg.info("Focal array scanning image acquired")
        except Exception as e:
            self.logg.error(f"Error stopping focal array scanning: {e}")

    def run_focal_array_scan(self):
        self.v.get_dialog()
        self.run_task(task=self.focal_array_scan)

    def prepare_grid_pattern_scan(self):
        self.lasers = self.con_controller.get_lasers()
        self.set_lasers(self.lasers)
        self.cameras["imaging"] = self.con_controller.get_imaging_camera()
        self.set_camera_roi("imaging")
        self.m.cam_set[self.cameras["imaging"]].prepare_live()
        self.update_trigger_parameters("imaging")
        dtr, sw, dch = self.generate_live_triggers("imaging")
        self.m.daq.write_triggers(digital_sequences=dtr, digital_channels=dch)
        self.con_controller.display_camera_timings(exposure=self.p.trigger.exposure_time,
                                                   clean=self.p.trigger.initial_time,
                                                   standby=self.p.trigger.standby_time)

    def grid_pattern_scan(self):
        try:
            self.prepare_grid_pattern_scan()
        except Exception as e:
            self.logg.error(f"Error preparing grid pattern scanning: {e}")
            return
        try:
            pos_x, pos_y, pos_z = self.con_controller.get_piezo_positions()
            positions = [pos_x[1], pos_y[1], pos_z[1]]
            axis_lengths, step_sizes = self.con_controller.get_piezo_scan_parameters()
            starts = [position - 0.5 * axis_length for position, axis_length in zip(positions, axis_lengths)]
            ends = [position + 0.5 * axis_length for position, axis_length in zip(positions, axis_lengths)]
            scans = [np.arange(start / 10, end / 10 + step_size / 10, step_size / 10) for start, end, step_size in
                     zip(starts, ends, step_sizes)]
            self.m.daq.set_piezo_position([scans[0][0], scans[1][0]], [0, 1])
            # grid pattern minima
            data = []
            sx, sy = scans[0].shape[0], scans[1].shape[0]
            mx = np.zeros((sy, sx))
            self.m.cam_set[self.cameras["imaging"]].start_live()
            time.sleep(0.2)
            for j in range(sy):
                self.m.daq.set_piezo_position([scans[1][j]], [1])
                for i in range(sx):
                    self.m.daq.set_piezo_position([scans[0][i]], [0])
                    time.sleep(0.08)
                    self.m.daq.run_triggers()
                    time.sleep(0.04)
                    temp = self.m.cam_set[self.cameras["imaging"]].get_last_image()
                    self.m.daq.stop_triggers(_close=False)
                    data.append(temp)
                    mx[j, i] = np.mean(temp)
            fd = os.path.join(self.data_folder, time.strftime("%Y%m%d%H%M%S") + '_grid_pattern_scan.tif')
            tf.imwrite(fd, np.asarray(data), imagej=True,
                       resolution=(1 / self.pixel_sizes[self.cameras["imaging"]],
                                   1 / self.pixel_sizes[self.cameras["imaging"]]),
                       metadata={'unit': 'um'})
            fd = os.path.join(self.data_folder, time.strftime("%Y%m%d%H%M%S") + '_grid_pattern_scan_recon.tif')
            tf.imwrite(fd, mx)
            self.v.view_view.plot_image(data=mx, axis_arrays=scans, axis_labels=None)
        except Exception as e:
            self.finish_grid_pattern_scan()
            self.logg.error(f"Error running grid pattern scanning: {e}")
            return
        self.finish_grid_pattern_scan()

    def finish_grid_pattern_scan(self):
        try:
            # self.m.pz.release_lock()
            self.m.cam_set[self.cameras["imaging"]].stop_live()
            self.m.daq.stop_triggers()
            self.lasers_off()
            self.logg.info("Grid pattern scanning image acquired")
        except Exception as e:
            self.logg.error(f"Error stopping grid pattern scanning: {e}")

    def run_grid_pattern_scan(self):
        self.v.get_dialog()
        self.run_task(task=self.grid_pattern_scan)

    @QtCore.pyqtSlot(str)
    def select_dm(self, dm_n):
        self.dfm = self.m.dm[dm_n]
        self.v.ao_view.QComboBox_cmd.clear()
        self.v.ao_view.QComboBox_cmd.addItems([str(i) for i in range(len(self.dfm.dm_cmd))])
        self.v.ao_view.QComboBox_cmd.setCurrentIndex(self.dfm.current_cmd)

    @QtCore.pyqtSlot(int, float)
    def push_actuator(self, n: int, a: float):
        try:
            values = [0.] * self.dfm.n_actuator
            values[n] = a
            self.dfm.set_dm(self.dfm.cmd_add(values, self.dfm.dm_cmd[self.dfm.current_cmd]))
        except Exception as e:
            self.logg.error(f"DM Error: {e}")

    def set_zernike(self, factory=False):
        try:
            md = self.ao_controller.get_img_wfs_method()
            indz, amp = self.ao_controller.get_zernike_mode()
            if factory:
                self.dfm.set_dm(
                    self.dfm.cmd_add([i * amp for i in self.dfm.z2c[indz]], self.dfm.dm_cmd[self.dfm.current_cmd]))
            else:
                self.dfm.set_dm(
                    self.dfm.cmd_add(self.dfm.get_zernike_cmd(indz, amp, md), self.dfm.dm_cmd[self.dfm.current_cmd]))
        except Exception as e:
            self.logg.error(f"DM Error: {e}")

    @QtCore.pyqtSlot()
    def set_dm(self):
        try:
            i = int(self.ao_controller.get_cmd_index())
            self.dfm.set_dm(self.dfm.dm_cmd[i])
            self.dfm.current_cmd = i
        except Exception as e:
            self.logg.error(f"DM Error: {e}")

    @QtCore.pyqtSlot()
    def set_dm_flat(self):
        if int(self.ao_controller.get_cmd_index()) == self.dfm.current_cmd:
            self.dfm.write_flat_cmd(t=time.strftime("%Y_%m_%d_%H_%M"), cmd=self.dfm.dm_cmd[self.dfm.current_cmd])

    @QtCore.pyqtSlot()
    def update_dm(self):
        try:
            self.dfm.dm_cmd.append(self.dfm.temp_cmd[-1])
            self.ao_controller.update_cmd_index()
            self.dfm.set_dm(self.dfm.dm_cmd[-1])
        except Exception as e:
            self.logg.error(f"DM Error: {e}")

    @QtCore.pyqtSlot()
    def load_dm(self):
        filename = self.v.get_file_dialog(sw="Open File")
        if filename is not None:
            try:
                self.dfm.read_cmd(filename)
                self.logg.info('New DM cmd loaded')
                self.v.ao_view.QComboBox_cmd.clear()
                self.v.ao_view.QComboBox_cmd.addItems([str(i) for i in range(len(self.dfm.dm_cmd))])
                self.v.ao_view.QComboBox_cmd.setCurrentIndex(self.dfm.current_cmd)
            except Exception as e:
                self.logg.error(f"DM Error: {e}")

    @QtCore.pyqtSlot()
    def save_dm(self):
        try:
            t = time.strftime("%Y%m%d_%H%M%S_")
            self.dfm.write_cmd(self.data_folder, t, flatfile=False)
            self.logg.info('DM cmd saved')
        except Exception as e:
            self.logg.error(f"DM Error: {e}")

    def set_img_wfs(self, idx):
        if idx == 1:
            parameters = self.ao_controller.get_parameters_img()
            self.p.shwfsr.pixel_size = self.pixel_sizes[self.cameras["wfs"]] / 1000
            self.p.shwfsr.update_parameters(parameters)
            self.logg.info('SHWFS parameter updated')
        elif idx == 2:
            parameters = self.ao_controller.get_parameters_foc()
            self.p.shwfsr.pixel_size = self.pixel_sizes[self.cameras["wfs"]] / 1000
            self.p.shwfsr.update_parameters(parameters)
            self.logg.info('SHWFS parameter updated')
        else:
            raise ValueError("Invalid wfs index")

    def prepare_img_wfs(self):
        self.lasers = self.con_controller.get_lasers()
        self.set_lasers(self.lasers)
        self.cameras["wfs"] = self.ao_controller.get_wfs_camera()
        self.set_camera_roi("wfs")
        self.m.cam_set[self.cameras["wfs"]].prepare_live()
        self.set_img_wfs(self.cameras["wfs"])
        self.update_trigger_parameters("wfs")
        dtr, sw, chs = self.p.trigger.generate_digital_triggers(self.lasers, self.cameras["wfs"])
        self.set_switch(self.p.trigger.galvo_sw_states[self.cameras["wfs"]])
        self.m.daq.write_triggers(digital_sequences=dtr, digital_channels=chs, finite=False)

    def start_img_wfs(self):
        try:
            self.prepare_img_wfs()
        except Exception as e:
            self.logg.error(f"Error preparing wfs: {e}")
            self.stop_img_wfs()
        try:
            self.m.cam_set[self.cameras["wfs"]].start_live()
            self.m.daq.run_triggers()
            self.thread_wfs.start()
        except Exception as e:
            self.logg.error(f"Error starting wfs: {e}")
            self.stop_img_wfs()
            return

    def stop_img_wfs(self):
        try:
            if self.thread_wfs.isRunning():
                self.thread_wfs.quit()
                self.thread_wfs.wait()
            self.m.cam_set[self.cameras["wfs"]].stop_live()
            self.m.daq.stop_triggers()
            self.lasers_off()
        except Exception as e:
            self.logg.error(f"Error stopping wfs: {e}")

    def img_wfs(self, sw):
        if sw:
            self.start_img_wfs()
        else:
            self.stop_img_wfs()

    @QtCore.pyqtSlot()
    def imshow_img_wfs(self):
        try:
            self.p.shwfsr.meas = self.m.cam_set[self.cameras["wfs"]].get_last_image()
            self.view_controller.plot_sh(self.p.shwfsr.meas, layer=self.cameras["wfs"])
        except Exception as e:
            self.logg.error(f"Error showing shwfs: {e}")

    @QtCore.pyqtSlot()
    def set_reference_wf(self):
        try:
            self.p.shwfsr.ref = self.m.cam_set[self.cameras["wfs"]].get_last_image()
            self.view_controller.plot_shb(self.p.shwfsr.ref)
            self.logg.info('shwfs base set')
        except Exception as e:
            self.logg.error(f"Error setting shwfs base: {e}")

    @QtCore.pyqtSlot()
    def run_img_wfr(self):
        self.v.get_dialog()
        self.run_task(task=self.img_wfr, callback=self.imshow_img_wfr)

    def img_wfr(self):
        try:
            self.p.shwfsr.method = self.ao_controller.get_gradient_method_img()
            self.p.shwfsr.wavefront_reconstruction()
        except Exception as e:
            self.logg.error(f"SHWFS Reconstruction Error: {e}")

    def imshow_img_wfr(self):
        try:
            self.view_controller.plot_wf(self.p.shwfsr.wf)
            self.ao_controller.display_img_wf_properties(ipr.img_properties(self.p.shwfsr.wf))
        except Exception as e:
            self.logg.error(f"SHWFS Wavefront Show Error: {e}")

    @QtCore.pyqtSlot()
    def run_compute_img_wf(self):
        self.v.get_dialog()
        self.run_task(task=self.compute_img_wf)

    def compute_img_wf(self):
        md = self.ao_controller.get_gradient_method_img()
        gradx, grady = self.p.shwfsr.get_gradient_xy(mtd=md)
        a = self.dfm.get_zernike_coffs(gradx, grady)
        self.view_controller.plot_update(a, x=np.asarray(tz.modes))
        self.sazf.emit(tz.modes, a)

    @QtCore.pyqtSlot(list, np.ndarray)
    def save_zernike_coeffs(self, zdx: list, za: np.ndarray):
        df = pd.DataFrame({'mods': zdx, 'amps': za})
        fn = self.v.get_file_dialog()
        if fn is not None:
            file_path = fn + '_' + time.strftime("%Y%m%d%H%M%S")
        else:
            file_path = os.path.join(self.data_folder, time.strftime("%Y%m%d%H%M%S"))
        df.to_excel(file_path + '_zernike_coefficients.xlsx', index=False)

    @QtCore.pyqtSlot()
    def save_img_wf(self):
        fn = self.v.get_file_dialog()
        if fn is not None:
            file_name = os.path.join(self.data_folder, time.strftime("%Y%m%d%H%M%S") + "_" + fn)
        else:
            file_name = os.path.join(self.data_folder, time.strftime("%Y%m%d%H%M%S"))
        self.p.shwfsr.save_wfs_results(file_name, self.dfm)

    def prepare_influence_function(self):
        self.lasers = self.con_controller.get_lasers()
        self.set_lasers(self.lasers)
        self.cameras["wfs"] = self.ao_controller.get_wfs_camera()
        self.set_camera_roi("wfs")
        self.m.cam_set[self.cameras["wfs"]].prepare_live()
        self.set_img_wfs(self.cameras["wfs"])
        self.update_trigger_parameters("wfs")
        wfs = self.ao_controller.get_dm_selection()
        self.set_switch(self.p.trigger.galvo_sw_states[self.cameras["wfs"]])
        dtr, sw, chs = self.p.trigger.generate_digital_triggers(self.lasers, self.cameras["wfs"])
        self.m.daq.write_triggers(digital_sequences=dtr, digital_channels=chs)

    def influence_function(self):
        try:
            self.prepare_influence_function()
        except Exception as e:
            self.finish_influence_function()
            self.logg.error(f"Error preparing influence function: {e}")
            return
        try:
            fd = os.path.join(self.data_folder, time.strftime("%Y%m%d%H%M") + '_influence_function')
            os.makedirs(fd, exist_ok=True)
            self.logg.info(f'Directory {fd} has been created successfully.')
        except Exception as er:
            self.logg.error(f'Error creating influence function directory: {er}')
            self.finish_influence_function()
            return
        try:
            n, amp = self.ao_controller.get_actuator()
            self.m.cam_set[self.cameras["wfs"]].start_live()
            time.sleep(0.02)
            for i in range(self.dfm.n_actuator):
                shimg = []
                self.v.dialog_text.setText(f"actuator {i}")
                values = [0.] * self.dfm.n_actuator
                self.dfm.set_dm(values)
                time.sleep(0.02)
                self.m.daq.run_triggers()
                time.sleep(0.08)
                shimg.append(self.m.cam_set[self.cameras["wfs"]].get_last_image())
                self.m.daq.stop_triggers(_close=False)
                values[i] = amp
                self.dfm.set_dm(values)
                time.sleep(0.02)
                self.m.daq.run_triggers()
                time.sleep(0.08)
                shimg.append(self.m.cam_set[self.cameras["wfs"]].get_last_image())
                self.m.daq.stop_triggers(_close=False)
                values = [0.] * self.dfm.n_actuator
                self.dfm.set_dm(values)
                time.sleep(0.02)
                self.m.daq.run_triggers()
                time.sleep(0.08)
                shimg.append(self.m.cam_set[self.cameras["wfs"]].get_last_image())
                self.m.daq.stop_triggers(_close=False)
                values[i] = - amp
                self.dfm.set_dm(values)
                time.sleep(0.02)
                self.m.daq.run_triggers()
                time.sleep(0.08)
                shimg.append(self.m.cam_set[self.cameras["wfs"]].get_last_image())
                self.m.daq.stop_triggers(_close=False)
                tf.imwrite(fd + r'/' + 'actuator_' + str(i) + '_push_' + str(amp) + '.tif', np.asarray(shimg))
        except Exception as e:
            self.logg.error(f"Error running influence function: {e}")
            self.finish_influence_function()
            return
        try:
            self.v.dialog_text.setText(f"computing influence function")
            dmn = self.v.ao_view.QComboBox_dms.currentText()
            self.p.shwfsr.generate_influence_matrices(data_folder=fd, dm=self.dfm, sv=self.config)
        except Exception as e:
            self.logg.error(f"Error computing influence function: {e}")
            self.finish_influence_function()
            return
        self.finish_influence_function()

    def finish_influence_function(self):
        try:
            self.lasers_off()
            self.m.cam_set[self.cameras["wfs"]].stop_live()
            self.m.daq.stop_triggers()
        except Exception as e:
            self.logg.error(f"Error finishing influence function: {e}")

    @QtCore.pyqtSlot()
    def run_influence_function(self):
        self.v.get_dialog()
        self.run_task(self.influence_function)

    def prepare_close_loop_correction(self):
        self.lasers = self.con_controller.get_lasers()
        self.set_lasers(self.lasers)
        self.cameras["wfs"] = self.ao_controller.get_wfs_camera()
        self.set_camera_roi("wfs")
        self.m.cam_set[self.cameras["wfs"]].prepare_live()
        self.set_img_wfs(self.cameras["wfs"])
        self.update_trigger_parameters("wfs")
        self.dfm.ctrl.reset_control()
        self.set_switch(self.p.trigger.galvo_sw_states[self.cameras["wfs"]])
        dtr, sw, chs = self.p.trigger.generate_digital_triggers(self.lasers, self.cameras["wfs"])
        self.m.daq.write_triggers(digital_sequences=dtr, digital_channels=chs, finite=True)

    def close_loop_correction(self):
        try:
            self.m.daq.run_triggers()
            time.sleep(0.08)
            self.p.shwfsr.meas = self.m.cam_set[self.cameras["wfs"]].get_last_image()
            self.m.daq.stop_triggers(_close=False)
            md = self.ao_controller.get_img_wfs_method()
            self.dfm.get_correction(self.p.shwfsr.get_gradient_xy(), method="modal")
            self.dfm.set_dm(self.dfm.dm_cmd[-1])
            self.ao_controller.update_cmd_index()
            i = int(self.ao_controller.get_cmd_index())
            self.dfm.current_cmd = i
        except Exception as e:
            self.logg.error(f"Error Run CloseLoop Correction Error: {e}")
            self.finish_close_loop_correction()
            return

    def finish_close_loop_correction(self):
        try:
            self.lasers_off()
            self.m.cam_set[self.cameras["wfs"]].stop_live()
            self.m.daq.stop_triggers()
        except Exception as e:
            self.logg.error(f"CloseLoop Correction Error: {e}")

    @QtCore.pyqtSlot(int)
    def run_close_loop_correction(self, nlp: int):
        try:
            self.prepare_close_loop_correction()
        except Exception as e:
            self.logg.error(f"Prepare CloseLoop Correction Error: {e}")
            self.finish_close_loop_correction()
            return
        try:
            self.v.get_dialog()
            self.m.cam_set[self.cameras["wfs"]].start_live()
            time.sleep(0.02)
            self.run_task(task=self.close_loop_correction, iteration=nlp)
        except Exception as e:
            self.finish_close_loop_correction()
            self.logg.error(f"CloseLoop Correction Error: {e}")
            return
        self.finish_close_loop_correction()

    @QtCore.pyqtSlot()
    def set_array_mask(self):
        m = self.view_controller.get_image_data(layer=self.cameras["imaging"])
        m = m - m.min()
        m = m / m.max()
        m[m < 0.5] = 0.
        self.view_controller.plot_msk(data=m)

    def prepare_sensorless_iteration(self):
        vd_mod = self.con_controller.get_live_mode()
        self.lasers = self.con_controller.get_lasers()
        self.set_lasers(self.lasers)
        self.cameras["imaging"] = self.con_controller.get_imaging_camera()
        self.set_camera_roi("imaging")
        self.m.cam_set[self.cameras["imaging"]].prepare_live()
        if vd_mod == "Wide Field":
            dtr, sw, dch = self.generate_live_triggers("imaging")
            self.set_switch(self.p.trigger.galvo_sw_states[self.cameras["imaging"]])
            self.m.daq.write_triggers(digital_sequences=dtr, digital_channels=dch)
            self.con_controller.display_camera_timings(exposure=self.p.trigger.exposure_time,
                                                       clean=self.p.trigger.initial_time,
                                                       standby=self.p.trigger.standby_time)
        elif vd_mod == "Dot Scan":
            dtr, gtr, chs = self.p.trigger.generate_digital_scanning_triggers(self.lasers, self.cameras["imaging"])
            self.m.daq.write_triggers(galvo_sequences=gtr, galvo_channels=[0, 1, 2],
                                      digital_sequences=dtr, digital_channels=chs)
            self.con_controller.display_camera_timings(exposure=self.p.trigger.exposure_time,
                                                       clean=self.p.trigger.initial_time,
                                                       standby=self.p.trigger.standby_time)
        else:
            self.m.cam_set[self.cameras["imaging"]].stop_live()
            self.lasers_off()
            raise ValueError("Invalid video mode")

    def sensorless_iteration(self, dms):
        ims = []
        for dmsp in dms:
            self.dfm.set_dm(dmsp)
            time.sleep(0.016)
            self.m.daq.run_triggers()
            time.sleep(0.032)
            self.m.daq.stop_triggers(_close=False)
            ims.append(self.m.cam_set[self.cameras["imaging"]].get_last_image())
        return ims

    def sensorless_iterations(self):
        try:
            lpr, hpr, slf, mf, err = self.ao_controller.get_ao_parameters()
            if mf == 'Mask(Intensity)':
                msk = self.view_controller.get_image_data(7)
            name = time.strftime("%Y%m%d_%H%M%S_") + self.dfm.dm_serial + '_ao_iterations_' + mf
            new_folder = os.path.join(self.data_folder, name)
            os.makedirs(new_folder, exist_ok=True)
            self.logg.info(f'Directory {new_folder} has been created successfully.')
        except Exception as e:
            self.logg.error(f'Error creating directory for sensorless iteration: {e}')
            return
        try:
            self.prepare_sensorless_iteration()
        except Exception as e:
            self.logg.error(f"Prepare sensorless iteration Error: {e}")
            return
        try:
            mode_start, mode_stop, amp_start, amp_step, amp_step_number = self.ao_controller.get_ao_iteration()
            md = self.ao_controller.get_img_wfs_method()
            amprange = [amp_start + step_number * amp_step for step_number in range(amp_step_number)]
            results = [('Mode', 'Amp', 'Metric')]
            za = []
            mv = []
            zp = [0] * self.dfm.n_zernike
            cmd = self.dfm.dm_cmd[self.dfm.current_cmd]
            self.m.cam_set[self.cameras["imaging"]].start_live()
            time.sleep(0.1)
            self.logg.info("Sensorless AO iterations start")
            self.dfm.set_dm(cmd)
            time.sleep(0.016)
            if err:
                images = []
                for i in range(8):
                    self.m.daq.run_triggers()
                    time.sleep(0.032)
                    self.m.daq.stop_triggers(_close=False)
                    images.append(self.m.cam_set[self.cameras["imaging"]].get_last_image())
                if mf == "Max(Intensity)":
                    mts = [img.max() for img in images]
                if mf == "Sum(Intensity)":
                    mts = [img.sum() for img in images]
                if mf == 'Mask(Intensity)':
                    mts = [(img * msk).sum() for img in images]
                if mf == "SNR(FFT)":
                    mts = [ipr.snr(img, lpr, hpr, True) for img in images]
                if mf == "HighPass(FFT)":
                    mts = [ipr.hpf(img, hpr) for img in images]
                if mf == "Selected(FFT)":
                    mts = [ipr.selected_frequency(img, [slf, 2 * slf]) for img in images]
                std = np.std(mts)
                fn = new_folder + r"\original.tiff"
                tf.imwrite(str(fn), np.asarray(images))
            else:
                self.m.daq.run_triggers()
                time.sleep(0.032)
                self.m.daq.stop_triggers(_close=False)
                fn = new_folder + r"\original.tiff"
                tf.imwrite(str(fn), self.m.cam_set[self.cameras["imaging"]].get_last_image())
            for mode in range(mode_start, mode_stop + 1):
                self.v.dialog_text.setText(f"Zernike mode #{mode}")
                labels = ["zm%0.2d_amp%.4f" % (mode, amp) for amp in amprange]
                cmds = [self.dfm.cmd_add(self.dfm.get_zernike_cmd(mode, amp, method=md), cmd) for amp in amprange]
                images = self.sensorless_iteration(cmds)
                if mf == "Max(Intensity)":
                    mts = [img.max() for img in images]
                if mf == "Sum(Intensity)":
                    mts = [img.sum() for img in images]
                if mf == 'Mask(Intensity)':
                    mts = [(img * msk).sum() for img in images]
                if mf == "SNR(FFT)":
                    mts = [ipr.snr(img, lpr, hpr, True) for img in images]
                if mf == "HighPass(FFT)":
                    mts = [ipr.hpf(img, hpr) for img in images]
                if mf == "Selected(FFT)":
                    mts = [ipr.selected_frequency(img, [slf, 2 * slf]) for img in images]
                self.logg.info(f"zernike mode #{mode}, ({amprange}), ({mts})")
                self.sig_plt.emit(amprange, mts)
                if err:
                    mts_err = [std] * len(mts)
                    pm = ipr.peak_find(amprange, mts, mts_err)
                else:
                    pm = ipr.peak_find(amprange, mts)
                if isinstance(pm, str):
                    self.logg.error(f"zernike mode #{mode} " + pm)
                else:
                    zp[mode] = pm
                    cmd = self.dfm.cmd_add(self.dfm.get_zernike_cmd(mode, pm, method=md), cmd)
                    self.dfm.set_dm(cmd)
                    self.logg.info("set mode %d at value of %.4f" % (mode, pm))
                for amp, mt in zip(amprange, mts):
                    results.append((mode, amp, mt))
                za.extend(amprange)
                mv.extend(mts)
                fn = os.path.join(str(new_folder), f"zernike mode #{mode}.tiff")
                with tf.TiffWriter(fn) as tif:
                    for img, label in zip(images, labels):
                        tif.write(img, description=label)
            self.dfm.set_dm(cmd)
            time.sleep(0.016)
            self.m.daq.run_triggers()
            time.sleep(0.032)
            self.m.daq.stop_triggers(_close=False)
            fn = new_folder + r"\final.tiff"
            tf.imwrite(str(fn), self.m.cam_set[self.cameras["imaging"]].get_last_image())
            self.dfm.dm_cmd.append(cmd)
            self.ao_controller.update_cmd_index()
            i = int(self.ao_controller.get_cmd_index())
            self.dfm.current_cmd = i
            self.dfm.write_cmd(new_folder, '_')
            self.dfm.save_sensorless_results(os.path.join(str(new_folder), 'results.xlsx'), za, mv, zp)
        except Exception as e:
            self.finish_sensorless_iteration()
            self.logg.error(f"Sensorless AO Error: {e}")
            return
        self.finish_sensorless_iteration()

    def finish_sensorless_iteration(self):
        try:
            self.lasers_off()
            self.m.daq.stop_triggers()
            self.m.cam_set[self.cameras["imaging"]].stop_live()
            self.logg.info("sensorless AO finished")
        except Exception as e:
            self.logg.error(f"Finish Sensorless AO Error: {e}")

    @QtCore.pyqtSlot()
    def run_sensorless_iteration(self):
        self.v.get_dialog()
        self.run_task(task=self.sensorless_iterations)

    def sensorless_metric_acquisition(self):
        try:
            self.prepare_sensorless_iteration()
        except Exception as e:
            self.logg.error(f"Prepare sensorless iteration Error: {e}")
            return
        try:
            name = time.strftime("%Y%m%d_%H%M%S_") + 'sensorless_metric_acquisition'
            new_folder = os.path.join(self.data_folder, name)
            os.makedirs(new_folder, exist_ok=True)
            self.logg.info(f'Directory {new_folder} has been created successfully.')
        except Exception as e:
            self.logg.error(f'Error creating directory for sensorless iteration: {e}')
            return
        try:
            t = time.strftime("%Y%m%d%H%M_")
            mode_start, mode_stop, amp_start, amp_step, amp_step_number = self.ao_controller.get_ao_iteration()
            md = self.ao_controller.get_img_wfs_method()
            amprange = np.linspace(amp_start, -amp_start, amp_step_number + 1)
            cmd = self.dfm.dm_cmd[self.dfm.current_cmd]
            self.m.cam_set[self.cameras["imaging"]].start_live()
            time.sleep(0.08)
            self.logg.info("Automated sensorless AO iterations start")
            self.dfm.set_dm(cmd)
            time.sleep(0.016)
            tpd = []
            for _ in range(16):
                self.m.daq.run_triggers()
                time.sleep(0.032)
                self.m.daq.stop_triggers(_close=False)
                tpd.append(self.m.cam_set[self.cameras["imaging"]].get_last_image())
            fn = os.path.join(new_folder, t + "zm_%0.2d_amp_%.3f.tiff" % (0, 0.000))
            tf.imwrite(str(fn), np.asarray(tpd))
            for mode in range(mode_start, mode_stop + 1):
                self.v.dialog_text.setText(f"Zernike mode #{mode}")
                for amp in amprange:
                    label = t + "zm_%0.2d_amp_%.3f.tiff" % (mode, amp)
                    cm = self.dfm.cmd_add(self.dfm.get_zernike_cmd(mode, amp, method=md), cmd)
                    self.dfm.set_dm(cm)
                    time.sleep(0.016)
                    ims = []
                    for _ in range(16):
                        self.m.daq.run_triggers()
                        time.sleep(0.032)
                        self.m.daq.stop_triggers(_close=False)
                        ims.append(self.m.cam_set[self.cameras["imaging"]].get_last_image())
                    fn = os.path.join(new_folder, label)
                    tf.imwrite(str(fn), np.asarray(ims))
            self.dfm.set_dm(cmd)
        except Exception as e:
            self.finish_sensorless_iteration()
            self.logg.error(f"Sensorless AO Error: {e}")
            return
        self.finish_sensorless_iteration()

    @QtCore.pyqtSlot()
    def run_sensorless_metric_acquisition(self):
        self.v.get_dialog()
        self.run_task(task=self.sensorless_metric_acquisition)

    def sensorless_ml_acquisition(self):
        try:
            self.prepare_sensorless_iteration()
        except Exception as e:
            self.logg.error(f"Prepare sensorless iteration Error: {e}")
            return
        try:
            name = time.strftime("%Y%m%d_%H%M%S_") + 'sensorless_ml_acquisition'
            new_folder = os.path.join(self.data_folder, name)
            os.makedirs(new_folder, exist_ok=True)
            self.logg.info(f'Directory {new_folder} has been created successfully.')
        except Exception as e:
            self.logg.error(f'Error creating directory for sensorless iteration: {e}')
            return
        try:
            mode_start, mode_stop, amp_start, amp_step, amp_step_number = self.ao_controller.get_ao_iteration()
            md = self.ao_controller.get_img_wfs_method()
            self.m.cam_set[self.cameras["imaging"]].start_live()
            self.dfm.set_dm(self.dfm.dm_cmd[self.dfm.current_cmd])
            self.logg.info("Automated sensorless AO iterations start")
            mds = np.arange(mode_start, mode_stop + 1)
            for _ in range(30):
                amps = np.random.uniform(amp_start, -amp_start, size=mds.shape)
                cmd = self.dfm.dm_cmd[self.dfm.current_cmd]
                for m, a in zip(mds, amps):
                    cmd = self.dfm.cmd_add(self.dfm.get_zernike_cmd(m, a, method=md), cmd)
                self.dfm.set_dm(cmd)
                time.sleep(0.08)
                self.m.daq.run_triggers()
                time.sleep(0.032)
                self.m.daq.stop_triggers(_close=False)
                img = self.m.cam_set[self.cameras["imaging"]].get_last_image()
                fn = os.path.join(new_folder, f"{str(uuid.uuid4())}.tiff")
                tf.imwrite(str(fn), img, metadata={"modes": mds.tolist(), "amplitudes": amps.tolist()})
        except Exception as e:
            self.finish_sensorless_iteration()
            self.logg.error(f"Sensorless AO Error: {e}")
            return
        self.finish_sensorless_iteration()

    @QtCore.pyqtSlot()
    def run_sensorless_ml_acquisition(self):
        self.v.get_dialog()
        self.run_task(task=self.sensorless_ml_acquisition)

    def auto_sensorless(self):
        self.loop_flag = True
        try:
            self.prepare_sensorless_iteration()
        except Exception as e:
            self.logg.error(f"Prepare sensorless iteration Error: {e}")
            return
        try:
            lpr, hpr, slf, mf, err = self.ao_controller.get_ao_parameters()
            name = time.strftime("%Y%m%d_%H%M%S_") + '_auto_ao_iterations_' + mf
            new_folder = os.path.join(self.data_folder, name)
            os.makedirs(new_folder, exist_ok=True)
            self.logg.info(f'Directory {new_folder} has been created successfully.')
        except Exception as e:
            self.logg.error(f'Error creating directory for sensorless iteration: {e}')
            return
        try:
            mode_start, mode_stop, amp_start, amp_step, amp_step_number = self.ao_controller.get_ao_iteration()
            md = self.ao_controller.get_img_wfs_method()
            za = []
            mv = []
            zp = [0] * self.dfm.n_zernike
            cmd = self.dfm.dm_cmd[self.dfm.current_cmd]
            self.m.cam_set[self.cameras["imaging"]].start_live()
            time.sleep(0.1)
            self.logg.info("Automated sensorless AO iterations start")
            self.dfm.set_dm(cmd)
            time.sleep(0.016)
            self.m.daq.run_triggers()
            time.sleep(0.032)
            self.m.daq.stop_triggers(_close=False)
            fn = new_folder + r"\original.tiff"
            tf.imwrite(str(fn), self.m.cam_set[self.cameras["imaging"]].get_last_image())
            for mode in range(mode_start, mode_stop + 1):
                step_size = amp_step
                self.v.dialog_text.setText(f"Zernike mode #{mode}")
                while step_size >= amp_step:
                    if self.loop_flag:
                        amps = [- step_size + step_number * step_size for step_number in range(3)]
                        cmds = [self.dfm.cmd_add(self.dfm.get_zernike_cmd(mode, amp, method=md), cmd) for amp in amps]
                        images = self.sensorless_iteration(cmds)
                        if mode == 3 or 10:
                            mts = [-ipr.calculate_focus_measure_with_sobel(img) for img in images]
                        else:
                            mts = [ipr.hpf(img, hpr) for img in images]
                        self.logg.info(f"zernike mode #{mode}, ({amps}), ({mts})")
                        self.sig_plt.emit(amps, mts)
                        pm = ipr.peak_find(amps, mts)
                        if isinstance(pm, str):
                            self.logg.error(f"zernike mode #{mode} " + pm)
                            step_size *= 1.5
                        else:
                            if step_size < amp_step:
                                zp[mode] = pm
                                cmd = self.dfm.cmd_add(self.dfm.get_zernike_cmd(mode, pm, method=md), cmd)
                                self.dfm.set_dm(cmd)
                                self.logg.info("set mode %d at value of %.4f" % (mode, pm))
                                break
                            else:
                                step_size /= 1.5
                    else:
                        break
            self.dfm.set_dm(cmd)
            time.sleep(0.016)
            self.m.daq.run_triggers()
            time.sleep(0.032)
            self.m.daq.stop_triggers(_close=False)
            fn = new_folder + r"\final.tiff"
            tf.imwrite(str(fn), self.m.cam_set[self.cameras["imaging"]].get_last_image())
            self.dfm.dm_cmd.append(cmd)
            self.ao_controller.update_cmd_index()
            i = int(self.ao_controller.get_cmd_index())
            self.dfm.current_cmd = i
            self.dfm.write_cmd(new_folder, '_')
            self.dfm.save_sensorless_results(os.path.join(str(new_folder), 'results.xlsx'), za, mv, zp)
        except Exception as e:
            self.finish_sensorless_iteration()
            self.logg.error(f"Sensorless AO Error: {e}")
            return
        self.finish_sensorless_iteration()

    @QtCore.pyqtSlot()
    def run_auto_sensorless(self):
        self.v.get_dialog(interrupt=True)
        self.v.dialog.dialog_closed.connect(self.interrupt_thread)
        self.run_task(task=self.auto_sensorless)

    def prepare_shwfs_acquisition(self):
        self.lasers = self.con_controller.get_lasers()
        self.set_lasers(self.lasers)
        self.cameras["wfs"] = self.ao_controller.get_wfs_camera()
        self.set_camera_roi("wfs")
        self.m.cam_set[self.cameras["wfs"]].prepare_live()
        self.set_img_wfs(self.cameras["wfs"])
        self.update_trigger_parameters("wfs")
        self.set_switch(self.p.trigger.galvo_sw_states[self.cameras["wfs"]])
        dtr, sw, chs = self.p.trigger.generate_digital_triggers(self.lasers, self.cameras["wfs"])
        self.m.daq.write_triggers(digital_sequences=dtr, digital_channels=chs, finite=True)

    def shwfs_acquisition(self):
        try:
            self.prepare_shwfs_acquisition()
        except Exception as e:
            self.logg.error(f"Error prepare shwfs acquisition: {e}")
            self.finish_shwfs_acquisition()
            return
        try:
            fd = os.path.join(self.data_folder, time.strftime("%Y%m%d%H%M") + '_shwfs_acquisition')
            os.makedirs(fd, exist_ok=True)
            self.logg.info(f'Directory {fd} has been created successfully.')
        except Exception as er:
            self.logg.error(f'Error creating directory: {er}')
            self.finish_shwfs_acquisition()
            return
        try:
            mtd = self.ao_controller.get_img_wfs_method()
            modes = np.arange(16)
            self.m.cam_set[self.cameras["wfs"]].start_live()
            time.sleep(0.02)
            for i in range(64):
                self.v.dialog_text.setText(f"Acquisition #{i}")
                data = []
                amps = np.zeros((modes.shape[0], 2))
                cmd = self.dfm.dm_cmd[self.dfm.current_cmd]
                self.dfm.set_dm(cmd)
                time.sleep(0.02)
                self.m.daq.run_triggers()
                time.sleep(0.08)
                data.append(self.m.cam_set[self.cameras["wfs"]].get_last_image())
                self.m.daq.stop_triggers(_close=False)
                amps[:, 0] = np.random.rand(modes.shape[0]) / 128
                for m, mode in enumerate(modes):
                    amp = amps[m, 0]
                    cmd = self.dfm.cmd_add(self.dfm.get_zernike_cmd(mode, amp, method=mtd), cmd)
                self.dfm.set_dm(cmd)
                time.sleep(0.02)
                self.m.daq.run_triggers()
                time.sleep(0.08)
                data.append(self.m.cam_set[self.cameras["wfs"]].get_last_image())
                self.m.daq.stop_triggers(_close=False)
                self.p.shwfsr.ref = data[0]
                self.p.shwfsr.meas = data[1]
                md = self.ao_controller.get_gradient_method_img()
                gradx, grady = self.p.shwfsr.get_gradient_xy(mtd=md)
                amps[:, 1] = self.dfm.get_zernike_coffs(gradx, grady)
                t = time.strftime("%Y%m%d_%H%M%S_")
                # fn = os.path.join(fd, t + "shwfs_proc_images.tif")
                # tf.imwrite(fn, self.p.shwfsr.im)
                # fn = os.path.join(fd, t + "shwfs_recon_wf.tif")
                # tf.imwrite(fn, self.p.shwfsr.wf)
                fn = os.path.join(fd, t + "shwfs_wf_zcoffs.xlsx")
                df = pd.DataFrame(amps, index=modes, columns=['Amp_Inpt', 'Amp_Meas'])
                with pd.ExcelWriter(fn, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Zernike Amplitudes')
        except Exception as er:
            self.finish_shwfs_acquisition()
            self.logg.error(f'Error running shwfs acquisition: {er}')
            return
        self.finish_shwfs_acquisition()

    def finish_shwfs_acquisition(self):
        try:
            self.lasers_off()
            self.m.cam_set[self.cameras["wfs"]].stop_live()
            self.m.daq.stop_triggers()
        except Exception as e:
            self.logg.error(f"Error finishing shwfs acquisition: {e}")

    @QtCore.pyqtSlot()
    def run_shwfs_acquisition(self):
        self.v.get_dialog()
        self.run_task(self.shwfs_acquisition)


class TaskWorkerSignals(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(tuple)


class TaskWorker(QtCore.QObject):
    def __init__(self, task=None, n=1, parent=None):
        super().__init__(parent)
        self.task = task if task is not None else self._do_nothing
        self.n = n
        self.signals = TaskWorkerSignals()

    def run(self):
        try:
            for i in range(self.n):
                self._do()
            self.signals.finished.emit()
        except Exception as e:
            self.signals.error.emit((e, traceback.format_exc()))
            return

    @QtCore.pyqtSlot()
    def _do(self):
        self.task()

    @staticmethod
    def _do_nothing():
        pass


class LoopWorker(QtCore.QObject):
    signal_loop = QtCore.pyqtSignal()

    def __init__(self, loop=None, callback=False, dt=0, parent=None):
        super().__init__(parent)
        self.loop = loop if loop is not None else self._do_nothing
        self.callback = callback
        if self.callback:
            self.signal_loop_callback = QtCore.pyqtSignal()
        self.dt = dt
        self._stop = False
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._do)
        if dt > 0:
            self.timer.setInterval(dt)

    def start(self):
        self._stop = False
        if not self.timer.isActive():
            self.timer.start()

    def stop(self):
        self._stop = True
        if self.timer.isActive():
            self.timer.stop()
        if self.callback:
            self.signal_loop_callback.emit()

    @QtCore.pyqtSlot()
    def _do(self):
        if self._stop:
            return
        self.loop()
        self.signal_loop.emit()

    @staticmethod
    def _do_nothing():
        pass
