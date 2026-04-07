from miao.modules import module_hamamtsu_scmos
from miao.modules import module_tis
from miao.modules import module_coboltlaser
from miao.modules import module_deformablemirror
from miao.modules import module_nucleo
from miao.modules import module_piezo

class MainModule:

    def __init__(self, config, logg, path):
        self.config = config
        self.logg = logg
        self.data_folder = path
        self.cam_set = {}
        try:
            self.hcam = module_hamamtsu_scmos.HamamatsuCamera(logg=self.logg.error_log)
            self.cam_set[0] = self.hcam
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.tiscam = module_tis.TISCamera(logg=self.logg.error_log)
            self.cam_set[1] = self.tiscam
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.laser = module_coboltlaser.CoboltLaser(logg=self.logg.error_log, config=self.config)
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        key = self.config.configs["Adaptive Optics"]["Deformable Mirrors"].keys()
        try:
            self.dm = module_deformablemirror.DeformableMirror(name=list(key)[0], logg=self.logg.error_log,
                                                               config=self.config, path=self.data_folder)
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.nucleo = module_nucleo.NucleoBoards(logg=self.logg.error_log)
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.pz = module_piezo.KinesisPiezo(logg=self.logg.error_log, config=self.config)
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        self.logg.error_log.info("Finish initiating devices")

    def close(self):
        try:
            for key in self.cam_set.keys():
                self.cam_set[key].close()
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.laser.close()
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.dm.close()
        except Exception as e:
            self.logg.error_log.error(f"{e}")
        try:
            self.pz.close()
        except Exception as e:
            self.logg.error_log.error(f"{e}")
