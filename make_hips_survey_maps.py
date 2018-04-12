"""Gnerate HIPS maps from the HGPS survey FITS maps.



"""
import subprocess
import os
import logging
import tempfile
from make_extra_survey_maps import get_sky_image

logging.basicConfig(level='INFO')
log = logging.getLogger(__name__)
ALADIN_JAR_PATH = os.environ.get('ALADIN_JAR')

HIPSGEN_OPTIONS = {'creator_did': 'HiPSID',
                   'blank': '0',
                   }


def generate_hips(quantity):
    image = get_sky_image(quantity, normed=False)
    filename = tempfile.NamedTemporaryFile(suffix='.fits').name
    image.write(filename)

    options = {}
    options['in'] = filename
    options['out'] = f'./HGPS_HiPS_{quantity}'

    if quantity == 'flux':
        options['hips_pixel_cut'] = '"1e-14 1e-12 log"'
    elif quantity == 'significance':
        options['hips_pixel_cut'] = '"0 100 log"'

    options.update(HIPSGEN_OPTIONS)

    hipsgen_options = ''
    for key, value in options.items():
        hipsgen_options += f' {key}={value}'

    cmd = f'java -Xmx1400m -jar {ALADIN_JAR_PATH} -hipsgen {hipsgen_options}'
    log.info(f'Executing command {cmd}')
    subprocess.call(cmd, shell=True)


def view_hips(quantity):
    hips_out_folder = f'./HGPS_HiPS_{quantity}'
    cmd = f'java -jar {ALADIN_JAR_PATH} {hips_out_folder}'
    log.info(f'Executing command {cmd}')
    subprocess.call(cmd, shell=True)


def clean_hips(quantity):
    hips_out_folder = f'HGPS_HiPS_{quantity}'
    cmd = f'rm -r {hips_out_folder}'
    log.info(f'Executing command {cmd}')
    subprocess.call(cmd, shell=True)


def tar_hips(quantity):
    hips_out_folder = f'HGPS_HiPS_{quantity}'
    cmd = f'tar cfvz {hips_out_folder}.tar.gz {hips_out_folder}'
    log.info(f'Executing command {cmd}')
    subprocess.call(cmd, shell=True)


if __name__ == '__main__':
    quantity = 'flux'  # 'flux'
    clean_hips(quantity)
    generate_hips(quantity)
    view_hips(quantity)
    tar_hips(quantity)
    clean_hips(quantity)
