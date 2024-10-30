import numpy as np
from numpy.fft import fft2, fftshift
from scipy.optimize import curve_fit
from skimage import filters
import matplotlib.pyplot as plt

wl = 0.5  # wavelength in microns
na = 1.4  # numerical aperture
dx = 0.081  # pixel size in microns
fs = 1 / dx  # Spatial sampling frequency, inverse microns


def rms(data):
    _nx, _ny = data.shape
    _n = _nx * _ny
    m = np.mean(data, dtype=np.float64)
    a = (data - m) ** 2
    r = np.sqrt(np.sum(a) / _n)
    return r


def img_properties(img):
    return img.min(), img.max(), rms(img)


def fourier_transform(data):
    return np.log(np.abs(fftshift(fft2(data))))


def find_center_of_mass(image):
    height, width = image.shape
    # row_indices, col_indices = np.indices((height, width))
    # total_mass = np.sum(image)
    # row_mass = np.sum(row_indices * image) / total_mass
    # col_mass = np.sum(col_indices * image) / total_mass
    row_indices = np.arange(0, height)[:, np.newaxis]
    col_indices = np.arange(0, width)
    total_mass = np.sum(image)
    row_mass = np.sum(image * row_indices) / total_mass
    col_mass = np.sum(image * col_indices) / total_mass
    return row_mass, col_mass


def find_valley_2d(image, coordinates=None):
    data = image - image.min()
    data = data / data.max()
    mx = np.average(data, axis=0)
    my = np.average(data, axis=1)
    if coordinates is not None:
        cdx, cdy = coordinates
        l_ = valley_find(cdy, my)
        k_ = valley_find(cdx, mx)
        return k_, l_
    else:
        l_ = np.where(my == my.min())
        k_ = np.where(mx == mx.min())
        return k_[0][0], l_[0][0]


def find_peak_2d(image, coordinates=None):
    data = image - image.min()
    data = data / data.max()
    mx = np.average(data, axis=0)
    my = np.average(data, axis=1)
    if coordinates is not None:
        cdx, cdy = coordinates
        l_ = peak_find(cdy, my)
        k_ = peak_find(cdx, mx)
        return k_, l_
    else:
        l_ = np.where(my == my.max())
        k_ = np.where(mx == mx.max())
        return k_[0][0], l_[0][0]


def gaussian_beam(r, bg, I0, r0, w0):
    return bg + I0 * np.exp(-2 * ((r - r0) / w0) ** 2)


def fit_gaussian(image, verbose=False, plot=False, bounds=None):
    y_px, x_px = image.shape
    x, y = range(x_px), range(y_px)
    x_max = np.max(image, axis=0)
    y_max = np.max(image, axis=1)
    if bounds is None:
        bg_min, bg_max = 0, 10 * np.min(image)  # background
        I0_min, I0_max = np.min(image), 2 * np.max(image)  # peak intensity
        mean_min, mean_max = 0, max(x_px, y_px)  # mean
        w0_min, w0_max = 0, max(x_px, y_px)  # beam 1/e^2 radius
        bounds = ((bg_min, I0_min, mean_min, w0_min),
                  (bg_max, I0_max, mean_max, w0_max))
    xp = curve_fit(gaussian_beam, x, x_max, bounds=bounds)[0]  # x parameters
    yp = curve_fit(gaussian_beam, y, y_max, bounds=bounds)[0]  # y parameters
    xp = np.append(xp, (2 * np.log(2)) ** 0.5 * xp[3])  # add x FWHM
    yp = np.append(yp, (2 * np.log(2)) ** 0.5 * yp[3])  # add y FWHM
    if verbose:
        print('x: bg=%0.2f, I0=%0.2f, r0=%0.2f, w0=%0.2f, FWHM=%0.2f' % tuple(xp))
        print('y: bg=%0.2f, I0=%0.2f, r0=%0.2f, w0=%0.2f, FWHM=%0.2f' % tuple(yp))
    if plot:
        x_crv = gaussian_beam(x, *xp[:-1])
        y_crv = gaussian_beam(y, *yp[:-1])
        fig, ax = plt.subplots()
        ax.set_title('Gaussian fit')
        ax.set_ylabel('intensity')
        ax.set_xlabel('pixels')
        ax.plot(x, x_max, color='g', label='x_max', linestyle='--')
        ax.plot(x, x_crv, color='g', label='x_curve: (FWHM=%0.1f)' % xp[4])
        ax.plot(y, y_max, color='b', label='y_max', linestyle='--')
        ax.plot(y, y_crv, color='b', label='y_curve: (FWHM=%0.1f)' % yp[4])
        ax.legend(loc="upper right")
        fig.savefig('guassian_fit', dpi=150)
        fig.show()
    return xp, yp


def disc_array(shape=(128, 128), radi=64.0, origin=None, dtp=np.float64):
    _nx = shape[0]
    _ny = shape[1]
    ox = _nx / 2
    oy = _ny / 2
    x = np.linspace(-ox, ox - 1, _nx)
    y = np.linspace(-oy, oy - 1, _ny)
    xv, yv = np.meshgrid(x, y)
    rho = np.sqrt(xv ** 2 + yv ** 2)
    disc = (rho < radi).astype(dtp)
    if origin is not None:
        s0 = origin[0] - int(_nx / 2)
        s1 = origin[1] - int(_ny / 2)
        disc = np.roll(np.roll(disc, int(s0), 0), int(s1), 1)
    return disc


def gaussian_filter(shape, sigma, pv, orig=None):
    _nx, _ny = shape
    if orig is None:
        ux = _nx / 2.
        uy = _ny / 2.
    else:
        ux, uy = orig
    g = np.fromfunction(lambda i, j: np.exp(-((i - ux) ** 2. + (j - uy) ** 2.) / (2. * sigma ** 2.)), (_nx, _ny))
    return pv * g


def snr(img, lpr, hpr, gau=False):
    _ny, _nx = img.shape
    df = fs / _nx
    radius = (na / wl) / df
    msk = disc_array(shape=(_nx, _ny), radi=0.9 * radius)
    if gau:
        lp = msk * gaussian_filter(shape=(_nx, _ny), sigma=lpr * radius, pv=1, orig=None)
        hp = (1 - gaussian_filter(shape=(_nx, _ny), sigma=hpr * radius, pv=1, orig=None)) * msk
    else:
        lp = disc_array(shape=(_nx, _ny), radi=lpr * radius)
        hp = msk - disc_array(shape=(_nx, _ny), radi=hpr * radius)
    aft = np.fft.fftshift(np.fft.fft2(img))
    return (np.abs(hp * aft)).sum() / (np.abs(lp * aft)).sum()


def hpf(img, hpr, relative=True, gau=True):
    _nx, _ny = img.shape
    df = fs / _nx
    radius = (na / wl) / df
    msk = disc_array(shape=(_nx, _ny), radi=0.9 * radius)
    if gau:
        hp = (1 - gaussian_filter(shape=(_nx, _ny), sigma=hpr * radius, pv=1, orig=None)) * msk
    else:
        hp = msk - disc_array(shape=(_nx, _ny), radi=hpr * radius)
    aft = np.fft.fftshift(np.fft.fft2(img))
    aft = aft * hp
    if relative:
        wft = np.fft.fftshift(np.fft.fft2(img))
        return (np.abs(aft)).sum() / (np.abs(wft)).sum()
    else:
        return (np.abs(aft)).sum()


def peak_find(x, y):
    x = np.asarray(x)
    y = np.asarray(y)
    a, b, c = np.polyfit(x, y, 2)
    p = -1 * b / a / 2.0
    if a > 0:
        return "No peak"
    elif p >= x.max():
        return "Peak above maximum"
    elif p <= x.min():
        return "Peak below minimum"
    else:
        return p


def valley_find(x, y):
    x = np.asarray(x)
    y = np.asarray(y)
    a, b, c = np.polyfit(x, y, 2)
    v = -1 * b / a / 2.0
    if a < 0:
        raise ValueError("no minimum")
    elif (v >= x.max()) or (v <= x.min()):
        raise ValueError("minimum exceeding range")
    else:
        return v


def get_profile(data, ax, norm=False):
    data = data - data.min()
    data = data / data.max()
    if ax == 'Y':
        m = data.mean(0)
    elif ax == 'X':
        m = data.mean(1)
    else:
        raise ValueError("invalid axis")
    if norm:
        return m / m.max()
    else:
        return m


def pseudo_inverse(A, n=32):
    u, s, vt = np.linalg.svd(A)
    s_inv = np.zeros_like(A.T)
    if n is None:
        s_inv[:min(A.shape), :min(A.shape)] = np.diag(1 / s[:min(A.shape)])
    else:
        s_inv[:n, :n] = np.diag(1 / s[:n])
    return vt.T @ s_inv @ u.T


def get_eigen_coefficients(mta, mtb, ng=32):
    mp = pseudo_inverse(mtb, n=ng)
    return np.matmul(mp, mta)


def calculate_focus_measure_with_sobel(image):
    edges = filters.sobel(image)
    focus_measure = np.var(edges)
    return focus_measure


def calculate_focus_measure_with_laplacian(image):
    laplacian_image = filters.laplace(image)
    focus_measure = np.var(laplacian_image)
    return focus_measure


def meshgrid(nx_, ny_):
    x_ = np.arange(-nx_ / 2, nx_ / 2)
    y_ = np.arange(-ny_ / 2, ny_ / 2)
    xv_, yv_ = np.meshgrid(x_, y_, indexing='ij', sparse=True)
    return np.roll(xv_, int(nx_ / 2)), np.roll(yv_, int(ny_ / 2))


def shift(arr, shifts=None):
    if shifts is None:
        shifts = np.array(arr.shape) / 2
    if len(arr.shape) == len(shifts):
        for m, p in enumerate(shifts):
            arr = np.roll(arr, int(p), m)
    return arr


def get_pupil(nx_, rd_):
    msk = shift(disc_array(shape=(nx_, nx_), radi=rd_)) / np.sqrt(np.pi * rd_ ** 2) / nx_
    phi = np.zeros((nx_, nx_))
    return msk * np.exp(1j * phi)


def get_psf(nx_, rd_):
    bpp = get_pupil(nx_, rd_)
    psf_ = np.abs((fft2(fftshift(bpp)))) ** 2
    return psf_ / psf_.sum()


def get_correlation(image_to_be_computed, shift_orientation, shift_spacing, xv, yv, psf):
    kx = dx * np.cos(shift_orientation) / shift_spacing
    ky = dx * np.sin(shift_orientation) / shift_spacing
    ysh = np.exp(2j * np.pi * (kx * xv + ky * yv))
    otf0 = fft2(psf)
    imgf0 = fft2(image_to_be_computed)
    otf = fft2(psf * ysh)
    imgf = fft2(image_to_be_computed * ysh)
    a = np.sum(imgf0 * np.conj(otf0) * np.conj(imgf * np.conj(otf)))
    return np.abs(a), np.angle(a)


def find_pattern(data, angle=0., spacing=0.268, nps=10, r_ang=0.005, r_sp=0.005, verbose=False):
    nx, ny = data.shape
    df = fs / nx
    radius = (na / wl) / df
    xv_, yv_ = meshgrid(nx, nx)
    psf_ = get_psf(nx, radius)
    d_ang = 2 * r_ang / nps
    d_sp = 2 * r_sp / nps
    ang_iter = np.arange(-r_ang, r_ang + d_ang / 2, d_ang) + angle
    sp_iter = np.arange(-r_sp, r_sp + d_sp / 2, d_sp) + spacing
    mags = np.zeros((nps + 1, nps + 1))
    phs = np.zeros((nps + 1, nps + 1))
    for m, ang in enumerate(ang_iter):
        for n, sp in enumerate(sp_iter):
            mag, phase = get_correlation(data, ang, sp, xv_, yv_, psf_)
            if np.isnan(mag):
                mags[m, n] = 0.0
            else:
                mags[m, n] = mag
                phs[m, n] = phase
    if verbose:
        plt.figure()  # Set the figure size for better visualization
        plt.subplot(211)  # First subplot for magnitudes
        plt.imshow(mags, vmin=mags.min(), vmax=mags.max(),
                   extent=(sp_iter.min(), sp_iter.max(), ang_iter.max(), ang_iter.min()),
                   interpolation='none', cmap='viridis')
        plt.colorbar()
        plt.title('Magnitude')
        plt.xlabel('Spatial Iteration')
        plt.ylabel('Angular Iteration')
        plt.subplot(212)
        plt.imshow(phs, extent=(sp_iter.min(), sp_iter.max(), ang_iter.max(), ang_iter.min()),
                   interpolation='none', cmap='twilight')
        plt.colorbar()
        plt.title('Phase')
        plt.xlabel('Spatial Iteration')
        plt.ylabel('Angular Iteration')
        plt.tight_layout()
        plt.show()
    m, n = np.where(mags == mags.max())
    ang_max = m[0] * d_ang - r_ang + angle
    sp_max = n[0] * d_sp - r_sp + spacing
    return ang_max, sp_max, mags[m, n]
