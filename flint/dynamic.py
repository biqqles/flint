"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file implements the features of dynamic programming used by
flint.
"""
import datetime
import os
import pickle
from dataclasses import dataclass
from functools import wraps
from types import FunctionType
from typing import Any, Dict

central_cache: Dict[FunctionType, Dict[tuple, Any]] = {}
cache_path = 'flint.dat'


def write_cache():
    #central_cache.saved = datetime.datetime.utcnow()
    with open(cache_path, 'wb') as f:
        pickle.dump(central_cache, f, protocol=4)


def load_cache(expiry_period_days=7):
    if os.path.isfile(cache_path):
        with open(cache_path, 'rb') as f:
            # noinspection PyBroadException
            # try to load the pickle from file. If it can't be loaded, for any reason, force a reload
            try:
                global central_cache
                if datetime.datetime.utcnow() < central_cache.saved + datetime.timedelta(days=expiry_period_days):
                    central_cache = pickle.load(f)
            except Exception:
                return


def cached(function):
    """A decorator which caches a function to the central cache."""
    name = function.__module__ + function.__name__
    central_cache[name] = {}  # initialise cache  # todo: should hash function but pickle is having issues

    @wraps(function)
    def wrapped(*args):
        function_cache = central_cache[function.__module__ + function.__name__]
        if args in function_cache:
            return central_cache[function.__module__ + function.__name__][args]
        result = function_cache[args] = function(*args)
        return result
    return wrapped


# noinspection PyPep8Naming
class cached_property:
    """A decorator that replaces the method it is applied to with a property which, when queried, replaces itself
    with its result, thus "caching" it."""
    ___slots___ = ('method',)

    def __init__(self, method):
        self.method = method

    def __get__(self, instance, owner):
        result = self.method(instance)
        setattr(instance, self.method.__name__, result)
        return result


class CachedDataclass(type):
    """A metaclass that applies the builtin `dataclass` decorator to the given class and the `cached_property`
    decorator defined within to all its methods."""
    # todo probably re-implement dataclass myself to use __slots__
    def __new__(mcs, name, bases, dict_):
        """Modify `__dict__` by wrapping non-builtin methods in `cached_property`, then apply `dataclass` and return."""
        return dataclass(super().__new__(mcs, name, bases, dict_), eq=False)

