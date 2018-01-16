#!/usr/bin/env python
import click


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


@cli.command()
def build():
    """Build webpage"""
    print('===> Executing task: build')
    build_html()
    build_data()
    build_images()


def build_html():
    print('---> build_html')
    # TODO: copy & fill templates in `build`


def build_data():
    print('---> build_data')
    # TODO: copy data files in `build/data`


def build_images():
    print('---> build_images')
    # TODO: copy image files in `build/images`


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


if __name__ == '__main__':
    cli()
