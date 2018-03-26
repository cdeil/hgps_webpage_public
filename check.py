#!/usr/bin/env python
import functools
from pathlib import Path
from astropy.io import fits
from astropy.table import Table
from gammapy.catalog import SourceCatalogHGPS, SourceCatalogGammaCat
import matplotlib
import click
import utils
from make import config

matplotlib.use('agg')


@functools.lru_cache()
def get_hgps_cat():
    filename = config.out_path / config.filename_cat
    print(f'Reading {filename}')
    return SourceCatalogHGPS(filename)


@functools.lru_cache()
def get_gamma_cat():
    filename = '$GAMMA_CAT/output/gammacat.fits.gz'
    print(f'Reading {filename}')
    return SourceCatalogGammaCat(filename)


def get_gamma_cat_source_for_hgps_source(source):
    if source.data['Analysis_Reference'] != 'EXTERN':
        return None

    gc_id = source.data["Gamma_Cat_Source_ID"]
    if (gc_id == '') or (',' in gc_id):
        return None

    gc_id = int(gc_id)

    cat = get_gamma_cat()
    # import IPython; IPython.embed(); 1/0
    row_idx = list(cat.table['source_id']).index(gc_id)
    gc_source = cat[row_idx]

    print('HGPS source:', source.name)
    print('Gamma-cat source:', gc_source.name)
    return gc_source


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
    cat = get_hgps_cat()

    for source in cat:
        text = str(source)

        filename = f'checks/sources-txt/{source.index:03d}.txt'
        print(f'Writing {filename}')
        Path(filename).write_text(text)


@cli.command('sources-spec')
def cli_sources_spec():
    """Plot spectrum for each source."""
    cat = get_hgps_cat()

    for source in cat:
        plot_spec(source, show_gamma_cat=False)
        # break


@cli.command('gammapy')
def cli_gammapy():
    """Checks for Gammapy."""
    cat = get_hgps_cat()

    # [_.spectrum_type for _ in cat]

    for source in cat:
        source.spectral_model('pl')


def plot_spec(source, show_gamma_cat):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()

    energy_range = source.energy_range
    opts = dict(ax=ax, energy_range=energy_range, energy_power=2)

    # Always show PL
    model = source.spectral_model('pl')
    model.plot_error(alpha=0.5, facecolor='gray', **opts)
    model.plot(color='gray', alpha=0.8, lw=2, **opts)

    # Show ECPL in addition if significant
    if source.spectral_model_type == 'ecpl':
        model = source.spectral_model('ecpl')
        model.plot_error(alpha=0.5, facecolor='green', **opts)
        model.plot(color='green', alpha=0.8, lw=2, **opts)

    source.flux_points.plot(
        ax=ax, energy_power=2, markeredgecolor='None', marker='o',
        markersize=4, capsize=0, color='0.3', zorder=10,
    )

    if show_gamma_cat:
        extern_source = get_gamma_cat_source_for_hgps_source(source)
        if extern_source is not None:
            # import IPython; IPython.embed()
            if extern_source.data['spec_type'] != 'none':
                extern_source.spectral_model.plot(
                    ax=ax, energy_range=energy_range, energy_power=2,
                    color='red', alpha=0.1, lw=2,
                )

            if extern_source.data['sed_n_points'] != 0:
                extern_source.flux_points.plot(
                    ax=ax, energy_power=2, markeredgecolor='None', marker='o',
                    markersize=4, capsize=0, color='red', zorder=10, alpha=0.5,
                )

    title = (
        f'HGPS: row {source.index}; {source.name}; {source.data["Identified_Object"]}\n'
        f'Ref: {source.data["Analysis_Reference"]}; gamma-cat: {source.data["Gamma_Cat_Source_ID"]}'
    )

    ax.set_title(title)
    ax.set_xlabel('Energy (TeV)')
    ax.set_ylabel(r'E$^2$ x F (erg cm$^{-2}$ s$^{-1}$)')
    ax.set_xlim(0.11, 80)
    ax.set_ylim(0.3e-13, 4e-11)
    ax.grid('on')
    fig.tight_layout()

    filename = f'checks/sources-spec/{source.index:03d}.png'
    print(f'Writing {filename}')
    fig.savefig(filename)
    plt.close()


if __name__ == '__main__':
    cli()
