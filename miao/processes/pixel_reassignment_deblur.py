# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


import numpy as np
import tifffile as tf
from scipy.interpolate import RectBivariateSpline
from scipy.ndimage import gaussian_filter, convolve


class ImageReconstruction:

    def __init__(self):
        self.gain_value = 1.4
        self.scale_factor = 1
        self.na = 1.4
        self.wl = 0.5
        self.pixel_size = 0.081
        self.window_radius = int(1 * np.ceil((self.wl / (2 * self.na)) / self.pixel_size))

    def load_data(self, fn=None, img=None):
        if fn is not None:
            self.I_in = tf.imread(fn)
        if img is not None:
            self.I_in = img

    def calculate_coordinates(self):
        self.number_row_initial, self.number_column_initial = self.I_in.shape
        self.number_row_scaleup = int(self.scale_factor * self.number_row_initial)
        self.number_column_scaleup = int(self.scale_factor * self.number_column_initial)
        self.x0 = np.linspace(-0.5, 0.5, self.number_column_initial)
        self.y0 = np.linspace(-0.5, 0.5, self.number_row_initial)
        self.X0, self.Y0 = np.meshgrid(self.x0, self.y0)
        self.x = np.linspace(-0.5, 0.5, self.number_column_scaleup)
        self.y = np.linspace(-0.5, 0.5, self.number_row_scaleup)
        self.X, self.Y = np.meshgrid(self.x, self.y)

    def dpr_single(self):
        self.single_frame_I_in = self.I_in - np.min(self.I_in)
        self.local_minimum = np.zeros_like(self.single_frame_I_in)
        self.single_frame_I_in_localmin = np.zeros_like(self.single_frame_I_in)

        for u in range(self.number_row_initial):
            for v in range(self.number_column_initial):
                sub_window = self.single_frame_I_in[
                             max(0, u - self.window_radius):min(self.number_row_initial, u + self.window_radius + 1),
                             max(0, v - self.window_radius):min(self.number_column_initial, v + self.window_radius + 1)
                             ]
                self.local_minimum[u, v] = np.min(sub_window)
                self.single_frame_I_in_localmin[u, v] = self.single_frame_I_in[u, v] - self.local_minimum[u, v]

    def upscale_interp(self):
        interp_localmin = RectBivariateSpline(self.y0, self.x0, self.single_frame_I_in_localmin)
        single_frame_localmin_magnified = interp_localmin(self.y, self.x, grid=True)
        single_frame_localmin_magnified[single_frame_localmin_magnified < 0] = 0
        self.single_frame_localmin_magnified = np.pad(single_frame_localmin_magnified, ((10, 10), (10, 10)),
                                                      mode='constant')

        interp_in = RectBivariateSpline(self.y0, self.x0, self.single_frame_I_in)
        single_frame_I_magnified = interp_in(self.y, self.x, grid=True)
        single_frame_I_magnified[single_frame_I_magnified < 0] = 0
        self.single_frame_I_magnified = np.pad(single_frame_I_magnified, ((10, 10), (10, 10)), mode='constant')

        self.number_row, self.number_column = single_frame_I_magnified.shape

    def local_norm(self):
        self.I_normalized = self.single_frame_localmin_magnified / (
                    gaussian_filter(self.single_frame_localmin_magnified, 8) + 1e-5)

    def calculate_gradients(self):
        sobelX = np.array([[1, 0, -1], [2, 0, -2], [1, 0, -1]])
        sobelY = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]])
        gradient_y = convolve(self.I_normalized, sobelX, mode='reflect')
        gradient_x = convolve(self.I_normalized, sobelY, mode='reflect')

        self.gradient_x = gradient_x / (self.I_normalized + 1e-5)
        self.gradient_y = gradient_y / (self.I_normalized + 1e-5)

    def calculate_displacement(self):
        self.displacement_x = self.gain_value * self.gradient_x
        self.displacement_y = self.gain_value * self.gradient_y
        self.displacement_x[np.abs(self.displacement_x) > 10] = 0
        self.displacement_y[np.abs(self.displacement_y) > 10] = 0

    def calcualte_output(self):
        self.single_frame_I_out = np.zeros((self.number_row, self.number_column))
        for nx in range(10, self.number_row - 10):
            for ny in range(10, self.number_column - 10):
                weighted1 = (1 - np.abs(self.displacement_x[nx, ny] - np.fix(self.displacement_x[nx, ny]))) * (
                            1 - np.abs(self.displacement_y[nx, ny] - np.fix(self.displacement_y[nx, ny])))
                weighted2 = (1 - np.abs(self.displacement_x[nx, ny] - np.fix(self.displacement_x[nx, ny]))) * (
                    np.abs(self.displacement_y[nx, ny] - np.fix(self.displacement_y[nx, ny])))
                weighted3 = (np.abs(self.displacement_x[nx, ny] - np.fix(self.displacement_x[nx, ny]))) * (
                            1 - np.abs(self.displacement_y[nx, ny] - np.fix(self.displacement_y[nx, ny])))
                weighted4 = (np.abs(self.displacement_x[nx, ny] - np.fix(self.displacement_x[nx, ny]))) * (
                    np.abs(self.displacement_y[nx, ny] - np.fix(self.displacement_y[nx, ny])))

                coordinate1 = [int(np.fix(self.displacement_x[nx, ny])), int(np.fix(self.displacement_y[nx, ny]))]
                coordinate2 = [int(np.fix(self.displacement_x[nx, ny])),
                               int(np.fix(self.displacement_y[nx, ny]) + np.sign(self.displacement_y[nx, ny]))]
                coordinate3 = [int(np.fix(self.displacement_x[nx, ny]) + np.sign(self.displacement_x[nx, ny])),
                               int(np.fix(self.displacement_y[nx, ny]))]
                coordinate4 = [int(np.fix(self.displacement_x[nx, ny]) + np.sign(self.displacement_x[nx, ny])),
                               int(np.fix(self.displacement_y[nx, ny]) + np.sign(self.displacement_y[nx, ny]))]

                self.single_frame_I_out[nx + coordinate1[0], ny + coordinate1[1]] += weighted1 * \
                                                                                     self.single_frame_I_magnified[
                                                                                         nx, ny]
                self.single_frame_I_out[nx + coordinate2[0], ny + coordinate2[1]] += weighted2 * \
                                                                                     self.single_frame_I_magnified[
                                                                                         nx, ny]
                self.single_frame_I_out[nx + coordinate3[0], ny + coordinate3[1]] += weighted3 * \
                                                                                     self.single_frame_I_magnified[
                                                                                         nx, ny]
                self.single_frame_I_out[nx + coordinate4[0], ny + coordinate4[1]] += weighted4 * \
                                                                                     self.single_frame_I_magnified[
                                                                                         nx, ny]
        return self.single_frame_I_out, self.single_frame_I_magnified


if __name__ == "__main__":
    r = ImageReconstruction()
    r.load_data(r"C:\Users\ruizhe.lin\Documents\data\20241001\20241001124830_dot_scanning_crop.tif")
    r.calculate_coordinates()
    r.dpr_single()
    r.upscale_interp()
    r.local_norm()
    r.calculate_gradients()
    r.calculate_displacement()
    result = r.calcualte_output()
