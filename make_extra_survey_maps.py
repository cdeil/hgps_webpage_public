"""Plot a few extra HGPS survey maps.

This is for the HGPS public release webpage.
We might also want to use those e.g. to make HiPS.
"""
import functools
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage.morphology import binary_erosion, disk
from astropy import units as u
from astropy.coordinates import Angle
from astropy.wcs import WCS
from astropy.io import fits
from astropy.visualization import ImageNormalize, LogStretch
from gammapy.image import SkyImage
from gammapy.image.plotting import SkyImagePanelPlotter
from make import config
from hgps.config import PERCENT_CRAB
import matplotlib

matplotlib.use('agg')
from matplotlib.image import imsave
import matplotlib.pyplot as plt


@functools.lru_cache()
def get_hdu(quantity):
    filename = f'build/data/hgps_map_{quantity}_0.1deg_v{config.version}.fits.gz'
    print(f'Reading {filename}')
    return fits.open(filename)[0]


@functools.lru_cache()
def get_data(quantity, normed=True):
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

    if normed and quantity != 'sensitivity':
        opts = get_opts(quantity)
        data = opts['norm'](data)

    return data


@functools.lru_cache()
def get_sky_image(quantity, normed=True):
    data = get_data(quantity, normed)
    wcs = WCS(get_hdu(quantity).header)
    return SkyImage(data=data, wcs=wcs)


@functools.lru_cache()
def get_opts(quantity):
    opts = dict(
        # TODO: try 'inferno' ?
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
            stretch=LogStretch(20),
        )
    else:
        raise ValueError(f'Invalid quantity: {quantity}')

    opts['norm'] = ImageNormalize(vmin=opts['vmin'], vmax=opts['vmax'], stretch=opts['stretch'], clip=True)

    return opts


def make_plot_no_axes(quantity):
    data = get_data(quantity)
    opts = get_opts(quantity)

    filename = f'build/figures/hgps_survey_{quantity}_single_panel_no_axes.png'
    print(f'Writing {filename}')
    imsave(filename, data, origin='lower', cmap=opts['cmap'])


def make_plot_with_axes_four_panel(quantity):
    image = get_sky_image(quantity)
    opts = get_opts(quantity)

    # Note: goal here is to match the paper Figure: hgps_survey_flux.pdf
    # There we have the following options (with an older version of this class):
    #     panel_pars = dict(npanels=4, center=[-19, -0.5], fov=[187, 7.5], xsize=None,
    #                   ysize=7.087, xborder=0.45, yborder=0.38, yspacing=0.22)
    center = -19, -0.5
    fov = 187, 7.5
    XLIM = Angle([center[0] + fov[0] / 2, center[0] - fov[0] / 2], 'deg')
    YLIM = Angle([center[1] - fov[1] / 2, center[1] + fov[1] / 2], 'deg')

    #             cbar_axes = self.fits_figure._figure.add_axes([0.86, 0.08, 0.02, 0.14])
    #                                                           [left, bottom, width, height]
    GRID_SPEC = dict(top=0.98, bottom=0.08, right=0.98, left=0.05, hspace=0.20)

    with u.imperial.enable():
        figsize_aanda = [241, 165] * u.mm  # was height: 180
        FIGSIZE = figsize_aanda.to('inch').value

    fig = plt.figure(figsize=FIGSIZE)
    plotter = SkyImagePanelPlotter(fig, xlim=XLIM, ylim=YLIM, npanels=4, **GRID_SPEC)
    axes = plotter.plot(image, cmap=opts['cmap'])
    [format_axes(ax) for ax in axes]

    # add_colobar(fig)

    filename = f'build/figures/hgps_survey_{quantity}_four_panel.png'
    print(f'Writing {filename}')
    plt.savefig(filename, dpi=300)


def format_axes(ax):
    ax.coords.frame.set_linewidth(0.)
    lon = ax.coords['glon']
    lon.set_ticks(spacing=5. * u.deg, color='w')
    lon.set_minor_frequency(5)
    lon.display_minor_ticks(True)
    lon.ticks.set_tick_out(False)
    lon.set_major_formatter('d')
    lon.set_axislabel('Galactic Longitude (deg)')

    lat = ax.coords['glat']
    lat.set_ticks(spacing=2 * u.deg, color='w')
    lat.set_minor_frequency(2)
    lat.set_major_formatter('d')
    lat.display_minor_ticks(True)
    lat.set_axislabel('Gal. Lat. (deg)')
    lat.ticks.set_tick_out(False)
    return ax


def main():
    make_plot_no_axes('significance')
    make_plot_no_axes('flux')
    make_plot_with_axes_four_panel('significance')
    make_plot_with_axes_four_panel('flux')


if __name__ == '__main__':
    main()
