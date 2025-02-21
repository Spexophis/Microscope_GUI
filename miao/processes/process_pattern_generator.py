import numpy as np
from PIL import Image


def generate_uniform_phase(size=(1536, 2048), ph=0, typ=np.uint8):
    if ph:
        return 255 * np.ones(size, dtype=typ)
    else:
        return np.zeros(size, dtype=typ)


def generate_binary_phase_1bit(size=(2048, 1536), period=(8, 0), value=255, typ=np.uint8):
    width, height = size
    period_x, period_y = period
    x = np.arange(width)
    y = np.arange(height)
    xx, yy = np.meshgrid(x, y)
    return np.where(((xx % period_x) < (period_x // 2)) ^ ((yy % period_y) < (period_y // 2)), value, 0).astype(typ)


def generate_binary_phase_8bit(size=(2048, 1536), periods=(8, 0), typ=np.uint8):
    width, height = size
    patterns = np.zeros((8, width, height))
    pattern = np.zeros((width, height))
    for i in range(8):
        pattern += patterns[i] * 2 ** i
    # pattern = pattern_7 * 2 ** 0 + pattern_6 * 2 ** 1 + pattern_2 * 2 ** 2 + pattern_3 * 3 ** 2 + pattern_4 * 2 ** 4 + pattern_5 * 2 ** 5 + pattern_6 * 2 ** 6 + pattern_7 * 2 ** 7
    return pattern


def save_to_bmp(data, svd, fn, bt=1):
    img = Image.fromarray(data, mode='L')
    if bt:
        img = img.convert('1', dither=Image.NONE)
        img.save(svd + fn + r"_1bit.bmp", format='BMP')
    else:
        img.save(svd + fn + r"_8bit.bmp", format='BMP')
