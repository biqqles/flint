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
"""
from typing import Union, List, Set
from collections import defaultdict
from functools import lru_cache
import os
import warnings

from . import bini


@lru_cache
def parse(paths: Union[str, List[str]], target_section: str = '', fold_values=True):
    """Parse the Freelancer-style INI file(s) at `paths`.

    INIs are parsed to a dictionary of section names mapping to a list of dicts representing the entries of those
    sections. In other words, {section_name -> [{entry_name -> entry_value}]}.

    If an entry appears multiple times in a section (i.e. it has multiple values) its value becomes a list of those
    values, while entries with single values are "folded" into primitives. If `fold_values` is False, all entry values
    will be lists. This aids with processing in some cases."""
    result = defaultdict(list)

    if isinstance(paths, str):  # accept both single paths and lists of paths
        paths = [paths]

    for path in paths:
        assert os.path.isfile(path)
        with open(path, 'rb') as f:
            data = f.read(4)
            if data[:4] == b'BINI':
                bini_data = bini.parse(path, fold_values)
                return bini_data if not target_section else bini_data[target_section]
            f.seek(0)
            data = f.read()
        raw = data.decode('windows-1252').lower()
        raw = raw.replace(DELIMITER_COMMENT + SECTION_NAME_START, '')  # delete commented section markers

        sections = raw.split(SECTION_NAME_START)
        for s in sections:
            try:
                section_name, delimiter, entries = s.partition(SECTION_NAME_END)
                if not delimiter or (DELIMITER_COMMENT in section_name) or \
                        (target_section and section_name != target_section):
                    continue
                section_entries = {}
                for entry in entries.splitlines():
                    # discard comments and whitespace, then split into key-value pairs
                    entry = entry.split(DELIMITER_COMMENT, 1)[0].replace(' ', '').replace('\t', '')
                    key, delimiter, value = entry.partition(DELIMITER_KEY_VALUE)
                    if not delimiter:
                        continue

                    value = parse_value(value)

                    # if key is new, add value to dictionary. If it has been seen before, add value to list instead
                    if fold_values and key not in section_entries:
                        section_entries[key] = value
                    elif not isinstance(section_entries.get(key), list):
                        section_entries[key] = [section_entries[key], value] if fold_values else [value]
                    else:
                        section_entries[key].append(value)
                result[section_name].append(section_entries)
            except ValueError as e:
                warnings.warn(f"Couldn't parse line in {path!r}; {e.args[0]}")
                continue
    return result if not target_section else result[target_section]


def fetch(paths: Union[str, List[str]], target_section: str, target_keys: Set[str]):
    """Fetch only a specified section (`target_section`) and keys (`target_keys`) from the Freelancer-style INI file(s)
    at `paths`.

    Sections and keys which do not match the targets are dropped. The result is a list of dictionaries of matching keys
    and their values for each section instance."""
    parsed = parse(paths)
    result = []
    for section_name, sections in parsed.items():
        if section_name == target_section:
            for entries in sections:
                matching_entries = {n: v for n, v in entries.items() if n in target_keys}
                result.append(matching_entries)
    return result


def parse_value(entry_value: str):
    """Parse an entry value (consisting either of a string, int or float or a tuple of such) using and return it as a
    Python object."""
    def auto_cast(v: str):
        if not (v[:1] == '-' or v[:1].isdigit()):
            return v
        try:
            return int(v)
        except ValueError:
            return float(v)

    return tuple(map(auto_cast, entry_value.split(','))) if ',' in entry_value else auto_cast(entry_value)


DELIMITER_KEY_VALUE = '='
DELIMITER_COMMENT = ';'
SECTION_NAME_START = '['
SECTION_NAME_END = ']'
