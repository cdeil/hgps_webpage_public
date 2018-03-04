#!/usr/bin/env python
from pathlib import Path
from astropy.io import fits
from astropy.table import Table
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

    path = Path('checks/tables')
    path.mkdir(exist_ok=True, parents=True)

    for hdu in hdu_list[1:]:
        # import IPython; IPython.embed()
        table = Table.read(hdu)
        data = utils.table_to_list_of_dict(table)
        path = Path(f'checks/tables/{hdu.name}.json')
        print(f'Writing {path}')
        utils.write_json(data, path)

    # import IPython; IPython.embed()


if __name__ == '__main__':
    cli()
