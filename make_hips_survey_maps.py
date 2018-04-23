#!/usr/bin/env python
"""Generate HIPS for HGPS."""
import subprocess
import os
import logging
from collections import OrderedDict
from pathlib import Path
import click
from make_extra_survey_maps import get_sky_image

log = logging.getLogger(__name__)

HIPSGEN_OPTIONS = {
    'creator_did': 'ivo://XXX',
    'blank': '0',
}

HIPS_META_INFO = {
    'obs_regime': 'Gamma-ray',
    'obs_collection': 'HGPS',
    'obs_title': 'HGPS Integral Flux >1TeV',
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
    'hips_creator': 'XXX (A.Donath and C.Deil)',
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

config = Config()


def prepare_inputs():
    """Prepare input files for hipsgen"""
    image = get_sky_image(config.quantity, normed=False)
    filename = config.in_fits
    log.info(f'Writing {filename}')
    image.write(filename)


def get_aladin_jar():
    if 'ALADIN_JAR' not in os.environ:
        os.environ['ALADIN_JAR'] = '/Users/deil/software/bin/Aladin.jar'
        # raise EnvironmentError('You have to set an environment variable ALADIN_JAR')

    return os.environ['ALADIN_JAR']


def run_hipsgen(hipsgen_options):
    aladin_jar = get_aladin_jar()
    cmd = f'java -Xmx1400m -jar {aladin_jar} -hipsgen {hipsgen_options}'
    log.info(f'Executing command {cmd}')
    subprocess.call(cmd, shell=True)


def generate_hips():
    options = {}
    options['in'] = config.in_fits
    options['out'] = config.out_path

    if config.quantity == 'flux':
        options['hips_pixel_cut'] = '"1e-14 1e-12 log"'
    elif config.quantity == 'significance':
        options['hips_pixel_cut'] = '"0 100 log"'

    options.update(HIPSGEN_OPTIONS)

    hipsgen_options = ''
    for key, value in options.items():
        hipsgen_options += f' {key}={value}'

    run_hipsgen(hipsgen_options)


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
            if key.replace('#', '') in HIPS_META_INFO:
                key = key.replace('#', '')
            properties[key] = value

        properties.update(HIPS_META_INFO)
        fh.seek(0)
        lines = ["{key:20s} = {value}".format(key=key, value=value) for key, value in properties.items()]
        lines.append(footer)
        fh.write('\n'.join(lines))
        fh.truncate()


@click.command()
@click.option('--quantity', default='significance', type=click.Choice(['significance', 'flux']))
def cli(quantity):
    """Generate HIPS for HGPS."""
    logging.basicConfig(level='INFO')
    config.quantity = quantity
    config.in_path.mkdir(parents=True, exist_ok=True)
    config.out_path.mkdir(parents=True, exist_ok=True)

    prepare_inputs()

    clean_hips()
    generate_hips()
    update_hips_properties()


if __name__ == '__main__':
    cli()
