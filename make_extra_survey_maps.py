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
import matplotlib

matplotlib.use('agg')
from matplotlib.image import imsave
import matplotlib.pyplot as plt

FLUX_CRAB_INT_1TEV = 2.26e-11  # m^-2 s^-1
PERCENT_CRAB = 100 / FLUX_CRAB_INT_1TEV


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


def get_limits():
    # Note: goal here is to match the paper Figure: hgps_survey_flux.pdf
    # There we have the following options (with an older version of this class):
    #     panel_pars = dict(npanels=4, center=[-19, -0.5], fov=[187, 7.5], xsize=None,
    #                   ysize=7.087, xborder=0.45, yborder=0.38, yspacing=0.22)
    center = -19, -0.5
    fov = 187, 7.5
    xlim = Angle([center[0] + fov[0] / 2, center[0] - fov[0] / 2], 'deg')
    ylim = Angle([center[1] - fov[1] / 2, center[1] + fov[1] / 2], 'deg')
    return dict(xlim=xlim, ylim=ylim)


def make_plot_with_axes_four_panel(quantity):
    image = get_sky_image(quantity)
    opts = get_opts(quantity)

    #             cbar_axes = self.fits_figure._figure.add_axes([0.86, 0.08, 0.02, 0.14])
    #                                                           [left, bottom, width, height]
    grid_spec = get_limits()
    grid_spec['npanels'] = 4
    grid_spec.update(top=0.98, bottom=0.08, right=0.98, left=0.05, hspace=0.20)

    with u.imperial.enable():
        figsize_aanda = [241, 165] * u.mm  # was height: 180
        FIGSIZE = figsize_aanda.to('inch').value

    fig = plt.figure(figsize=FIGSIZE)
    plotter = SkyImagePanelPlotter(fig, **grid_spec)
    axes = plotter.plot(image, cmap=opts['cmap'])
    [format_axes(ax) for ax in axes]

    # Adding a colorbar currently doesn't work, because `data` is pre-scaled to 0 to 1.
    # label = dict(flux='Flux', significance='Significance')[quantity]
    # add_colorbar(fig, label=label)

    filename = f'build/figures/hgps_survey_{quantity}_four_panel.png'
    print(f'Writing {filename}')
    plt.savefig(filename, dpi=300)


def make_plot_with_axes_single_panel(quantity):
    image = get_sky_image(quantity)
    opts = get_opts(quantity)

    fig = plt.figure(figsize=(25, 1.8))
    # [left, bottom, width, height]
    ax = fig.add_axes([0.02, 0.13, 0.97, 0.92], projection=image.wcs)
    ax.imshow(image.data, origin='lower', cmap=opts['cmap'])
    format_axes(ax)

    # fig.tight_layout()

    filename = f'build/figures/hgps_survey_{quantity}_single_panel.png'
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


def add_colorbar(fig, label):
    cbar_axes = fig.add_axes([0.86, 0.09, 0.02, 0.14])
    image = fig.axes[3].images[0]
    # from IPython import embed; embed()

    cbar = fig.colorbar(image, cax=cbar_axes)
    cbar.solids.set_edgecolor('face')
    cbar.outline.set_edgecolor('white')
    cbar.outline.set_linewidth(0.5)
    cbar.ax.yaxis.set_tick_params(color='w', size=5)

    ticks_pos = image.norm.inverse(np.linspace(0, 1, 5))
    tick_labels = ['{:>4.1f}'.format(_) for _ in ticks_pos]
    cbar.set_ticks(ticks_pos)
    cbar_axes.set_yticklabels(tick_labels, color='w', ha='left')
    cbar_axes.set_ylabel(label, color='w')
    cbar_axes.tick_params(direction='in')


def main():
    make_plot_no_axes('significance')
    make_plot_no_axes('flux')

    make_plot_with_axes_four_panel('significance')
    make_plot_with_axes_four_panel('flux')

    make_plot_with_axes_single_panel('significance')
    make_plot_with_axes_single_panel('flux')


if __name__ == '__main__':
    main()
