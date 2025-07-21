# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


import pandas as pd
import math
import tifffile as tf
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib
from miao.tools import tool_zernike
import numpy as np
matplotlib.use('Qt5Agg')


def plot_colortable(colors, *, ncols=4, sort_colors=True):
    cell_width = 212
    cell_height = 22
    swatch_width = 48
    margin = 12

    # Sort colors by hue, saturation, value and name.
    if sort_colors is True:
        names = sorted(
            colors, key=lambda c: tuple(matplotlib.colors.rgb_to_hsv(matplotlib.colors.to_rgb(c))))
    else:
        names = list(colors)

    n = len(names)
    nrows = math.ceil(n / ncols)

    width = cell_width * ncols + 2 * margin
    height = cell_height * nrows + 2 * margin
    dpi = 72

    fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    fig.subplots_adjust(margin / width, margin / height,
                        (width - margin) / width, (height - margin) / height)
    ax.set_xlim(0, cell_width * ncols)
    ax.set_ylim(cell_height * (nrows - 0.5), -cell_height / 2.)
    ax.yaxis.set_visible(False)
    ax.xaxis.set_visible(False)
    ax.set_axis_off()

    for i, name in enumerate(names):
        row = i % nrows
        col = i // nrows
        y = row * cell_height

        swatch_start_x = cell_width * col
        text_pos_x = cell_width * col + swatch_width + 7

        ax.text(text_pos_x, y, name, fontsize=14,
                horizontalalignment='left',
                verticalalignment='center')

        ax.add_patch(
            Rectangle(xy=(swatch_start_x, y - 9), width=swatch_width,
                      height=18, facecolor=colors[name], edgecolor='0.7')
        )

    return fig


# plot_colortable(matplotlib.colors.CSS4_COLORS)
# plt.show()


# Read the Excel file
file_path = r"C:\Users\Ruiz\Desktop\New folder\corr_1_20240708141707zernike_coefficients.xlsx"
df = pd.read_excel(file_path)
labels = df['mods']
values = df['amps']
str_labels = labels.astype(str)
# Plot the bar graph
plt.ion()
plt.figure(figsize=(5, 3))  # High resolution
plt.bar(str_labels, values, color='deepskyblue')
plt.xlabel('Zernike Modes', fontsize=12)
plt.ylabel('Amplitudes', fontsize=12)
plt.grid(True, linestyle='--', linewidth=0.4)
plt.xticks(rotation=45, ha='center', fontsize=10)
plt.tight_layout()
plt.savefig(r'C:\Users\Ruiz\Desktop\New folder\zernike_coefficients_c_1.png', dpi=600)
plt.show()

# Read the Excel file
file_path = r"C:\Users\Ruiz\Desktop\New folder\corr_2_20240708141822zernike_coefficients.xlsx"
df = pd.read_excel(file_path)
labels = df['mods']
values = df['amps']
str_labels = labels.astype(str)
# Plot the bar graph
plt.ion()
plt.figure(figsize=(5, 3))  # High resolution
plt.bar(str_labels, values, color='deepskyblue')
plt.xlabel('Zernike Modes', fontsize=12)
plt.ylabel('Amplitudes', fontsize=12)
plt.grid(True, linestyle='--', linewidth=0.4)
plt.xticks(rotation=45, ha='center', fontsize=10)
plt.tight_layout()
plt.savefig(r'C:\Users\Ruiz\Desktop\New folder\zernike_coefficients_c_2.png', dpi=600)
plt.show()
# Plot the wavefront
zernike = tool_zernike.zernike_polynomials(size=[512, 512])
wf = np.zeros((512, 512))
for i in range(16):
    wf += values[i] * zernike[i]
plt.ion()
plt.figure(figsize=(5, 5))
plt.imshow(wf, interpolation='none')
plt.show(block=False)


# Read the Excel file
file_path = r"C:\Users\Ruiz\Desktop\New folder\fwhms.xlsx"
df = pd.read_excel(file_path)
labels = df['x']
values = df['w AO']
values_2 = df['w/o AO']
adjusted_labels = labels / 1000 - 0.5 * labels.max() / 1000
# Plot the profile graph
plt.ion()
plt.figure(figsize=(5, 3))
plt.plot(adjusted_labels, values, label="w AO", linewidth=2, linestyle='-', marker='o', markersize=5)
plt.plot(adjusted_labels, values_2, label="w/o AO", linewidth=2, linestyle='--', marker='s', markersize=5)
plt.xlabel(r'x / $\mu$m', fontsize=12)
plt.ylabel('Intensity', fontsize=12)
plt.grid(True, linestyle='--', linewidth=0.4, alpha=0.7)
plt.xticks(ha='center', fontsize=10)
plt.legend(fontsize=12, loc='best')
plt.tight_layout()
plt.savefig(r'C:\Users\Ruiz\Desktop\New folder\fwhm.png', dpi=600)
plt.show()


# Reconstruct wavefront
zernike = tool_zernike.zernike_polynomials(size=[128, 128])
zslopes = tool_zernike.zernike_derivatives(size=[128, 128])
fn = r"C:\Users\ruizhe.lin\Documents\data\dm_files\bax513\influence_function_modal_2024_11_25_16_54.tif"
inf_model = tf.imread(fn)
fnd = r"D:\data\20241128\20241128183628_BAX513_cmd_file.xlsx"
df = pd.read_excel(fnd, sheet_name=None)
cmds = []
for key, cmd in df.items():
    cmds.append(df[key]['Push'].tolist())
r = []
wf = []
for cmd in cmds:
    r_temp = np.dot(inf_model, np.asarray(cmd)) - np.dot(inf_model, np.asarray(cmds[1]))
    r.append(r_temp)
    wf_temp = np.zeros((128, 128))
    for i in range(16):
        wf_temp += zernike[i] * r_temp[i]
    wf.append(wf_temp)
