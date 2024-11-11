import numpy as np
import tifffile as tf
from numpy.fft import fft2, fftshift
from scipy.optimize import curve_fit
from skimage.feature import peak_local_max


class ImageReconstruction:

    def __init__(self):
        self.na = 1.4
        self.wl = 0.5
        self.resolution = self.wl / (2 * self.na)
        self.pixel_size_x = 0.081
        self.pixel_size_y = 0.081
        self.sigma = self.resolution / (2 * np.sqrt(2 * np.log(2)))
        self.wd = 2

    def load_data(self, fd):
        data = tf.TiffFile(fd)
        self.data_stack = data.asarray()
        self.n, self.ny, self.nx = self.data_stack.shape
        page = data.pages[0]
        x_resolution = page.tags.get('XResolution')
        y_resolution = page.tags.get('YResolution')
        if x_resolution is not None and y_resolution is not None:
            x_res_value = x_resolution.value[0] / x_resolution.value[1]
            y_res_value = y_resolution.value[0] / y_resolution.value[1]
            factor = 10.0 ** 4
            self.pixel_size_x = int(factor / x_res_value) / factor
            self.pixel_size_y = int(factor / y_res_value) / factor

    def generate_coordinates(self):
        self.xv, self.yv = np.meshgrid(np.linspace(0, self.nx - 1, self.nx), np.linspace(0, self.ny - 1, self.ny))
        self.xv = self.pixel_size_x * self.xv
        self.yv = self.pixel_size_y * self.yv

    def set_scanning_parameters(self, step_nums=(32, 32)):
        assert step_nums[0] * step_nums[1] == self.n, f"Scanning step numbers does not match the data size"
        self.step_y, self.step_x = step_nums

    def set_focal_parameters(self, periods=(0.83, 0.83), ranges=((20., 40.), (20., 40.))):
        self.period_x_um, self.period_y_um = periods  # micrometer
        self.range_x_um, self.range_y_um = ranges  # micrometers
        x_centers = np.arange(self.range_x_um[0], self.range_x_um[1], self.period_x_um)
        y_centers = np.arange(self.range_y_um[0], self.range_y_um[1], self.period_y_um)
        self.nxc = x_centers.shape[0]
        self.nyc = y_centers.shape[0]
        x_grid, y_grid = np.meshgrid(x_centers, y_centers)
        self.center_list = np.column_stack([y_grid.ravel(), x_grid.ravel()]).tolist()

    def correct_center_array(self):
        for i, (y_center, x_center) in enumerate(self.center_list):
            x_start = max(0, x_center - self.period_x_um / 2)
            y_start = max(0, y_center - self.period_y_um / 2)
            x_end = min(self.nx * self.pixel_size_x, x_start + self.period_x_um)
            y_end = min(self.ny * self.pixel_size_y, y_start + self.period_y_um)
            x_start = int(x_start / self.pixel_size_x)
            y_start = int(y_start / self.pixel_size_y)
            x_end = int(x_end / self.pixel_size_x)
            y_end = int(y_end / self.pixel_size_y)
            sub_img = self.image_avg[y_start:y_end, x_start:x_end]
            yp, xp = fit_gaussian_2d(sub_img)
            x_center = (x_start + xp[2]) * self.pixel_size_x
            y_center = (y_start + yp[2]) * self.pixel_size_y
            self.center_list[i] = [y_center, x_center]

    def generate_center_array(self):
        center_array = np.zeros_like(self.xv)
        for i, (yc, xc) in enumerate(self.center_list):
            x_idx = (np.abs(self.xv[0, :] - xc)).argmin()
            y_idx = (np.abs(self.yv[:, 0] - yc)).argmin()
            center_array[y_idx, x_idx] = 1
        return center_array

    def create_gaussian_1d_array(self, x_=True):
        array = np.zeros((self.ny, self.nx))
        for [y_center, x_center] in self.center_list:
            if x_:
                array += self.gaussian_1d(self.xv, x_center, self.sigma)
            else:
                array += self.gaussian_1d(self.yv, y_center, self.sigma)
        return array

    def create_gaussian_2d_array(self, t=True):
        array = np.zeros((self.ny, self.nx))
        for [y_center, x_center] in self.center_list:
            array += self.gaussian_2d(self.xv, self.yv, x_center, y_center, self.sigma, t)
        return array

    def apply_gaussian(self, stack):
        mask = self.create_gaussian_2d_array()
        assert stack.shape[1:] == mask.shape, "Gaussian mask shape must match the shape of each 2D slice in the stack"
        masked_stack = stack * mask[np.newaxis, :, :]
        return masked_stack

    def stack_subarray(self, array_stack, direction=0):
        subarray_stack = []
        for [y_center, x_center] in self.center_list:
            x_start = max(0, x_center - self.period_x_um / 2)
            y_start = max(0, y_center - self.period_y_um / 2)
            x_end = min(self.nx * self.pixel_size_x, x_start + self.period_x_um)
            y_end = min(self.ny * self.pixel_size_y, y_start + self.period_y_um)
            x_start_px = int(x_start / self.pixel_size_x)
            y_start_px = int(y_start / self.pixel_size_y)
            x_end_px = int(x_end / self.pixel_size_x)
            y_end_px = int(y_end / self.pixel_size_y)
            subarray = array_stack[:, y_start_px:y_end_px, x_start_px:x_end_px]
            subarray = np.sum(subarray, axis=(1, 2)).reshape(self.step_y, self.step_x)
            if direction == 0:
                subarray_stack.append(subarray)
            elif direction == 1:
                subarray_stack.append(np.transpose(subarray)[::-1])
            elif direction == 2:
                subarray_stack.append(np.transpose(subarray[::-1]))
            elif direction == 3:
                subarray_stack.append(subarray[::-1, ::-1])
        return np.asarray(subarray_stack)

    def tile_sub_images(self, substack, axis='x'):
        x_tiles = self.nxc
        y_tiles = self.nyc
        n, h, w = substack.shape
        assert (n, h, w) == (x_tiles * y_tiles, self.step_y, self.step_x), f"Input stack has the wrong shape"
        full_image = np.zeros((y_tiles * h, x_tiles * w))
        for idx in range(n):
            if axis == 'x':
                row = idx // x_tiles
                col = idx % x_tiles
            elif axis == 'y':
                row = idx % y_tiles
                col = idx // y_tiles
            else:
                raise ValueError("Axis must be 'x' or 'y'")
            full_image[row * h:(row + 1) * h, col * w:(col + 1) * w] = substack[idx]
        return full_image

    def gaussian_1d(self, x_, mu_x, sigma):
        g = np.exp(-((x_ - mu_x) ** 2) / (2 * sigma ** 2))
        msk = ((x_ - mu_x) ** 2) / (self.wd * sigma ** 2)
        msk = msk <= 1.
        return g * msk

    def gaussian_2d(self, x_, y_, mu_x, mu_y, sigma, thr=True):
        g = np.exp(-((x_ - mu_x) ** 2 + (y_ - mu_y) ** 2) / (2 * sigma ** 2))
        msk = ((x_ - mu_x) ** 2 + (y_ - mu_y) ** 2) / (self.wd * sigma ** 2)
        if thr:
            msk = msk <= 1.
            return g * msk
        else:
            return g

    def extract_periods(self):
        self.image_avg = np.average(self.data_stack, axis=0)
        fft_image = fftshift(fft2(self.image_avg))
        magnitude_spectrum = np.abs(fft_image)
        normalized_spectrum = np.log1p(magnitude_spectrum)
        peaks = peak_local_max(normalized_spectrum, min_distance=10, threshold_rel=0.1)
        center = np.array(normalized_spectrum.shape) // 2
        peak_distances = np.sqrt((peaks[:, 0] - center[0]) ** 2 + (peaks[:, 1] - center[1]) ** 2)
        sorted_indices = np.argsort(peak_distances)
        sorted_peaks = peaks[sorted_indices]
        periods = []
        for peak in sorted_peaks[1:5]:
            distance = np.sqrt((peak[0] - center[0]) ** 2 + (peak[1] - center[1]) ** 2)
            period = (self.image_avg.shape[0] / distance) * self.pixel_size_x
            periods.append(period)
        return periods, normalized_spectrum, sorted_peaks[1:5]

    def fft_frequency_map(self, rows, cols):
        freq_x = np.fft.fftfreq(cols, self.pixel_size_x)
        freq_y = np.fft.fftfreq(rows, self.pixel_size_y)
        fx, fy = np.meshgrid(freq_x, freq_y)
        fxy = np.sqrt(fx ** 2 + fy ** 2)
        frequency_map = np.divide(1.0, fxy, where=fxy != 0, out=np.zeros_like(fxy))
        return fftshift(frequency_map)


def fit_gaussian_2d(image, bounds=None):
    def gaussian_beam(r, bg, I0, r0, w0):
        # Gaussian function in 1D for fitting the beam profile
        return bg + I0 * np.exp(-2 * ((r - r0) / w0) ** 2)

    # Get the dimensions of the image
    y_px, x_px = image.shape

    # Generate the coordinates for x and y
    x = np.arange(x_px)
    y = np.arange(y_px)

    # Get the maximum intensity values along the x and y axes
    x_max = np.max(image, axis=0)
    y_max = np.max(image, axis=1)

    # Set bounds if none are provided
    if bounds is None:
        bg_min, bg_max = 0, 10 * np.min(image)  # Background bounds
        I0_min, I0_max = np.min(image), 2 * np.max(image)  # Intensity bounds
        mean_min, mean_max = 0, max(x_px, y_px)  # Mean (center) bounds
        w0_min, w0_max = 0, max(x_px, y_px)  # Width (beam size) bounds
        bounds = ((bg_min, I0_min, mean_min, w0_min),
                  (bg_max, I0_max, mean_max, w0_max))

    # Fit the Gaussian beam to both the x and y axes using curve_fit
    xp = curve_fit(gaussian_beam, x, x_max, bounds=bounds)[0]  # x parameters
    yp = curve_fit(gaussian_beam, y, y_max, bounds=bounds)[0]  # y parameters

    return yp, xp


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    r = ImageReconstruction()
    r.load_data(r"C:\Users\ruizhe.lin\Documents\data\20241001\20241001124830_dot_scanning_crop.tif")
    r.pixel_size_x = 0.081
    r.pixel_size_y = 0.081
    r.generate_coordinates()
    r.set_scanning_parameters(step_nums=(27, 27))
    data_avg = np.average(r.data_stack, axis=0)
    r.set_focal_parameters(periods=(0.846, 0.846), ranges=((0.4, r.nx * r.pixel_size_x), (0.36, r.ny * r.pixel_size_y)))
    arr = r.generate_center_array()
    plt.figure()
    plt.imshow(arr, cmap='viridis', interpolation='none')
    plt.imshow(data_avg, cmap='plasma', interpolation='none', alpha=0.2)
    plt.savefig(r'C:\Users\ruizhe.lin\Desktop\alignment.png', dpi=600)
    gd = r.apply_gaussian(r.data_stack)
    sub = r.stack_subarray(gd, direction=2)
    result = r.tile_sub_images(sub, 'y')
    tf.imwrite(r'C:\Users\ruizhe.lin\Desktop\result_image.tif', result)
