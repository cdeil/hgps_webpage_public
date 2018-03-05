#!/usr/bin/env python
from pathlib import Path
from astropy.io import fits
from astropy.table import Table
from gammapy.catalog import SourceCatalogHGPS
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
def cli_tables():
    """Dump all HGPS tables to text files.

    The purpose is to have the complete content under version control.
    """
    filename = config.out_path / config.filename_cat
    print(f'Reading {filename}')
    hdu_list = fits.open(str(filename))

    path = Path('checks/tables')
    path.mkdir(exist_ok=True, parents=True)

    # Dump all header content to text files
    for hdu in hdu_list:
        txt = hdu.header.tostring(sep='\n', padding=False)
        path = Path(f'checks/tables/{hdu.name}_header.txt')
        print(f'Writing {path}')
        path.write_text(txt)

    # Dump all data content to text (JSON) files
    for hdu in hdu_list[1:]:
        table = Table.read(hdu)
        data = utils.table_to_list_of_dict(table)
        path = Path(f'checks/tables/{hdu.name}.json')
        print(f'Writing {path}')
        utils.write_json(data, path)


@cli.command('sources-txt')
def cli_sources_txt():
    """Dump all HGPS source information via Gammapy"""
    filename = config.out_path / config.filename_cat
    print(f'Reading {filename}')
    cat = SourceCatalogHGPS(filename)

    for idx, source in enumerate(cat):
        text = str(source)

        filename = f'checks/sources-txt/{idx:03d}.txt'
        print(f'Writing {filename}')
        Path(filename).write_text(text)


@cli.command('sources-spec')
def cli_sources_spec():
    pass
    # import IPython; IPython.embed()


if __name__ == '__main__':
    cli()
