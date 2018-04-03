#!/usr/bin/env python
import os
import hashlib
from pathlib import Path
from shutil import copyfile
import datetime
import yaml
import jinja2
import click
import utils


# TODO: pre-compute everything in `config` and only pass that to the template render
# Get rid of the other bullshit and review for duplicated code

class Config:
    def __init__(self):
        self.config = yaml.load(open('config.yaml'))
        self.version = self.config['version']
        self.hgps_paper_dir = Path(os.environ['HGPS_PAPER'])
        self.hgps_analysis_dir = Path(os.environ['HGPS_ANALYSIS'])
        self.hgps_data_dir = Path(os.environ['HGPS_DATA'])
        self.filename_cat = f'hgps_catalog_v{self.version}.fits.gz'
        self.out_path = Path('build/data')

        for m in self.config['maps']:
            filename = f'hgps_map_{m["quantity"]}_{m["radius"]}deg_v{self.version}.fits.gz'
            m['info'] = self.make_file_info(filename)

        for figure in self.config['figures']:
            figure['info'] = self.make_figure_info(figure)

        for figure in self.config['figures_extra']:
            figure['info'] = self.make_figure_info_extra(figure)

        if self.config['page_update_date'] == 'today':
            self.config['page_update_date'] = datetime.date.today().strftime('%B %d, %Y')

    @property
    def html_context(self):
        ctx = {}
        ctx['config'] = self.config
        ctx['catalog'] = self.make_file_info(self.filename_cat)
        return ctx

    @staticmethod
    def make_file_info(filename):
        info = dict()
        info['filename'] = filename
        info['path'] = 'data/' + info['filename']
        path = Path('build') / info['path']
        fs = path.stat().st_size
        if fs > 1024 ** 2:
            info['filesize'] = f'{fs//1024**2} MB'
        else:
            info['filesize'] = f'{fs//1024} kB'
        # md5 = hashlib.md5(path.read_bytes()).hexdigest()
        # info['md5'] = md5
        # Note: I decided to remove filesize here, not used.
        info['html'] = '<a href="{path}" download>{filename}</a>'.format_map(info)
        return info

    @staticmethod
    def make_figure_info(figure):
        info = dict()
        info['number'] = figure['number']
        info['fn_pdf'] = Path('figures') / figure['webpage_repo']
        info['text_pdf'] = figure['webpage_repo']
        info['fn_png'] = info['fn_pdf'].with_suffix('.png')
        info['html'] = 'Figure {number}: <a href="{fn_pdf}">{text_pdf}</a>, <a href="{fn_png}">PNG</a>'.format_map(info)
        return info

    @staticmethod
    def make_figure_info_extra(figure):
        info = dict()
        info['html'] = f'{figure["description"]}: <a href="figures/{figure["filename"]}">{figure["filename"]}</a>'
        return info


config = Config()


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
    utils.run('rm -rf build')


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
    ctx.invoke(build_figures)
    ctx.invoke(build_html)


@build.command('html')
def build_html():
    """Make build/index.html"""
    print('---> build_html')

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('src'),
        undefined=jinja2.StrictUndefined,
    )
    template = env.get_template('index.html')
    text = template.render(config.html_context)
    Path('build/index.html').write_text(text)

    copyfile('src/bootstrap.min.css', 'build/bootstrap.min.css')
    copyfile('src/style.css', 'build/style.css')


@build.command('data')
def build_data():
    """Make build/data"""
    print('---> build_data')
    config.out_path.mkdir(exist_ok=True)
    src = config.hgps_analysis_dir / 'data/catalogs/HGPS3/release/HGPS_v0.4.fits.gz'
    target = config.out_path / config.filename_cat
    print(f'cp {src} {target}')
    copyfile(src, target)

    for m in config.config['maps']:
        m['filename'] = f'hgps_map_{m["quantity"]}_{m["radius"]}deg_v{config.version}.fits.gz'
        src = config.hgps_data_dir / 'release' / m['in']
        target = config.out_path / m['filename']
        print(f'cp {src} {target}')
        copyfile(src, target)


@build.command('figures')
def build_figures():
    """Make build/figures"""
    print('---> build_figures')
    out_path = Path('build/figures')
    out_path.mkdir(exist_ok=True)

    for figure in config.config['figures']:
        # Copy figures in PDF format
        src = config.hgps_analysis_dir / figure['analysis_repo']
        dst = out_path / figure['webpage_repo']
        print(f'cp {src} {dst}')
        copyfile(src, dst)

        # Copy figures in PNG format
        src = src.with_suffix('.png')
        dst = dst.with_suffix('.png')

        print(f'cp {src} {dst}')
        copyfile(src, dst)


@cli.command()
def archive():
    """Archive webpage"""
    print('===> Executing task: archive')
    # TODO: Copy `build` folder to appropriately name archive/vX/
    # TODO: Print that user should run check now and then git commit


@cli.command()
def deploy():
    """Deploy webpage"""
    print('===> Executing task: deploy')
    # TODO: implement


if __name__ == '__main__':
    cli()
