"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file provides a simple, speedy parser for Freelancer-style
INI files, which are used to store all information about the game
world.

Freelancer actually stores INIs in a compressed binary-INI (BINI)
format, but will accept text INIs happily. This is therefore the
format most used by mods as it facilitates editing.

This file is intended to be the main interface for accessing INI
*and* BINI functions, as it contains higher-level functions as well
as logic for checking whether a .ini file is an INI or a BINI.
"""
from typing import Union, List, Dict, Any, Tuple
from collections import defaultdict
from functools import lru_cache
import concurrent.futures
import itertools
import warnings

from . import bini


@lru_cache(64)
def sections(paths: Union[str, Tuple[str]], fold_sections=False, fold_values=True) -> Dict[str, Any]:
    """Parse the Freelancer-style INI file(s) at `paths` and group sections of the same name together.

    THe result is a dict mapping a section name to a list of dictionaries representing the contents of each section
    "instance". If `fold_sections` is true, this list will be "folded" into one dict for sections with only one
    instance.

    If `fold_values` is true (the default), the same logic applies to entries and their values: if an entry is only
    defined once in a section, its value is "folded" into a primitive (a float, int, bool or string) rather than being a
    list."""
    return fold_dict(parse(paths, fold_values), fold_sections)


def parse(paths: Union[str, Tuple[str]], fold_values=True) -> List[Tuple[str, Dict[str, Any]]]:
    """Parse an INI file, or a collection of INIs, to a list of tuples of the form (section_name, section_contents),
    where section_contents is a dict of the entries in that section. If fold_values is true (the default), the
    entries dict will be "folded" (see the docstring for `fold_dict`)."""
    if isinstance(paths, str):  # accept both single paths and tuples of paths
        paths = [paths]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        sections_ = itertools.chain(*executor.map(parse_file, paths))

    return [(name, fold_dict(entries, fold_values)) for name, entries in filter(None, sections_)]


def group(paths: Union[str, Tuple[str]], fold_sections=True, fold_values=True):
    """Similar to `parse` but groups contiguous sequences of the same section name together."""
    groups = itertools.groupby(parse(paths, fold_values), key=lambda pair: pair[0])  # group by section name
    return [next(iter(fold_dict(contents, fold_sections).items())) for key, contents in groups]


def parse_file(path: str):
    """Takes a path to an INI or BINI file and outputs a list of tuples containing a section name and a list of tuples
    of entry/value pairs."""
    if bini.is_bini(path):
        return bini.parse_file(path)
    with open(path, encoding='windows-1252') as f:
        contents = f.read().lower()  # files are case insensitive
    contents.replace(DELIMITER_COMMENT + SECTION_NAME_START, '')  # delete commented section markers
    return list(map(parse_section, contents.split(SECTION_NAME_START)))


def parse_section(section: str):
    """Takes a raw section string (minus the [) and outputs a tuple containing the section name and a list of tuples
    of entry/value pairs. If the section is invalid, an empty tuple will be returned."""
    section_name, delimiter, entries = section.partition(SECTION_NAME_END)
    if not delimiter or (DELIMITER_COMMENT in section_name):
        return ()
    try:
        return section_name, list(map(parse_entry, entries.splitlines()))
    except ValueError as e:  # an entry with a syntax error invalidates the whole section
        warnings.warn(f"Couldn't parse line in section {section_name!r}; {e.args[0]}")
        return ()


def parse_entry(entry: str):
    """Takes an entry string consisting of a delimiter separated key/value pair and outputs a tuple of the
    name and value. If the entry is invalid, an empty tuple will be returned."""
    entry = entry.split(DELIMITER_COMMENT, 1)[0].replace(' ', '').replace('\t', '')  # remove comments and whitespace
    key, delimiter, value = entry.partition(DELIMITER_KEY_VALUE)
    if not delimiter or key == 'comment':  # if this isn't a valid entry line after all
        return ()
    return key, parse_value(value)


def parse_value(entry_value: str) -> Union[Any, Tuple]:
    """Parse an entry value (consisting either of a string, int or float or a tuple of such) using and return it as a
    Python object."""
    return tuple(map(auto_cast, entry_value.split(','))) if ',' in entry_value else auto_cast(entry_value)


def auto_cast(value: str) -> Any:
    """Interpret and coerce a string value to a Python type. If the value cannot be interpreted as a valid Python type,
    a `ValueError` will be raised."""
    if not (value[:1] == '-' or value[:1].isdigit()):  # if not a number
        if value == 'true':
            return True
        if value == 'false':
            return False
        return value
    try:
        return int(value)
    except ValueError:
        return float(value)


def fold_dict(sequence, fold_values=True) -> Dict[str, Any]:
    """Construct a dict out of a sequence of tuples of the form (key, value). If `fold_values` is false, or multiple
    values are given for the same key, those values are collected into a list. If `fold_values` is true (the default),
    the value for keys with only one value (i.e. they appear only once in the sequence) are "folded" into a primitive
    instead of being a list of one element."""
    d = dict() if fold_values else defaultdict(list)

    for key, value in filter(None, sequence):
        if not fold_values or (key in d and type(d[key]) is list):
            d[key].append(value)
        elif key in d:
            d[key] = [d[key], value]
        else:
            d[key] = value
    return d


DELIMITER_KEY_VALUE = '='
DELIMITER_COMMENT = ';'
SECTION_NAME_START = '['
SECTION_NAME_END = ']'
