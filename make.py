#!/usr/bin/env python
import os
import hashlib
from pathlib import Path
from shutil import copyfile
import yaml
import jinja2
import click


def run(cmd):
    """Helper function to echo and run a shell command."""
    from subprocess import call
    print('Executing: {}'.format(cmd))
    call(cmd, shell=True)


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

        for m in self.config['maps']:
            filename = f'hgps_map_{m["quantity"]}_{m["radius"]}deg_v{self.version}.fits.gz'
            m['info'] = self.make_file_info(filename)

        for figure in self.config['figures']:
            figure['info'] = self.make_figure_info(figure)

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
        mb = path.stat().st_size / 1024 ** 2
        info['filesize'] = f'{mb:.1f} MB'
        # md5 = hashlib.md5(path.read_bytes()).hexdigest()
        # info['md5'] = md5
        info['html'] = '<a href="{path}" download>{filename}</a> ({filesize})'.format_map(info)
        return info

    @staticmethod
    def make_figure_info(figure):
        info = dict()
        info['number'] = figure['number']
        info['filename_pdf'] = figure['paper_repo']
        info['text_pdf'] = info['filename_pdf'].split('/')[-1]
        info['filename_png'] = info['filename_pdf'].replace('.pdf', '.png')
        info[
            'html'] = 'Figure {number}: <a href="{filename_pdf}">{text_pdf}</a>, <a href="{filename_png}">PNG</a>'.format_map(
            info)
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
    ctx.invoke(build_figures)
    ctx.invoke(build_notebook)
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

    out_path = Path('build/data')
    out_path.mkdir(exist_ok=True)
    copyfile(config.hgps_analysis_dir / 'data/catalogs/HGPS3/release/HGPS_v0.4.fits', out_path / config.filename_cat)

    for m in config.config['maps']:
        m['filename'] = f'hgps_map_{m["quantity"]}_{m["radius"]}deg_v{config.version}.fits.gz'
        copyfile(config.hgps_data_dir / 'release' / m['in'], out_path / m['filename'])


@build.command('figures')
def build_figures():
    """Make build/figures"""
    print('---> build_figures')
    out_path = Path('build/figures')
    out_path.mkdir(exist_ok=True)

    for figure in config.config['figures']:
        filename = Path(figure['paper_repo']).name
        copyfile(config.hgps_analysis_dir / figure['analysis_repo'], out_path / filename)


@build.command('notebook')
def build_notebook():
    """Make notebook ipynb and HTML in build/data.

    https://nbconvert.readthedocs.io/en/latest/nbconvert_library.html
    """
    print('---> build_notebook')
    import nbformat
    import nbconvert

    hgps_nb_version = 'v1'  # not coupled to the data file version; update here as needed

    nb = nbformat.read('src/hgps_notebook.ipynb', nbformat.NO_CONVERT)

    # Make the HTML version
    source, meta = nbconvert.HTMLExporter().from_notebook_node(nb)
    path = Path(f'build/data/hgps_notebook_{hgps_nb_version}.html')
    print('Writing {}'.format(path))
    path.write_text(source, encoding='utf-8')

    # Make the ipynb version
    source, meta = nbconvert.NotebookExporter().from_notebook_node(nb)
    path = Path(f'build/data/hgps_notebook_{hgps_nb_version}.ipynb')
    print('Writing {}'.format(path))
    path.write_text(source, encoding='utf-8')


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


if __name__ == '__main__':
    cli()
