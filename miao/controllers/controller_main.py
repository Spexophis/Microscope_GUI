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
    sada = QtCore.pyqtSignal(str, np.ndarray, list)
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
        self._set_signal_connections()
        self._initial_setup()
        self.lasers = []
        self.cameras = {"imaging": 0, "wfs": 1}
        self.acq_num = 1
        # dedicated thread pool for tasks
        self.task_worker = None
        self.task_thread = None
        self.loop_flag = False
        self.videoWorker = None
        self.thread_video = None
        self.fftWorker = None
        self.thread_fft = None
        self.plotWorker = None
        self.thread_plot = None
        self.wfsWorker = None
        self.thread_wfs = None

    def setup_video_thread(self):
        # video thread
        self.videoWorker = LoopWorker(dt=100)
        self.videoWorker.signal_loop.connect(self.imshow_main)
        self.thread_video = QtCore.QThread()
        self.videoWorker.moveToThread(self.thread_video)
        self.thread_video.started.connect(self.videoWorker.start)
        self.thread_video.finished.connect(self.videoWorker.stop)

    def setup_fft_thread(self):
        # image process thread
        self.fftWorker = LoopWorker(dt=250)
        self.fftWorker.signal_loop.connect(self.imshow_fft)
        self.thread_fft = QtCore.QThread()
        self.fftWorker.moveToThread(self.thread_fft)
        self.thread_fft.started.connect(self.fftWorker.start)
        self.thread_fft.finished.connect(self.fftWorker.stop)

    def setup_plot_thread(self):
        # plot thread
        self.plotWorker = LoopWorker(dt=250)
        self.plotWorker.signal_loop.connect(self.profile_plot)
        self.thread_plot = QtCore.QThread()
        self.plotWorker.moveToThread(self.thread_plot)
        self.thread_plot.started.connect(self.plotWorker.start)
        self.thread_plot.finished.connect(self.plotWorker.stop)

    def setup_wfs_thread(self):
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
        # Galvo Scanners
        # self.v.con_view.Signal_galvo_set.connect(self.set_galvo)
        self.v.con_view.Signal_galvo_scan_update.connect(self.update_galvo_scanner)
        # Cobolt Lasers
        self.v.con_view.Signal_set_laser.connect(self.set_laser)
        # Main Image Control
        self.v.con_view.Signal_plot_trigger.connect(self.plot_trigger)
        self.v.con_view.Signal_video.connect(self.video)
        self.v.con_view.Signal_fft.connect(self.fft)
        self.v.con_view.Signal_plot_profile.connect(self.plot_live)
        self.v.con_view.Signal_add_profile.connect(self.plot_add)
        self.v.con_view.Signal_set_mask.connect(self.set_array_mask)
        # NUCLEO
        # self.v.con_view.Signal_nucleo_update.connect(self.update_nucleo)
        self.v.con_view.Signal_nucleo_send.connect(self.send_nucleo)
        # Main Data Recording
        self.v.con_view.Signal_data_acquire.connect(self.data_acquisition)
        # DM
        self.v.ao_view.Signal_push_actuator.connect(self.push_actuator)
        self.v.ao_view.Signal_set_zernike.connect(self.set_zernike)
        self.v.ao_view.Signal_set_dm.connect(self.set_dm)
        self.v.ao_view.Signal_load_dm.connect(self.load_dm)
        self.v.ao_view.Signal_update_cmd.connect(self.update_dm)
        self.v.ao_view.Signal_save_dm.connect(self.save_dm)
        self.v.ao_view.Signal_set_dm_flat.connect(self.set_dm_flat)
        self.v.ao_view.Signal_influence_function.connect(self.run_influence_function)
        # WFS
        self.v.ao_view.Signal_foc_shwfs_base.connect(self.set_reference_wf)
        self.v.ao_view.Signal_foc_wfs.connect(self.img_wfs)
        self.v.ao_view.Signal_foc_shwfr_run.connect(self.run_img_wfr)
        self.v.ao_view.Signal_foc_shwfs_compute_wf.connect(self.run_compute_img_wf)
        self.v.ao_view.Signal_foc_shwfs_save_wf.connect(self.save_img_wf)
        self.v.ao_view.Signal_foc_shwfs_acquisition.connect(self.run_shwfs_acquisition)
        # AO
        self.v.ao_view.Signal_foc_shwfs_correct_wf.connect(self.run_close_loop_correction)
        self.v.ao_view.Signal_sensorlessAO_run.connect(self.run_sensorless_iteration)
        self.v.ao_view.Signal_sensorlessAO_auto.connect(self.run_auto_sensorless)
        self.v.ao_view.Signal_sensorlessAO_metric_acquisition.connect(self.run_sensorless_metric_acquisition)
        self.v.ao_view.Signal_sensorlessAO_ml_acquisition.connect(self.run_sensorless_ml_acquisition)

    def _initial_setup(self):
        try:

            self.loop_flag = True

            self.reset_galvo_positions()
            self.update_galvo_scanner()

            self.laser_lists = ["405", "488"]

            self.pixel_sizes = [0.02738, 3.45]

            self.dm_cmd_ind = self.m.dm.current_cmd
            self.dfm = self.m.dm
            self.v.ao_view.QComboBox_cmd.clear()
            self.v.ao_view.QComboBox_cmd.addItems([str(i) for i in range(len(self.dfm.dm_cmd))])
            self.v.ao_view.QComboBox_cmd.setCurrentIndex(self.dfm.current_cmd)

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

    def reset_galvo_positions(self):
        g_x, g_y = self.con_controller.get_galvo_positions()
        try:
            self.m.nucleo.set_galvo_position([g_x, g_y])
        except Exception as e:
            self.logg.error(f"Galvo Error: {e}")

    @QtCore.pyqtSlot(float, float)
    def set_galvo(self, voltx: float, volty: float):
        try:
            self.m.nucleo.set_galvo_position([voltx, volty])
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

    def set_camera_roi(self, key="imaging"):
        try:
            if self.cameras[key] == 0:
                x, y, nx, ny, bn = self.con_controller.get_thorcam_roi()
                self.m.cam_set[self.cameras[key]].set_roi(bn, bn, x, nx, y, ny)
            if self.cameras[key] == 1:
                expo = self.con_controller.get_webcam_expo()
                self.m.cam_set[self.cameras[key]].set_exposure(expo)
                x, y, nx, ny, bn = self.con_controller.get_webcam_roi()
                self.m.cam_set[self.cameras[key]].set_roi(x, y, nx, ny)
        except Exception as e:
            self.logg.error(f"Camera Error: {e}")

    # @QtCore.pyqtSlot()
    # def update_nucleo(self, sample_rate):
    #     self.update_galvo_scanner()

    @QtCore.pyqtSlot(str)
    def send_nucleo(self, mod: str):
        self.v.get_dialog()
        if mod == "video":
            self.run_task(task=self.send_nucleo_video)
        elif mod == "acquire":
            self.run_task(task=self.send_nucleo_acquisition)
        elif mod == "ao":
            self.run_task(task=self.send_nucleo_ao)
        else:
            raise ValueError("Invalid sequence mode")

    def send_nucleo_video(self):
        self.lasers = [0, 1]
        self.cameras["imaging"] = self.con_controller.get_imaging_camera()
        self.update_trigger_parameters("imaging")
        vd_mod = self.con_controller.get_live_mode()
        if vd_mod == "Wide Field":
            dtr, dchs, gtr, gchs = self.p.trigger.generate_digital_triggers(self.lasers, self.cameras["imaging"])
            self.m.nucleo.write_triggers(galvo_sequences=gtr, galvo_channels=[3, 4],
                                         digital_sequences=dtr, digital_channels=dchs, infinity=True)
        elif vd_mod == "Dot Scan":
            dtr, gtr, chs = self.p.trigger.generate_dot_scanning_triggers(self.lasers, self.cameras["imaging"])
            self.m.nucleo.t = dtr.shape[1] / self.m.nucleo.sample_rate
            print(self.m.nucleo.t)
            self.m.nucleo.write_triggers(galvo_sequences=gtr, galvo_channels=[3, 4],
                                         digital_sequences=dtr, digital_channels=chs, infinity=True)
        else:
            raise ValueError("Invalid video mode")

    def send_nucleo_acquisition(self):
        self.lasers = [0, 1]
        self.cameras["imaging"] = self.con_controller.get_imaging_camera()
        self.update_trigger_parameters("imaging")
        acq_mod = self.con_controller.get_acquisition_mode()
        if "Wide Field" in acq_mod:
            dtr, dchs, gtr, gchs = self.p.trigger.generate_digital_triggers(self.lasers, self.cameras["imaging"])
            self.m.nucleo.write_triggers(galvo_sequences=gtr, galvo_channels=[3, 4],
                                         digital_sequences=dtr, digital_channels=dchs, infinity=False)
        elif "Dot Scan" in acq_mod:
            self.m.cam_set[self.cameras["imaging"]].acq_num = 1
            dtr, gtr, chs = self.p.trigger.generate_dot_scanning_triggers(self.lasers, self.cameras["imaging"])
            self.m.nucleo.write_triggers(galvo_sequences=gtr, galvo_channels=[3, 4],
                                         digital_sequences=dtr, digital_channels=chs, infinity=False)
        elif "Line Scan" in acq_mod:
            dtr, dchs, gtr, gchs = self.p.trigger.generate_digital_triggers(self.lasers, self.cameras["imaging"])
            self.m.nucleo.write_triggers(galvo_sequences=gtr, galvo_channels=[3, 4],
                                         digital_sequences=dtr, digital_channels=dchs, infinity=False)
        else:
            raise ValueError("Invalid acquisition mode")

    def send_nucleo_ao(self):
        self.lasers = [0, 1]
        self.cameras["imaging"] = self.con_controller.get_imaging_camera()
        self.update_trigger_parameters("imaging")
        vd_mod = self.con_controller.get_live_mode()
        if vd_mod == "Wide Field":
            dtr, dchs, gtr, gchs = self.p.trigger.generate_digital_triggers(self.lasers, self.cameras["imaging"])
            self.m.nucleo.write_triggers(galvo_sequences=gtr, galvo_channels=[3, 4],
                                         digital_sequences=dtr, digital_channels=dchs, infinity=False)
        elif vd_mod == "Dot Scan":
            dtr, gtr, chs = self.p.trigger.generate_dot_scanning_triggers(self.lasers, self.cameras["imaging"])
            self.m.nucleo.write_triggers(galvo_sequences=gtr, galvo_channels=[3, 4],
                                         digital_sequences=dtr, digital_channels=chs, infinity=False)
        else:
            raise ValueError("Invalid video mode")

    @QtCore.pyqtSlot()
    def update_galvo_scanner(self):
        galvo_positions, galvo_ranges, dot_pos, offset, high_samples, galvo_positions_act, galvo_ranges_act, dot_pos_act, offset_act, high_samples_act = self.con_controller.get_galvo_scan_parameters()
        self.p.trigger.update_galvo_scan_parameters(origins=galvo_positions, ranges=galvo_ranges,
                                                    foci=dot_pos, offsets=offset, samples_high=high_samples,
                                                    origins_act=galvo_positions_act, ranges_act=galvo_ranges_act,
                                                    foci_act=dot_pos_act, offsets_act=offset_act, samples_high_act=high_samples_act)
        self.con_controller.display_frequency(self.p.trigger.frequency, self.p.trigger.frequency_act)

    def update_trigger_parameters(self, cam_key):
        """Ensure that the camera acquisition is fully set up before executing this function."""
        try:
            digital_starts, digital_ends = self.con_controller.get_digital_parameters()
            self.p.trigger.update_digital_parameters(digital_starts, digital_ends)
            self.update_galvo_scanner()
            self.logg.info(f"Trigger Updated")
        except Exception as e:
            self.logg.error(f"Trigger Error: {e}")

    def generate_live_triggers(self, cam_key):
        self.update_trigger_parameters(cam_key)
        return self.p.trigger.generate_digital_triggers(self.lasers, self.cameras[cam_key])

    def prepare_video(self):
        self.lasers = [0, 1]
        self.set_lasers(self.lasers)
        self.set_camera_roi("imaging")
        t = self.con_controller.get_thorcam_expo()
        self.m.cam_set[self.cameras["imaging"]].t_exposure = t
        self.m.cam_set[self.cameras["imaging"]].prepare_live()
        self.setup_video_thread()

    def start_video(self, vm):
        try:
            self.prepare_video()
        except Exception as e:
            self.logg.error(f"Error preparing imaging video: {e}")
            self.m.nucleo.stop_triggers()
            self.lasers_off()
            return
        try:
            self.m.cam_set[self.cameras["imaging"]].start_live()
            self.m.nucleo.run_triggers()
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
            self.m.nucleo.stop_triggers()
            self.m.cam_set[self.cameras["imaging"]].stop_live()
            self.lasers_off()
            if vm == "Dot Scan":
                self.reset_galvo_positions()
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
            self.setup_fft_thread()
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
            self.setup_plot_thread()
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
            dtr, dch, gtr, gch = self.generate_live_triggers("imaging")
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
            self.run_widefield(acq_num)
        elif acq_mod == "Dot Scan 2D":
            self.run_dot_scan(acq_num)
        elif acq_mod == "Line Scan 2D":
            self.run_line_scan(acq_num)
        else:
            self.logg.error(f"Invalid video mode")

    @QtCore.pyqtSlot(str, np.ndarray, list)
    def save_data(self, tm: str, d: np.ndarray, idx: list):
        fn = self.v.get_file_dialog()
        if fn is not None:
            fd = os.path.join(self.data_folder, tm + '_' + fn)
        else:
            fd = os.path.join(self.data_folder, tm)
        pixel_size = self.pixel_sizes[self.cameras["imaging"]]
        tf.imwrite(str(fd + r".tif"), data=d, metadata={"pixel_size": (pixel_size, pixel_size)})
        with pd.ExcelWriter(str(fd + r"_metadata.xlsx"), engine="openpyxl") as writer:
            if len(idx):
                df_idx = pd.DataFrame(idx, columns=["acquisition_sequence"])
                df_idx.to_excel(writer, sheet_name="acquisition_sequence", index=False)

    @QtCore.pyqtSlot(str, np.ndarray, list)
    def save_data_stack(self, tm: str, d: np.ndarray, idx: list):
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

    def prepare_widefield(self):
        # self.lasers = self.con_controller.get_lasers()
        self.set_lasers(self.lasers)
        # self.cameras["imaging"] = self.con_controller.get_imaging_camera()
        self.set_camera_roi("imaging")
        self.m.cam_set[self.cameras["imaging"]].acq_num = 1
        self.m.cam_set[self.cameras["imaging"]].prepare_data_acquisition()
        # self.update_trigger_parameters("imaging")
        # dtr, sw, ptr, dch, pch, pos = self.p.trigger.generate_piezo_scan(self.lasers, self.cameras["imaging"])
        # self.m.cam_set[self.cameras["imaging"]].acq_num = pos
        # self.m.nucleo.set_piezo_position(pos=[ptr[0]], indices=[2])
        # self.m.nucleo.write_triggers(piezo_sequences=ptr, piezo_channels=pch,
        #                              digital_sequences=dtr, digital_channels=dch, infinity=False)

    def widefield(self):
        data = []
        for n in range(self.acq_num):
            self.v.dialog_text.setText(f"Acquisition # {n+1}")
            self.v.refresh_gui()
            try:
                self.prepare_widefield()
            except Exception as e:
                self.logg.error(f"Error preparing widefield zstack: {e}")
                return
            try:
                self.m.cam_set[self.cameras["imaging"]].start_data_acquisition()
                time.sleep(0.02)
                self.m.nucleo.run_triggers()
                time.sleep(0.3)
                self.dm_cmd_ind = self.m.dm.current_cmd
                data.append(self.m.cam_set[self.cameras["imaging"]].get_data())
                l = list(self.m.cam_set[self.cameras["imaging"]].data.ind_list)
            except Exception as e:
                self.finish_widefield()
                self.logg.error(f"Error running widefield zstack: {e}")
                return
            self.finish_widefield()
        self.sada.emit(time.strftime("%Y%m%d%H%M%S") + '_widefield', np.array(data), l)

    def finish_widefield(self):
        try:
            self.m.cam_set[self.cameras["imaging"]].stop_data_acquisition()
            self.lasers_off()
            self.m.nucleo.stop_triggers()
            self.logg.info("Widefield image stack acquired")
        except Exception as e:
            self.logg.error(f"Error stopping widefield zstack: {e}")

    def run_widefield(self, n: int):
        self.v.get_dialog()
        self.acq_num = n
        self.run_task(task=self.widefield)

    def prepare_dot_scan(self):
        # self.lasers = self.con_controller.get_lasers()
        self.set_lasers(self.lasers)
        # self.cameras["imaging"] = self.con_controller.get_imaging_camera()
        self.set_camera_roi("imaging")
        self.m.cam_set[self.cameras["imaging"]].acq_num = 1
        self.m.cam_set[self.cameras["imaging"]].prepare_data_acquisition()
        # self.update_trigger_parameters("imaging")
        # gtr, ptr, dtr, chs, pos = self.p.trigger.generate_dotsacn_resolft_2d(self.lasers, self.cameras["imaging"])
        # self.m.cam_set[self.cameras["imaging"]].acq_num = pos
        # self.m.nucleo.write_triggers(piezo_sequences=ptr, piezo_channels=[0, 1],
        #                           galvo_sequences=gtr, galvo_channels=[0, 1, 2],
        #                           digital_sequences=dtr, digital_channels=chs)

    def dot_scan(self):
        try:
            self.prepare_dot_scan()
        except Exception as e:
            self.logg.error(f"Error preparing galvo scanning: {e}")
            return
        try:
            self.m.cam_set[self.cameras["imaging"]].start_data_acquisition()
            time.sleep(0.02)
            self.m.nucleo.run_triggers()
            time.sleep(1 + self.m.nucleo.sequence_length * 10 / 1e6)
            self.dm_cmd_ind = self.m.dm.current_cmd
            self.sada.emit(time.strftime("%Y%m%d%H%M%S") + '_dot_scanning',
                           self.m.cam_set[self.cameras["imaging"]].get_data(),
                           list(self.m.cam_set[self.cameras["imaging"]].data.ind_list))
        except Exception as e:
            self.finish_dot_scan()
            self.logg.error(f"Error running dot scanning: {e}")
            return
        self.finish_dot_scan()

    def finish_dot_scan(self):
        try:
            self.m.cam_set[self.cameras["imaging"]].stop_data_acquisition()
            self.m.nucleo.stop_triggers()
            self.lasers_off()
            self.logg.info("Dot scanning image acquired")
        except Exception as e:
            self.logg.error(f"Error stopping dot scanning: {e}")

    def run_dot_scan(self, n: int):
        self.v.get_dialog()
        self.run_task(task=self.dot_scan, iteration=n)

    def prepare_line_scan(self):
        dot_stops = [o_ + r_ / 2 for (o_, r_) in zip(self.p.trigger.galvo_origins, self.p.trigger.dot_ranges)]
        x_pos = np.arange(self.p.trigger.dot_starts[0], dot_stops[0] + 0.0001, self.p.trigger.dot_step_v)
        y_pos = np.arange(self.p.trigger.dot_starts[1], dot_stops[1], self.p.trigger.dot_step_y)
        pos = x_pos.shape[0] * y_pos.shape[0]
        gtrs = []
        for xp in x_pos:
            for yp in y_pos:
                gtr = np.ones((2, self.m.nucleo.sequence_length), dtype=np.uint16)
                gtr[0] *= int(xp * 4096 / 3.3)
                gtr[1] *= int(yp * 4096 / 3.3)
                gtrs.append(gtr)
        # print(self.p.trigger.galvo_origins)
        # print(self.p.trigger.dot_ranges)
        # print(self.p.trigger.dot_starts)
        # print(self.p.trigger.dot_step_v, self.p.trigger.dot_step_y)
        # print(pos)
        # print(x_pos)
        # print(y_pos)
        # self.lasers = self.con_controller.get_lasers()
        self.set_lasers(self.lasers)
        # self.cameras["imaging"] = self.con_controller.get_imaging_camera()
        self.set_camera_roi("imaging")
        self.m.cam_set[self.cameras["imaging"]].acq_num = pos
        self.m.cam_set[self.cameras["imaging"]].prepare_data_acquisition()
        # self.update_trigger_parameters("imaging")
        # gtr, ptr, dtr, chs, pos = self.p.trigger.generate_dotsacn_resolft_2d(self.lasers, self.cameras["imaging"])
        # self.m.cam_set[self.cameras["imaging"]].acq_num = pos
        # self.m.nucleo.write_triggers(piezo_sequences=ptr, piezo_channels=[0, 1],
        #                           galvo_sequences=gtr, galvo_channels=[0, 1, 2],
        #                           digital_sequences=dtr, digital_channels=chs)
        return gtrs

    def line_scan(self):
        try:
            gtrs = self.prepare_line_scan()
        except Exception as e:
            self.logg.error(f"Error preparing galvo line scanning: {e}")
            return
        try:
            self.m.cam_set[self.cameras["imaging"]].start_data_acquisition()
            for gtr in gtrs:
                # print(gtr[:, 0])
                self.m.nucleo.write_triggers(galvo_sequences=gtr, galvo_channels=[3, 4], infinity=False)
                time.sleep(0.02)
                self.m.nucleo.run_triggers()
                time.sleep(self.m.nucleo.sequence_length * 10 / 1e6)
            self.dm_cmd_ind = self.m.dm.current_cmd
            self.sada.emit(time.strftime("%Y%m%d%H%M%S") + '_line_scanning',
                                   self.m.cam_set[self.cameras["imaging"]].get_data(),
                                   list(self.m.cam_set[self.cameras["imaging"]].data.ind_list))
        except Exception as e:
            self.finish_line_scan()
            self.logg.error(f"Error running line scanning: {e}")
            return
        self.finish_line_scan()

    def finish_line_scan(self):
        try:
            self.m.cam_set[self.cameras["imaging"]].stop_data_acquisition()
            self.m.nucleo.stop_triggers()
            self.lasers_off()
            self.logg.info("Line scanning image acquired")
        except Exception as e:
            self.logg.error(f"Error stopping line scanning: {e}")

    def run_line_scan(self, n: int):
        self.v.get_dialog()
        self.run_task(task=self.line_scan, iteration=n)

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
            md = self.ao_controller.get_wfs_method()
            indz, amp = self.ao_controller.get_zernike_mode()
            if factory:
                self.dfm.temp_cmd.append(self.dfm.cmd_add([i * amp for i in self.dfm.z2c[indz]], self.dfm.dm_cmd[self.dfm.current_cmd]))
                self.dfm.set_dm(self.dfm.temp_cmd[-1])
            else:
                self.dfm.temp_cmd.append(self.dfm.cmd_add(self.dfm.get_zernike_cmd(indz, amp, md), self.dfm.dm_cmd[self.dfm.current_cmd]))
                self.dfm.set_dm(self.dfm.temp_cmd[-1])
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
        parameters = self.ao_controller.get_parameters_foc()
        self.p.shwfsr.pixel_size = self.pixel_sizes[self.cameras["wfs"]] / 1000
        self.p.shwfsr.update_parameters(parameters)
        self.logg.info('SHWFS parameter updated')

    def prepare_img_wfs(self):
        # self.lasers = self.con_controller.get_lasers()
        # self.set_lasers(self.lasers)
        self.cameras["wfs"] = self.ao_controller.get_wfs_camera()
        self.set_camera_roi("wfs")
        self.set_img_wfs(self.cameras["wfs"])
        self.m.cam_set[self.cameras["wfs"]].prepare_live()
        # self.update_trigger_parameters("wfs")
        # dtr, sw, chs = self.p.trigger.generate_digital_triggers(self.lasers, self.cameras["wfs"])
        # self.m.nucleo.write_triggers(digital_sequences=dtr, digital_channels=chs, finite=False)
        self.setup_wfs_thread()

    def start_img_wfs(self):
        try:
            self.prepare_img_wfs()
        except Exception as e:
            self.logg.error(f"Error preparing wfs: {e}")
            self.stop_img_wfs()
        try:
            pw = self.con_controller.get_cobolt_laser_power("488")
            self.m.cam_set[self.cameras["wfs"]].start_live()
            self.set_laser(["488"], 1, pw[0])
            # self.m.nucleo.run_triggers()
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
            # self.m.nucleo.stop_triggers()
            self.lasers_off()
            self.m.cam_set[self.cameras["wfs"]].stop_live()
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
            self.p.shwfsr.method = self.ao_controller.get_gradient_method()
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
        md = self.ao_controller.get_gradient_method()
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
        # self.lasers = self.con_controller.get_lasers()
        # self.set_lasers(self.lasers)
        self.cameras["wfs"] = self.ao_controller.get_wfs_camera()
        self.set_camera_roi("wfs")
        self.m.cam_set[self.cameras["wfs"]].prepare_live()
        self.set_img_wfs(self.cameras["wfs"])
        # self.update_trigger_parameters("wfs")
        # wfs = self.ao_controller.get_dm_selection()
        # dtr, chs = self.p.trigger.generate_digital_triggers(self.lasers, self.cameras["wfs"])
        # self.m.nucleo.write_triggers(digital_sequences=dtr, digital_channels=chs)

    def read_tis_image(self, n):
        m = self.m.cam_set[self.cameras["wfs"]].data.image_counter
        while m == n:
            m = self.m.cam_set[self.cameras["wfs"]].data.image_counter
        dat = self.m.cam_set[self.cameras["wfs"]].get_last_image()
        return dat, m

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
            pw = self.con_controller.get_cobolt_laser_power("488")
            self.set_laser(["488"], 1, pw[0])
            num = self.m.cam_set[self.cameras["wfs"]].data.image_counter
            for i in range(self.dfm.n_actuator):
                shimg = []
                self.v.dialog_text.setText(f"actuator {i}")
                values = [0.] * self.dfm.n_actuator
                self.dfm.set_dm(values)
                time.sleep(0.2)
                # self.m.nucleo.run_triggers()
                # time.sleep(0.08)
                dat, num = self.read_tis_image(num)
                shimg.append(dat)
                # self.m.nucleo.stop_triggers(_close=False)
                values[i] = amp
                self.dfm.set_dm(values)
                time.sleep(0.2)
                # self.m.nucleo.run_triggers()
                # time.sleep(0.08)
                dat, num = self.read_tis_image(num)
                shimg.append(dat)
                # self.m.nucleo.stop_triggers(_close=False)
                values = [0.] * self.dfm.n_actuator
                self.dfm.set_dm(values)
                time.sleep(0.2)
                # self.m.nucleo.run_triggers()
                # time.sleep(0.08)
                dat, num = self.read_tis_image(num)
                shimg.append(dat)
                # self.m.nucleo.stop_triggers(_close=False)
                values[i] = - amp
                self.dfm.set_dm(values)
                time.sleep(0.2)
                # self.m.nucleo.run_triggers()
                # time.sleep(0.08)
                dat, num = self.read_tis_image(num)
                shimg.append(dat)
                # self.m.nucleo.stop_triggers(_close=False)
                tf.imwrite(fd + r'/' + 'actuator_' + str(i) + '_push_' + str(amp) + '.tif', np.asarray(shimg))
        except Exception as e:
            self.logg.error(f"Error running influence function: {e}")
            self.finish_influence_function()
            return
        try:
            self.v.dialog_text.setText(f"computing influence function")
            # dmn = self.v.ao_view.QComboBox_dms.currentText()
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
            # self.m.nucleo.stop_triggers()
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
        dtr, dchs, gtr, gchs = self.p.trigger.generate_digital_triggers(self.lasers, self.cameras["wfs"])
        self.m.nucleo.write_triggers(digital_sequences=dtr, digital_channels=dchs, finite=True)

    def close_loop_correction(self):
        try:
            self.m.nucleo.run_triggers()
            time.sleep(0.08)
            self.p.shwfsr.meas = self.m.cam_set[self.cameras["wfs"]].get_last_image()
            self.m.nucleo.stop_triggers(_close=False)
            md = self.ao_controller.get_wfs_method()
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
            self.m.nucleo.stop_triggers()
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
        self.lasers = [0, 1]
        self.set_lasers(self.lasers)
        self.cameras["imaging"] = self.con_controller.get_imaging_camera()
        self.set_camera_roi("imaging")
        self.m.cam_set[self.cameras["imaging"]].prepare_live()

    def sensorless_iteration(self, dms):
        ims = []
        for dmsp in dms:
            self.dfm.set_dm(dmsp)
            time.sleep(0.016)
            self.m.nucleo.run_triggers()
            time.sleep(self.m.nucleo.sequence_length * 10 / 1e6)
            ims.append(self.m.cam_set[self.cameras["imaging"]].get_last_image())
        return ims

    def sensorless_iterations(self):
        try:
            lpr, hpr, slf, mf, err = self.ao_controller.get_ao_parameters()
            if mf == 'Mask(Intensity)':
                msk = self.view_controller.get_image_data(5)
            name = time.strftime("%Y%m%d_%H%M%S_") + self.dfm.dm_serial + '_ao_iterations_' + mf
            new_folder = os.path.join(self.data_folder, name)
            os.makedirs(new_folder, exist_ok=True)
            self.logg.info(f'Directory {new_folder} has been created successfully.')
        except Exception as e:
            self.logg.error(f'Error creating directory for sensorless iteration: {e}')
            return
        try:
            mode_start, mode_stop, amp_start, amp_step, amp_step_number = self.ao_controller.get_ao_iteration()
            md = self.ao_controller.get_wfs_method()
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
                    self.m.nucleo.run_triggers()
                    time.sleep(self.m.nucleo.sequence_length * 10 / 1e6)
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
                self.m.nucleo.run_triggers()
                time.sleep(self.m.nucleo.sequence_length * 10 / 1e6)
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
            self.m.nucleo.run_triggers()
            time.sleep(self.m.nucleo.sequence_length * 10 / 1e6)
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
            self.m.nucleo.stop_triggers()
            self.m.cam_set[self.cameras["imaging"]].stop_live()
            self.logg.info("sensorless AO finished")
        except Exception as e:
            self.logg.error(f"Finish Sensorless AO Error: {e}")

    @QtCore.pyqtSlot()
    def run_sensorless_iteration(self):
        self.v.get_dialog()
        try:
            self.prepare_sensorless_iteration()
        except Exception as e:
            self.logg.error(f"Prepare sensorless iteration Error: {e}")
            return
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
            md = self.ao_controller.get_wfs_method()
            amprange = np.linspace(amp_start, -amp_start, amp_step_number + 1)
            cmd = self.dfm.dm_cmd[self.dfm.current_cmd]
            self.m.cam_set[self.cameras["imaging"]].start_live()
            time.sleep(0.08)
            self.logg.info("Automated sensorless AO iterations start")
            self.dfm.set_dm(cmd)
            time.sleep(0.016)
            tpd = []
            for _ in range(16):
                self.m.nucleo.run_triggers()
                time.sleep(0.032)
                self.m.nucleo.stop_triggers(_close=False)
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
                        self.m.nucleo.run_triggers()
                        time.sleep(0.032)
                        self.m.nucleo.stop_triggers(_close=False)
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
            md = self.ao_controller.get_wfs_method()
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
                self.m.nucleo.run_triggers()
                time.sleep(0.032)
                self.m.nucleo.stop_triggers(_close=False)
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
            md = self.ao_controller.get_wfs_method()
            za = []
            mv = []
            zp = [0] * self.dfm.n_zernike
            cmd = self.dfm.dm_cmd[self.dfm.current_cmd]
            self.m.cam_set[self.cameras["imaging"]].start_live()
            time.sleep(0.1)
            self.logg.info("Automated sensorless AO iterations start")
            self.dfm.set_dm(cmd)
            time.sleep(0.016)
            self.m.nucleo.run_triggers()
            time.sleep(0.032)
            self.m.nucleo.stop_triggers(_close=False)
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
            self.m.nucleo.run_triggers()
            time.sleep(0.032)
            self.m.nucleo.stop_triggers(_close=False)
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
        dtr, sw, chs = self.p.trigger.generate_digital_triggers(self.lasers, self.cameras["wfs"])
        self.m.nucleo.write_triggers(digital_sequences=dtr, digital_channels=chs, finite=True)

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
            mtd = self.ao_controller.get_wfs_method()
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
                self.m.nucleo.run_triggers()
                time.sleep(0.08)
                data.append(self.m.cam_set[self.cameras["wfs"]].get_last_image())
                self.m.nucleo.stop_triggers(_close=False)
                amps[:, 0] = np.random.rand(modes.shape[0]) / 128
                for m, mode in enumerate(modes):
                    amp = amps[m, 0]
                    cmd = self.dfm.cmd_add(self.dfm.get_zernike_cmd(mode, amp, method=mtd), cmd)
                self.dfm.set_dm(cmd)
                time.sleep(0.02)
                self.m.nucleo.run_triggers()
                time.sleep(0.08)
                data.append(self.m.cam_set[self.cameras["wfs"]].get_last_image())
                self.m.nucleo.stop_triggers(_close=False)
                self.p.shwfsr.ref = data[0]
                self.p.shwfsr.meas = data[1]
                md = self.ao_controller.get_gradient_method()
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
            self.m.nucleo.stop_triggers()
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
