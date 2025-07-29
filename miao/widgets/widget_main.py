# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


import os

from miao.widgets import widget_ao, widget_con, widget_view
from miao.utilities import customized_widgets as cw

from PyQt5 import QtWidgets, QtCore


class MainWidget(QtWidgets.QMainWindow):
    Signal_quit = QtCore.pyqtSignal()
    Signal_interrupt = QtCore.pyqtSignal()

    def __init__(self, config, logg, path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = config
        self.logg = logg.error_log
        self.data_folder = path

        self.con_view = widget_con.ConWidget(config, logg, path)
        self.view_view = widget_view.ViewWidget()
        self.ao_view = widget_ao.AOWidget(config, logg, path)

        self.dock_con = self.create_dock_widget(self.con_view)
        self.dock_ao = self.create_dock_widget(self.ao_view)

        self.setCentralWidget(self.view_view)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dock_con)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock_ao)

        self.dialog, self.dialog_text = None, None

        self.setWindowTitle("Microscope Control")
        self.setStyleSheet("background-color: #121212; color: #FFFFFF")

        self.create_menu()

        self.logg.info("Finish setting up widgets")

    def create_dock_widget(self, widget):
        dock_widget = QtWidgets.QDockWidget(self)
        dock_widget.setWidget(widget)
        dock_widget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        dock_widget.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable |
                                QtWidgets.QDockWidget.DockWidgetFloatable)
        dock_widget.setTitleBarWidget(CustomDockTitleBar(dock_widget))
        return dock_widget

    def create_menu(self):
        menubar = self.menuBar()
        view_menu = menubar.addMenu('View')

        show_con_action = QtWidgets.QAction('Show Control Widget', self)
        show_con_action.triggered.connect(lambda: self.dock_con.show())
        view_menu.addAction(show_con_action)

        show_ao_action = QtWidgets.QAction('Show AO Widget', self)
        show_ao_action.triggered.connect(lambda: self.dock_ao.show())
        view_menu.addAction(show_ao_action)

    def closeEvent(self, event, **kwargs):
        self.Signal_quit.emit()
        self.con_view.save_spinbox_values()
        self.ao_view.save_spinbox_values()
        super().closeEvent(event)

    def get_dialog(self, interrupt=False):
        self.dialog, self.dialog_text = cw.create_dialog(labtex=True, interrupt=interrupt)
        self.dialog.setModal(True)
        self.dialog.show()
        self.dialog_text.setText(f"Task is running, please wait...")
        self.refresh_gui()

    def get_file_dialog(self, sw="Save File"):
        file_dialog = cw.FileDialogWidget(name=sw, file_filter="All Files (*)", default_dir=self.data_folder)
        if file_dialog.exec_() == QtWidgets.QFileDialog.Accepted:
            selected_file = file_dialog.selectedFiles()
            if selected_file:
                return os.path.basename(selected_file[0])
            else:
                return None

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.Signal_interrupt.emit()
        elif event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            return
        else:
            super().keyPressEvent(event)

    @staticmethod
    def refresh_gui():
        QtWidgets.QApplication.processEvents()


class CustomDockTitleBar(QtWidgets.QWidget):
    def __init__(self, dock_widget):
        super().__init__()
        self.dock_widget = dock_widget
        self.init_ui()

    def init_ui(self):
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.label = QtWidgets.QLabel(self.dock_widget.windowTitle())
        self.layout.addWidget(self.label)

        self.minimize_button = QtWidgets.QToolButton()
        self.minimize_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_TitleBarMinButton))
        self.minimize_button.clicked.connect(self.minimize_dock_widget)
        self.layout.addWidget(self.minimize_button)

    def minimize_dock_widget(self):
        self.dock_widget.setFloating(False)
        self.dock_widget.hide()


if __name__ == "__main__":
    import sys
    from miao.utilities import configurations, error_log
    import time

    app = QtWidgets.QApplication(sys.argv)
    cfd = r"C:\\Users\\Public\\Documents\\Data\\config_files\\microscope_configurations_polarization_scan.json"
    cfg = configurations.MicroscopeConfiguration(cfd)
    pth = f"{cfg.configs['Data Path']}\\{time.strftime('%Y%m%d')}"
    try:
        os.makedirs(pth, exist_ok=True)
        print(f'Directory {pth} has been created successfully.')
    except Exception as e:
        print(f'Error creating directory {pth}: {e}')
    log_file = os.path.join(pth, time.strftime("%H%M%S") + 'app.log')
    lg = error_log.ErrorLog(log_file)

    main_widget = MainWidget(cfg, lg, pth)
    main_widget.show()
    sys.exit(app.exec_())
