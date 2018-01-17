#!/usr/bin/env python
import os
import hashlib
from pathlib import Path
from shutil import copyfile
import yaml
import jinja2
import click

CONFIG = yaml.load(open('config.yaml'))
VERSION = CONFIG['version']
HGPS_ANALYSIS_DIR = Path(os.environ['HGPS_ANALYSIS'])
HGPS_DATA_DIR = Path(os.environ['HGPS_DATA'])
FILENAME_CAT = f'hgps_catalog_v{VERSION}.fits.gz'


@click.group()
def cli():
    """HGPS public webpage CLI.

    This script is a static webpage generator that has the goal to make it
    simple and quick to make an updated version, and to make it hard to
    make some mistake, like forgetting to update a version number or accidentally
    publishing the wrong data files.

    Making a new version of the webpage usually consists of the following steps:
    edit `config.yaml`, then run `clean`, `build`, `archive`, `check` and `deploy`

    The `build` and `archive` steps write to folders of the same name.
    The `clean`, `check` and `deploy` steps write no local files.
    """


@cli.command()
def clean():
    """Remove build folder."""
    print('===> Executing task: clean')
    run('rm -rf build')


@cli.group()
def build():
    """Build webpage"""
    pass


@build.command('all')
@click.pass_context
def build_all(ctx):
    """Make build"""
    print('===> Executing task: build')
    ctx.invoke(build_data)
    ctx.invoke(build_images)
    ctx.invoke(build_html)


@build.command('html')
def build_html():
    """Make build/index.html"""
    print('---> build_html')
    ctx = {}
    ctx['config'] = CONFIG
    ctx['catalog'] = make_file_info(FILENAME_CAT)

    for m in CONFIG['maps']:
        filename = f'hgps_map_{m["quantity"]}_{m["radius"]}deg_v{VERSION}.fits.gz'
        m['info'] = make_file_info(filename)

    for figure in CONFIG['figures']:
        figure['info'] = make_figure_info(figure)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('src'),
        undefined=jinja2.StrictUndefined,
    )
    template = env.get_template('index.html')
    text = template.render(ctx)

    Path('build/index.html').write_text(text)

    copyfile('src/bootstrap.min.css', 'build/bootstrap.min.css')
    copyfile('src/style.css', 'build/style.css')


@build.command('data')
def build_data():
    """Make build/data"""
    print('---> build_data')
    out_path = Path('build/data')
    out_path.mkdir(exist_ok=True)
    copyfile(HGPS_ANALYSIS_DIR / 'data/catalogs/HGPS3/release/HGPS_v0.4.fits', out_path / FILENAME_CAT)

    for m in CONFIG['maps']:
        m['filename'] = f'hgps_map_{m["quantity"]}_{m["radius"]}deg_v{VERSION}.fits.gz'
        copyfile(HGPS_DATA_DIR / 'release' / m['in'], out_path / m['filename'])


@build.command('figures')
def build_figures():
    """Make build/figures"""
    print('---> build_figures')
    out_path = Path('build/figures')
    out_path.mkdir(exist_ok=True)

    for figure in CONFIG['figures']:
        filename = Path(figure['analysis_repo']).name
        copyfile(HGPS_ANALYSIS_DIR / figure['analysis_repo'], out_path / filename)

@cli.command()
def archive():
    """Archive webpage"""
    print('===> Executing task: archive')
    # TODO: Copy `build` folder to appropriately name archive/vX/
    # TODO: Print that user should run check now and then git commit


@cli.command()
def check():
    """Check webpage"""
    print('===> Executing task: check')
    # TODO: Check archive against file manifest and config (checksums & version)


@cli.command()
def deploy():
    """Deploy webpage"""
    print('===> Executing task: deploy')
    # TODO: implement


def run(cmd):
    """Helper function to echo and run a shell command."""
    from subprocess import call
    print('Executing: {}'.format(cmd))
    call(cmd, shell=True)


def make_file_info(filename):
    info = dict()
    info['filename'] = filename
    info['path'] = 'data/' + info['filename']
    path = Path('build') / info['path']
    mb = path.stat().st_size / 1024 ** 2
    info['filesize'] = f'{mb:.1f} MB'
    md5 = hashlib.md5(path.read_bytes()).hexdigest()
    info['md5'] = md5
    info['html'] = '<a href="{path}" download>{filename}</a> ({filesize}, MD5: {md5})'.format_map(info)
    return info


def make_figure_info(figure):
    info = dict()
    info['filename_pdf'] = figure['hgps_paper']
    info['html'] = '<a href="{filename_pdf}">{filename_pdf}</a>'.format_map(info)
    return info


if __name__ == '__main__':
    cli()
