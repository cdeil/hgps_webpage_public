#!/usr/bin/env python
"""Generate HIPS for HGPS."""
import subprocess
import os
import logging
from pathlib import Path
import shutil
import click
from astropy.io import fits
import hips
from make_extra_survey_maps import get_sky_image, get_hdu

log = logging.getLogger(__name__)

HIPSGEN_OPTIONS = {
    # The `blank` option is ignored for PNG (see email from Pierre)
    # 'blank': '0',
    # We choose equatorial frame, because MOC can only be in equatorial frame.
    # The input WCS image is in Galactic, but since a resampling to HEALPix
    # pixels happens anyways, it doesn't matter if the HiPS is equatorial or galactic frame.
    'hips_frame': 'equatorial',
    'order': 3,
    # The `mocOrder` option is ignored for PNG (see email from Pierre)
    'mocOrder': '9',
    'region': 'hips/significance_inputs/Moc.fits',
}

HIPSGEN_OPTIONS_SIGNIFICANCE = {
    **HIPSGEN_OPTIONS,
    'label': 'HGPS_Significance',
    'creator_did': 'CDS/P/HGPS/Significance',
}

HIPSGEN_OPTIONS_FLUX = {
    **HIPSGEN_OPTIONS,
    'label': 'HGPS_Flux',
    'creator_did': 'CDS/P/HGPS/Flux',
}

HIPS_META_INFO = {
    'obs_regime': 'Gamma-ray',
    'obs_collection': 'HGPS',
    'obs_description': ('H.E.S.S. is an array of ground-based gamma-ray telescopes located '
                        'in Namibia. The H.E.S.S. Galactic Plane Survey (HGPS) is the first '
                        'deep and wide survey of the Milky Way in TeV gamma-rays. The flux '
                        'values are given as integral photon flux above 1 TeV assuming a '
                        'power law spectrum for the differential flux with an index of -2.3. '
                        'The pixel values represent integrated values within a circular '
                        'region of 0.1 deg.'),
    'obs_copyright': '',
    'obs_ack': '',
    'hips_copyright': '',
    't_min': '53005',
    't_max': '56293',
    'em_max': '2.480e-20',
    'em_min': '1.240e-18',
    'bib_reference': '2018A&A...612A...1H',
    'bib_reference_url': 'https://ui.adsabs.harvard.edu/#abs/2018A%26A...612A...1H',
    'hips_creator': 'Christoph Deil, Axel Donath, Pierre Fernique',
}

HIPS_META_INFO_SIGNIFICANCE = {
    **HIPS_META_INFO,
    'obs_title': 'HGPS significance (Gaussian sigma)',
}

HIPS_META_INFO_FLUX = {
    **HIPS_META_INFO,
    'obs_title': 'HGPS integral flux > 1 TeV',
}


class Config:
    @property
    def out_path(self):
        return Path('hips') / self.quantity

    @property
    def in_path(self):
        return Path('hips') / (self.quantity + '_inputs')

    @property
    def in_fits(self):
        return self.in_path / 'image.fits'

    @property
    def in_png(self):
        return self.in_path / 'image.png'

    @property
    def in_header(self):
        return self.in_fits.with_suffix('.hhh')

    @property
    def hips_meta_info(self):
        if self.quantity == 'significance':
            return HIPS_META_INFO_SIGNIFICANCE
        elif self.quantity == 'flux':
            return HIPS_META_INFO_FLUX
        else:
            raise ValueError()

    @property
    def hipsgen_options(self):
        if self.quantity == 'significance':
            return HIPSGEN_OPTIONS_SIGNIFICANCE
        elif self.quantity == 'flux':
            return HIPSGEN_OPTIONS_FLUX
        else:
            raise ValueError()

    @property
    def aladin_jar(self):
        if 'ALADIN_JAR' not in os.environ:
            os.environ['ALADIN_JAR'] = '/Applications/Aladin.app//Contents/Resources/Java/Aladin.jar'
            # raise EnvironmentError('You have to set an environment variable ALADIN_JAR')

        return os.environ['ALADIN_JAR']


config = Config()


def prepare_inputs():
    """Prepare input files for hipsgen"""
    # Put this as a delayed import here due to this issue:
    # https://github.com/scikit-image/scikit-image/issues/3243
    import skimage.io
    from skimage.morphology import binary_closing, binary_dilation, disk

    image = get_sky_image(config.quantity, normed=False)
    filename = config.in_fits
    log.info(f'Writing {filename}')
    image.write(filename, overwrite=True)

    header = get_hdu(config.quantity).header
    filename = config.in_header
    log.info(f'Writing {filename}')
    header.totextfile(filename, endcard=True, overwrite=True)

    # For the PNG, we put the mask into the PNG alpha channel,
    # because hipsgen will use that to define the MOC,
    # i.e. then our sky area matches the HGPS survey area.
    filename = f'build/figures/hgps_survey_{config.quantity}_single_panel_no_axes.png'
    image = skimage.io.imread(filename)
    # This doesn't work, because mocgen doesn't take `mocOrder` into account with PNG
    # so it's not possible to make a good MOC (e.g. order 9) from a mask stored in PNG
    # if the tiles are only order 3 (see email from Pierre)
    significance = fits.open('hips/significance_inputs/image.fits')[0].data
    mask = binary_closing(significance != 0, selem=disk(20))
    image[:,:,-1] = 255 * mask[::-1,:].astype('uint8')
    # import IPython; IPython.embed()
    filename = str(config.in_png)
    log.info(f'Writing {filename}')
    skimage.io.imsave(filename, image)


def run_hipsgen(options):
    opts = ''
    for key, value in options.items():
        opts += f' {key}={value}'

    cmd = f'java -Xmx1400m -jar {config.aladin_jar} -hipsgen {opts}'
    log.info(f'Executing command: {cmd}')
    subprocess.call(cmd, shell=True)


def lint_hips():
    cmd = f'java -Xmx1400m -jar {config.aladin_jar} -hipsgen out={config.out_path} lint'
    log.info(f'Executing command: {cmd}')
    subprocess.call(cmd, shell=True)


def generate_hips():
    options = {}
    options['in'] = config.in_path
    options['out'] = config.out_path

    # These are only used for FITS tiles.
    # We decided not to produce FITS tiles here.
    # if config.quantity == 'flux':
    #     options['hips_pixel_cut'] = '"1e-14 1e-12 log"'
    # elif config.quantity == 'significance':
    #     options['hips_pixel_cut'] = '"0 100 log"'

    options.update(config.hipsgen_options)
    options['color'] = 'png'

    run_hipsgen(options)


def generate_moc():
    """Make a good MOC.

    Use order 9 and the mask.
    """
    filename_in = 'hips/significance_inputs/image.fits'
    filename_out = 'hips/significance_inputs/Moc.fits'
    cmd = f'java -Xmx1400m -jar {config.aladin_jar} -mocgen -strict in={filename_in} out={filename_out} blank=0 order=9'
    log.info(f'Executing command: {cmd}')
    subprocess.call(cmd, shell=True)


def patch_moc():
    src = 'hips/significance_inputs/Moc.fits'
    dst = str(config.out_path / 'Moc.fits')
    log.info(f'Copy: {src} {dst}')
    shutil.copy(src, dst)


def clean_hips():
    cmd = f'rm -r {config.out_path}'
    log.info(f'Executing command {cmd}')
    subprocess.call(cmd, shell=True)


def patch_hips_properties():
    path = config.out_path / 'properties'
    log.info(f'Patching {path}')
    properties = hips.HipsSurveyProperties.read(path)
    properties.data.update(config.hips_meta_info)
    properties.data['hips_initial_fov'] = '100'
    properties.data['hips_initial_ra'] = '266.40498829'
    properties.data['hips_initial_dec'] = '-28.93617776'
    properties.write(path)


@click.command()
@click.option('--quantity', default='all', type=click.Choice(['significance', 'flux', 'all']))
def cli(quantity):
    """Generate HIPS for HGPS."""
    logging.basicConfig(level='INFO')

    if quantity == 'all':
        quantities = ['significance', 'flux']
    else:
        quantities = [quantity]

    for quantity in quantities:
        config.quantity = quantity
        config.in_path.mkdir(parents=True, exist_ok=True)
        config.out_path.mkdir(parents=True, exist_ok=True)

        prepare_inputs()
        generate_moc()
        clean_hips()
        generate_hips()
        patch_hips_properties()
        patch_moc()
        lint_hips()


if __name__ == '__main__':
    cli()
