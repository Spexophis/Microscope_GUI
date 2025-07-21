# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


import numpy as np
from numpy.fft import fft2, ifft2, fftshift
from skimage.restoration import unwrap_phase


class Interferometer:

    def __init__(self):
        self.x = 409
        self.y = 279
        self.hsx = 128
        self.hsy = 128

    def reconstruction_surface(self, img, msk):
        imf = fftshift(fft2(img * msk))
        cf = self.extract_order(imf)
        ph = ifft2(cf)
        phase = np.arctan2(ph.imag, ph.real)
        phase_unwrapped = unwrap_phase(phase)
        return phase, phase_unwrapped

    def extract_order(self, df):
        return fftshift(df[self.y - self.hsy: self.y + self.hsy, self.x - self.hsx:self.x + self.hsx])

    @staticmethod
    def circular_mask(radius, size, circle_centre=(0, 0)):
        m = np.zeros((size, size))
        coord = np.arange(0.5, size, 1.0)
        x, y = np.meshgrid(coord, coord)
        x -= size / 2.
        y -= size / 2.
        x -= circle_centre[0]
        y -= circle_centre[1]
        mask = x ** 2 + y ** 2 <= radius ** 2
        m[mask] = 1
        return m
