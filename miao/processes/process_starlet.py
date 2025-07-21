# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


import numpy as np
import tifffile as tf


class StarletTransform:

    def __init__(self):
        self.c = []
        self.w = []

    def input_image(self, img):
        self.img_shape = img.shape
        self.c.append(img)

    def cubic_kernel(self):
        self._kernel = np.array([1 / 16, 1 / 4, 3 / 8, 1 / 4, 1 / 16])
        self._kernel_size = self._kernel.shape[0]

    def discrete_wavelet_transform(self):
        j = len(self.c) - 1
        temp = np.zeros(self.img_shape)
        for m in range(self._kernel_size):
            for n in range(self._kernel_size):
                temp += self._kernel[m] * self._kernel[n] * np.roll(np.roll(self.c[j], shift=n * 2 ** j, axis=0),
                                                                    shift=m * 2 ** j, axis=1)
        temp = temp / 25
        temp1 = np.zeros(self.img_shape)
        for m in range(5):
            for n in range(5):
                temp1 += temp1 + self._kernel[m] * self._kernel[n] * np.roll(np.roll(temp, shift=n * 2 ** j, axis=0),
                                                                             shift=m * 2 ** j, axis=1)
        temp1 = temp1 / 25
        self.c.append(temp1)
        self.w.append(self.c[j] - temp1)


if __name__ == '__main__':
    s = StarletTransform()
    s.cubic_kernel()
    s.input_image(r'C:\Users\ruizhe.lin\Desktop\monalisa_raw_data_frame.tif')
    for i in range(6):
        s.discrete_wavelet_transform()
    for i in range(6):
        print(s.c[i].sum())
    tf.imwrite(r'C:\Users\ruizhe.lin\Desktop\starlet_result_w.tif', np.asarray(s.w))
    tf.imwrite(r'C:\Users\ruizhe.lin\Desktop\starlet_result_c.tif', np.asarray(s.c))
