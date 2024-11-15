import os

import matplotlib.pyplot as plt
import numpy as np
import tifffile as tf
from scipy.optimize import curve_fit

from miao.tools import tool_improc as ipr


def binomial_model(x, a, b, c):
    return a * x ** 2 + b * x + c


def peak_find(x_data, y_data, y_std=None):
    x = np.asarray(x_data)
    y = np.asarray(y_data)
    if y_std is not None:
        y_err = np.asarray(y_std)
        p_opt, p_cov = curve_fit(binomial_model, x, y, sigma=y_err, absolute_sigma=True)
        a, b, c = p_opt
        x_peak = -b / (2 * a)
        if a > 0:
            return "No peak"
        elif x_peak >= x.max():
            return "Peak above maximum"
        elif x_peak <= x.min():
            return "Peak below minimum"
        else:
            sigma_a, sigma_b, sigma_c = np.sqrt(np.diag(p_cov))
            x_peak_err = np.sqrt((b / (2 * a ** 2) * sigma_a) ** 2 + (-1 / (2 * a) * sigma_b) ** 2)
            dy_da = x_peak ** 2
            dy_db = x_peak
            dy_dc = 1
            y_peak_err = np.sqrt((dy_da * sigma_a) ** 2 + (dy_db * sigma_b) ** 2 + (dy_dc * sigma_c) ** 2)
            return x_peak, x_peak_err, y_peak_err
    else:
        a, b, c = np.polyfit(x, y, 2)
        x_peak = -b / (2 * a)
        if a > 0:
            return "No peak"
        elif x_peak >= x.max():
            return "Peak above maximum"
        elif x_peak <= x.min():
            return "Peak below minimum"
        else:
            return x_peak


data_folder = r"C:\Users\ruizhe.lin\Documents\data\20241115\20241115_143610_sensorless_acquisitions"

metric_values = {i: {} for i in range(16)}

for filename in os.listdir(data_folder):
    if filename.endswith(".tiff"):
        fd = os.path.join(data_folder, filename)
        image_stack = tf.imread(fd)
        fn = os.path.splitext(filename)[0].split("_")
        zn, amp = int(fn[2]), float(fn[4])
        m = []
        for z in range(image_stack.shape[0]):
            img = image_stack[z, :, :]
            # res = ipr.hpf(img, 0.64, relative=True, gau=False)
            res = ipr.selected_frequency(img, freqs=[1.41, 2.82], relative=True)
            m.append(res)
        metric_values[zn][amp] = m

for n in [3, 4, 5, 6, 7, 8, 9, 10]:
    x = list(metric_values[0].keys())
    x.extend(list(metric_values[n].keys()))
    y = [np.mean(values) for values in metric_values[0].values()]
    y.extend([np.mean(values) for values in metric_values[n].values()])
    y_er = [np.std(values) for values in metric_values[0].values()]
    y_er.extend([np.std(values) for values in metric_values[n].values()])
    x_pk, x_pk_er, y_pk_er = peak_find(x, y, y_er)
    plt.figure(figsize=(10, 8))
    plt.errorbar(x, y, yerr=y_er, fmt='o', capsize=5, label='mean value with error bar')
    plt.axvline(x_pk, color='red', linestyle='--', label=f'peak = {x_pk:.3f}')
    plt.fill_betweenx([min(y), max(y)], x_pk - x_pk_er, x_pk + x_pk_er,
                      color='red', alpha=0.3, label=f'peak_err = ±{x_pk_er:.3f}')
    plt.xlabel('Zernike Amplitude')
    plt.ylabel('Metric Value')
    plt.title(f'Metric Value of Mode #{n}')
    plt.legend()
    plt.grid(True)
    plt.show()
    fd_n = os.path.join(data_folder, f"metric_value_mode_#{n}_plot.png")
    plt.savefig(fd_n, dpi=600, bbox_inches='tight')
