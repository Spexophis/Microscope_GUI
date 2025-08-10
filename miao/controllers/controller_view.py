# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


class ViewController:

    def __init__(self, view):
        self.v = view

    def plot_main(self, data, layer=0):
        self.v.show_image(self.v.img_layers[layer], data)

    def plot_sh(self, data, layer=1):
        self.v.show_image(self.v.img_layers[layer], data)

    def plot_fft(self, data, layer=4):
        self.v.show_image(self.v.img_layers[layer], data)

    def plot_shb(self, data, layer=5):
        self.v.show_image(self.v.img_layers[layer], data)

    def plot_wf(self, data, layer=6):
        self.v.show_image(self.v.img_layers[layer], data)

    def plot_msk(self, data, layer=7):
        self.v.show_image(self.v.img_layers[layer], data)

    def get_image_data(self, layer=1):
        return self.v.get_image(self.v.img_layers[layer])

    def plot(self, data, x=None, s=None):
        self.v.plot(data, x, s)

    def plot_update(self, data, x=None, s=None):
        self.v.update_plot(data, x, s)
