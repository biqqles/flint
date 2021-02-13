"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from types import FunctionType
from typing import Dict, Any
from functools import wraps
import warnings

warnings.formatwarning = lambda message, *args, **kwargs: f'{message!s}\n'  # patch formatter to only show message
central_cache: Dict[FunctionType, Dict[tuple, Any]] = {}


def cached(function):
    """A decorator which caches a function to the central cache."""
    central_cache[function] = {}  # initialise cache

    @wraps(function)
    def wrapped(*args):
        function_cache = central_cache[function]
        if args in function_cache:
            return function_cache[args]
        result = function_cache[args] = function(*args)
        return result
    return wrapped


from .paths import set_install_path, install_path_set
from .routines import get_commodities, get_bases, get_equipment, get_ships, get_systems, get_factions, get_goods


shorthand = {'bases': get_bases,
             'commodities': get_commodities,
             'equipment': get_equipment,
             'factions': get_factions,
             'goods': get_goods,
             'ships': get_ships,
             'systems': get_systems}


def __getattr__(name):
    """Implement shorthand (property-like syntax) for Python 3.7 and up. This function is only called if a name
    cannot be resolved directly."""
    if name in shorthand:
        assert install_path_set(), 'No game path set'
        return shorthand[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
