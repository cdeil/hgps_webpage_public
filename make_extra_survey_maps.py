"""Plot a few extra HGPS survey maps.

This is for the HGPS public release webpage.
We might also want to use those e.g. to make HiPS.
"""
import functools
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage.morphology import binary_erosion, disk
from astropy.io import fits
from astropy.visualization import ImageNormalize, LogStretch
from make import config
from hgps.config import PERCENT_CRAB, FLUX_CRAB_INT_1TEV

from matplotlib.image import imsave


@functools.lru_cache()
def get_hdu(quantity):
    filename = f'build/data/hgps_map_{quantity}_0.1deg_v{config.version}.fits.gz'
    print(f'Reading {filename}')
    return fits.open(filename)[0]


@functools.lru_cache()
def get_data(quantity):
    data = get_hdu(quantity).data.copy()

    # Replace NaN with 0 to avoid plotting issues
    data = np.nan_to_num(data)

    # For flux, apply a mask based on sensitivity
    if quantity == 'flux':
        s = get_data('sensitivity')
        good = (s * PERCENT_CRAB < 2.5) & (s > 0)
        # There are edge effects, we need to blank out a border of pixels
        good = binary_erosion(good, selem=disk(7))
        data[~good] = 0

    # Smooth a little bit to make the image less noisy
    data = gaussian_filter(data, sigma=1)

    return data


def get_opts(quantity):
    opts = dict(
        cmap='afmhot',
    )
    if quantity == 'significance':
        opts.update(
            vmin=0,
            vmax=100,
            stretch=LogStretch(150),
        )
    elif quantity == 'flux':
        opts.update(
            vmin=1e-14,
            vmax=1e-12,
            stretch=LogStretch(10),
        )
    else:
        raise ValueError(f'Invalid quantity: {quantity}')
    return opts


def make_plot_direct(quantity):
    data = get_data(quantity)
    opts = get_opts(quantity)

    norm = ImageNormalize(vmin=opts['vmin'], vmax=opts['vmax'], stretch=opts['stretch'], clip=True)
    data = norm(data)

    filename = f'build/figures/hgps_survey_{quantity}_single_panel.png'
    print(f'Writing {filename}')
    imsave(filename, data, origin='lower', cmap=opts['cmap'])


def main():
    make_plot_direct('significance')
    make_plot_direct('flux')


if __name__ == '__main__':
    main()
