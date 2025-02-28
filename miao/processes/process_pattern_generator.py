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


def generate_binary_phase_8bit(bit_indices, bit_sequences):
    if len(bit_sequences) != len(bit_indices):
        raise Exception("Error: bit index and bit sequence length does not match")
    width, height = bit_sequences[0].shape
    patterns = np.zeros((8, width, height))
    pattern = np.zeros((width, height), dtype=np.uint8)
    for i, bn in enumerate(bit_indices):
        patterns[bn] = bit_sequences[i]
    for i in range(8):
        pattern += patterns[i] * (2 ** i)
    return pattern


def save_to_bmp(data, svd, fn, bt=1):
    img = Image.fromarray(data, mode='L')
    if bt:
        img = img.convert('1', dither=Image.NONE)
        img.save(svd + fn + r"_1bit.bmp", format='BMP')
    else:
        img.save(svd + fn + r"_8bit.bmp", format='BMP')


def generate_split_grating(beam_num=5, spacing=32, pixel_nums=(1024, 1272), iterations=500, binary=True):
    cent_x, cent_y = pixel_nums[0] // 2, pixel_nums[1] // 2
    beam_positions = []
    offsets = np.linspace(start=-int(spacing * int(np.floor(beam_num / 2))),
                          stop=int(spacing * int(np.floor(beam_num / 2))),
                          num=beam_num, dtype=int)
    for r_off in offsets:
        for c_off in offsets:
            beam_positions.append((cent_x + r_off, cent_y + c_off))
    field = np.random.choice([1, -1], size=pixel_nums)
    target = np.zeros(pixel_nums, dtype=float)
    for pos in beam_positions:
        r, c = pos
        target[r, c] = 1.0
    for _ in range(iterations):
        far_field = np.fft.fftshift(np.fft.fft2(field))
        phase_far = np.exp(1j * np.angle(far_field))
        far_field_new = target * phase_far
        field_new = np.fft.ifft2(np.fft.ifftshift(far_field_new))
        if binary:
            field = np.where(np.real(field_new) >= 0, 1, -1)
    return field
