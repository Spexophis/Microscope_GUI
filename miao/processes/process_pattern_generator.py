import numpy as np
from PIL import Image


def generate_uniform_phase(size=(1536, 2048), ph=0, typ=np.uint8):
    if ph:
        return 255 * np.ones(size, dtype=typ)
    else:
        return np.zeros(size, dtype=typ)


def generate_binary_phase_1bit(size=(2048, 1536), period=(8, 0), phase=(0, 0), value=255, typ=np.uint8):
    width, height = size
    period_x, period_y = period
    offset_x, offset_y = phase
    x = np.arange(width)
    y = np.arange(height)
    xx, yy = np.meshgrid(x, y)
    xx += offset_x
    yy += offset_y
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


def generate_blazed_pattern(size=(1272, 1024), ps=12.5e-6, wl=488e-9, ang=4):
    slm_width, slm_height = size
    pixel_pitch = ps
    wavelength = wl
    theta_deg = ang

    theta_rad = np.deg2rad(theta_deg)
    grating_period = wavelength / np.sin(theta_rad)  # meters
    grating_period_px = grating_period / pixel_pitch

    x = np.arange(slm_width)
    blaze = (2 * np.pi * (x % grating_period_px) / grating_period_px)

    phase_pattern = np.tile(blaze, (slm_height, 1))
    return phase_pattern


def generate_lee_hologram(size=(1272, 1024), ps=12.5e-6, wl=488e-9, ang=4):
    slm_width, slm_height = size
    pixel_pitch = ps
    wavelength = wl
    steering_angle_deg = ang
    theta_rad = np.deg2rad(steering_angle_deg)
    k = 2 * np.pi / wavelength
    carrier_period_m = wavelength / np.sin(theta_rad)  # meters
    carrier_period_px = carrier_period_m / pixel_pitch
    carrier_freq_px = 1.0 / carrier_period_px

    x = np.arange(slm_width)
    y = np.arange(slm_height)
    xv, yv = np.meshgrid(x, y)
    carrier = 2 * np.pi * carrier_freq_px * xv

    phase_pattern = np.mod(carrier, 2 * np.pi)
    return phase_pattern


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


if __name__ == "__main__":
    data = np.zeros((512, 512), dtype=np.uint8)
    data[256 + 64, 256 - 64] = 255
    data[256 - 64, 256 - 64] = 255
    data[256 - 64, 256 + 64] = 255
    data[256 + 64, 256 + 64] = 255
    img = Image.fromarray(data, mode='L')
    img.save(r"C:\Users\ruizhe.lin\Documents\data\slm_files\Hamamatsu\four_dots_8bit.bmp", format='BMP')
