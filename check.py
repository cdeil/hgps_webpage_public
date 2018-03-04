#!/usr/bin/env python
from astropy.io import fits
import click
import utils
from make import config


@click.group()
def cli():
    """Automated checks for release files.

    Most checks work by writing to the `checks` folder.
    """
    pass


@cli.command('tables')
def check_dump_tables_to_text():
    """Dump all HGPS tables to text files.

    The purpose is to have the complete content under version control.
    """
    filename = config.out_path / config.filename_cat
    print(f'Reading {filename}')
    hdu_list = fits.open(str(filename))
    import IPython; IPython.embed()


if __name__ == '__main__':
    cli()
