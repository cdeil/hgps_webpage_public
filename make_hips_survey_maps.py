#!/usr/bin/env python
"""Generate HIPS for HGPS."""
import subprocess
import os
import logging
from collections import OrderedDict
from pathlib import Path
import shutil
import click
from make_extra_survey_maps import get_sky_image, get_hdu

log = logging.getLogger(__name__)

HIPSGEN_OPTIONS = {
    'creator_did': 'MPIK/P/HGPS',
    'blank': '0',
    'hips_frame': 'galactic',
}

HIPSGEN_OPTIONS_SIGNIFICANCE = {
    **HIPSGEN_OPTIONS,
    'label': 'HGPS_Significance',
}

HIPSGEN_OPTIONS_FLUX = {
    **HIPSGEN_OPTIONS,
    'label': 'HGPS_Flux',
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


config = Config()


def prepare_inputs():
    """Prepare input files for hipsgen"""
    image = get_sky_image(config.quantity, normed=False)
    filename = config.in_fits
    log.info(f'Writing {filename}')
    image.write(filename, overwrite=True)

    header = get_hdu(config.quantity).header
    filename = config.in_header
    log.info(f'Writing {filename}')
    header.totextfile(filename, endcard=True, overwrite=True)

    src = f'build/figures/hgps_survey_{config.quantity}_single_panel_no_axes.png'
    dst = str(config.in_png)
    log.info(f'Copy {src} -> {dst}')
    shutil.copy(src, dst)

def get_aladin_jar():
    if 'ALADIN_JAR' not in os.environ:
        os.environ['ALADIN_JAR'] = '/Users/deil/software/bin/Aladin.jar'
        # raise EnvironmentError('You have to set an environment variable ALADIN_JAR')

    return os.environ['ALADIN_JAR']


def run_hipsgen(opts):
    aladin_jar = get_aladin_jar()
    cmd = f'java -Xmx1400m -jar {aladin_jar} -hipsgen {opts}'
    log.info(f'Executing command {cmd}')
    subprocess.call(cmd, shell=True)


def generate_hips():
    options = {}
    options['in'] = config.in_path
    options['out'] = config.out_path

    # TODO: are these used for the HiPS FITS tiles?
    # If yes, we should try and make them match the PNG tiles
    if config.quantity == 'flux':
        options['hips_pixel_cut'] = '"1e-14 1e-12 log"'
    elif config.quantity == 'significance':
        options['hips_pixel_cut'] = '"0 100 log"'

    options.update(config.hipsgen_options)

    # options['-hhh'] = config.in_png
    options['color'] = 'png'

    opts = ''
    for key, value in options.items():
        opts += f' {key}={value}'

    run_hipsgen(opts)


def view_hips():
    cmd = f'java -jar {ALADIN_JAR_PATH} {config.out_path}'
    log.info(f'Executing command {cmd}')
    subprocess.call(cmd, shell=True)


def clean_hips():
    cmd = f'rm -r {config.out_path}'
    log.info(f'Executing command {cmd}')
    subprocess.call(cmd, shell=True)


def tar_hips():
    cmd = f'tar cfvz {hips_out_folder}.tar.gz {config.out_path}'
    log.info(f'Executing command {cmd}')
    subprocess.call(cmd, shell=True)


def update_hips_properties():
    filename = config.out_path / 'properties'

    properties = OrderedDict()
    with filename.open('r+') as fh:
        for line in fh:
            try:
                key, value = line.split(' = ')
            except ValueError:
                footer = line + fh.read()

            key, value = key.strip(), value.strip()
            if key.replace('#', '') in config.hips_meta_info:
                key = key.replace('#', '')
            properties[key] = value

        properties.update(config.hips_meta_info)
        fh.seek(0)
        lines = ["{key:20s} = {value}".format(key=key, value=value) for key, value in properties.items()]
        lines.append(footer)
        fh.write('\n'.join(lines))
        fh.truncate()


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

        clean_hips()
        generate_hips()
        update_hips_properties()


if __name__ == '__main__':
    cli()
