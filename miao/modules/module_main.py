from miao.modules import module_andorixon
from miao.modules import module_deformablemirror
from miao.modules import module_hamamatsuorchflash
from miao.modules import module_thorlabcam
from miao.modules import module_slm_qxga
# from miao.modules import module_slm_lcos
from miao.modules import module_coboltlaser
from miao.modules import module_mcldeck
from miao.modules import module_mclpiezo
from miao.modules import module_nidaq
from miao.modules import module_tis


class MainModule:

    def __init__(self, config, logg, path):
        self.config = config
        self.logg = logg
        self.data_folder = path
        self.cam_set = {}
        try:
            self.ccdcam = module_andorixon.EMCCDCamera(logg=self.logg.error_log)
            self.cam_set[0] = self.ccdcam
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.scmoscam = module_hamamatsuorchflash.HamamatsuCamera(logg=self.logg.error_log)
            self.cam_set[1] = self.scmoscam
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.thorcam = module_thorlabcam.ThorCMOS(logg=self.logg.error_log)
            self.cam_set[2] = self.thorcam
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.tiscam = module_tis.TISCamera(logg=self.logg.error_log)
            self.cam_set[3] = self.tiscam
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        self.dm = {}
        for key in self.config.configs["Adaptive Optics"]["Deformable Mirrors"].keys():
            try:
                self.dm[key] = module_deformablemirror.DeformableMirror(name=key, logg=self.logg.error_log,
                                                                        config=self.config, path=self.data_folder)
            except Exception as e:
                self.logg.error_log.error(f"{e}")
        self.slm = {}
        try:
            self.slm["Binary"] = module_slm_qxga.QXGA(logg=self.logg.error_log, config=self.config)
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        # try:
        #     self.slm["Phase"] = module_slm_lcos.LCOS(logg=self.logg.error_log, config=self.config)
        # except Exception as e:
        #     self.logg.error_log.error(f"{e}")
        try:
            self.laser = module_coboltlaser.CoboltLaser(logg=self.logg.error_log, config=self.config)
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.daq = module_nidaq.NIDAQ(logg=self.logg.error_log)
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.md = module_mcldeck.MCLMicroDrive(logg=self.logg.error_log)
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.pz = module_mclpiezo.MCLNanoDrive(logg=self.logg.error_log)
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        self.logg.error_log.info("Finish initiating devices")

    def close(self):
        try:
            self.ccdcam.close()
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.scmoscam.close()
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.thorcam.close()
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.tiscam.close()
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.laser.close()
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            for key in self.dm.keys():
                self.dm[key].close()
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            for key in self.slm.keys():
                self.dm[key].close()
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.daq.close()
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.md.close()
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.pz.close()
        except Exception as e:
            self.logg.error_log.error(f"{e}")
