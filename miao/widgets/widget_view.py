import matplotlib

matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

plt.style.use('dark_background')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
from miao.utilities import customized_widgets as cw
from miao.utilities import napari_tools
from PyQt5 import QtWidgets, QtCore


class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, dpi=512):
        fig = Figure(dpi=dpi)
        self.axes = fig.add_subplot(111)
        fig.set_facecolor("none")
        super(MplCanvas, self).__init__(fig)
        self.setStyleSheet("background-color: #242424")


class ViewWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_ui()
        self._set_napari_layers()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
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
            "view": cw.create_dock("Image"),
            "plot": cw.create_dock("Profile")
        }

    def _create_widgets(self):
        self.widgets = {
            "view": self._create_view_widgets(),
            "plot": self._create_plot_widgets()
        }

    def _create_view_widgets(self):
        layout_view = QtWidgets.QVBoxLayout()
        napari_tools.addNapariGrayclipColormap()
        self.napariViewer = napari_tools.EmbeddedNapari()
        layout_view.addWidget(self.napariViewer.get_widget())
        return layout_view

    def _create_plot_widgets(self):
        layout_plot = QtWidgets.QGridLayout()
        self.canvas_show = MplCanvas(self, dpi=64)
        self.canvas_plot = MplCanvas(self, dpi=64)
        toolbar = NavigationToolbar(self.canvas_plot)
        layout_plot.addWidget(toolbar, 0, 0, 1, 2)
        layout_plot.addWidget(self.canvas_show, 1, 0, 1, 1)
        layout_plot.addWidget(self.canvas_plot, 1, 1, 1, 1)
        return layout_plot

    def _set_napari_layers(self):
        self.napari_layers = {}
        self.img_layers = {0: "Andor EMCCD", 1: "Hamamatsu sCMOS", 3: "DMK 33UX250", 4: "FFT",
                           5: "ShackHartmann(Base)", 6: "Wavefront", 7: "Array Mask"}
        for name in reversed(list(self.img_layers.values())):
            self.napari_layers[name] = self.add_napari_layer(name)

    def add_napari_layer(self, name):
        return self.napariViewer.add_image(np.zeros((1024, 1024)), rgb=False, name=name, blending='additive',
                                           colormap=None, protected=True)

    def show_image(self, name, im):
        if isinstance(im, np.ndarray):
            self.napari_layers[name].data = im

    def get_image(self, name):
        return self.napari_layers[name].data

    def plot_image(self, data, axis_arrays=None, axis_labels=None):
        if axis_arrays is not None:
            self.canvas_show.axes.imshow(X=data, vmin=data.min(), vmax=data.max(),
                                         extent=(axis_arrays[0].min(), axis_arrays[0].max(),
                                                 axis_arrays[1].max(), axis_arrays[1].min()),
                                         interpolation='none')
        else:
            self.canvas_show.axes.imshow(X=data, vmin=data.min(), vmax=data.max(), interpolation='none')
        if axis_labels is not None:
            plt.xlabel(axis_labels[0])
            plt.ylabel(axis_labels[1])
        self.canvas_show.draw()

    def plot(self, data, x=None, sp=None):
        if x is not None:
            self.canvas_plot.axes.plot(x, data)
        else:
            self.canvas_plot.axes.plot(data)
        if sp is not None:
            self.canvas_plot.axes.axhline(y=sp, color='r', linestyle='--')
        self.canvas_plot.axes.grid(True)
        self.canvas_plot.draw()

    def update_plot(self, data, x=None, sp=None):
        self.canvas_plot.axes.cla()
        if x is not None:
            self.canvas_plot.axes.plot(x, data)
        else:
            self.canvas_plot.axes.plot(data)
        if sp is not None:
            self.canvas_plot.axes.axhline(y=sp, color='r', linestyle='--')
        self.canvas_plot.axes.grid(True)
        self.canvas_plot.draw()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = ViewWidget()
    window.show()
    sys.exit(app.exec_())
