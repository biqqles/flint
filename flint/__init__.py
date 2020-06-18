"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import warnings
from . import paths
from .routines import get_commodities, get_bases, get_equipment, get_ships, get_systems, get_factions, get_goods

warnings.formatwarning = lambda message, *args, **kwargs: f'{message!s}\n'  # patch formatter to only show message

shorthand = {'bases': get_bases,
             'commodities': get_commodities,
             'equipment': get_equipment,
             'factions': get_factions,
             'goods': get_goods,
             'ships': get_ships,
             'systems': get_systems}


# shorthand for Python 3.7 and up
def __getattr__(name):
    if not paths.install:
        raise AssertionError('No path set')
    if name in shorthand:
        return shorthand[name]()
    raise AttributeError
