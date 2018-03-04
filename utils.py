from collections import OrderedDict
import logging
from pathlib import Path
import json
import numpy as np
from subprocess import call

log = logging.getLogger(__name__)


def run(cmd):
    """Helper function to echo and run a shell command."""
    print('Executing: {}'.format(cmd))
    call(cmd, shell=True)


def load_json(path):
    """Helper function to load data from a JSON file."""
    path = Path(path)
    log.debug('Reading {}'.format(path))
    with path.open() as fh:
        data = json.load(fh, object_pairs_hook=OrderedDict)
    return data


def write_json(data, path):
    """Helper function to write data to a JSON file."""
    path = Path(path)
    log.info('Writing {}'.format(path))
    with path.open('w') as fh:
        json.dump(data, fh, indent=4)


def table_to_list_of_dict(table):
    """Convert table to list of dict."""
    rows = []
    for row in table:
        data = OrderedDict()
        for name in table.colnames:
            val = row[name]
            if isinstance(val, np.int64):
                val = int(val)
            elif isinstance(val, np.int32):
                val = int(val)
            elif isinstance(val, np.bool_):
                val = bool(val)
            elif isinstance(val, np.float):
                val = float(val)
            elif isinstance(val, np.float32):
                val = float(val)
            elif isinstance(val, np.str):
                val = str(val)
            elif isinstance(val, np.ndarray):
                vals = [float(_) for _ in val]
                val = list(vals)
            else:
                raise ValueError('Unknown type: {} {}'.format(val, type(val)))
            data[name] = val

        rows.append(data)

    return rows
