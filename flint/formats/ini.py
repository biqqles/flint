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
format most used by mods
"""
import os
from collections import defaultdict
from typing import Any, Union, List
import warnings

from . import bini

DELIMITER_KEY_VALUE = '='
DELIMITER_COMMENT = ';'
SECTION_NAME_START = '['
SECTION_NAME_END = ']'


def parse(paths: Union[str, List[str]], target_section: str = '', fold_values=True):
    """Interpret the inis in `paths` and return a parsed representation of their structure:
    If `fold_values` is True, fold keys with single values into single types (not lists), if False all values
    will be lists. The former is more consistent, so easier to process with minimal code, the latter is more useful
    when the individual values are important."""
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

        sections = raw.split(SECTION_NAME_START)
        for s in sections:
            section_name, delimiter, entries = s.partition(SECTION_NAME_END)
            if not delimiter or (target_section and section_name != target_section):
                continue
            section_entries = {}
            for entry in entries.splitlines():
                # discard comments and whitespace, then split into key-value pairs
                entry = entry.split(DELIMITER_COMMENT, 1)[0].replace(' ', '').replace('\t', '')
                key, delimiter, value = entry.partition(DELIMITER_KEY_VALUE)
                if not delimiter:
                    continue

                try:
                    value = parse_value(value)
                except ValueError as e:
                    warnings.warn(f"Couldn't parse line {entry!r} in file {path!r}; {e.args[0]}")
                    continue

                # if key is new, add value to dictionary. If it has been seen before, add value to list instead
                if fold_values and key not in section_entries:
                    section_entries[key] = value
                elif not isinstance(section_entries.get(key), list):
                    section_entries[key] = [section_entries[key], value] if fold_values else [value]
                else:
                    section_entries[key].append(value)
            result[section_name].append(section_entries)
    return result if not target_section else result[target_section]


def fetch(paths: Any, target_section: str, keys: set = frozenset(), multivalued_keys: set = frozenset(),
          target_key: str = None):
    """A simple, speedy parser for Freelancer-style INIs.

    Freelancer-style INIs have a number of features that make them unsuitable for use with Python's built-in
    configparser, most importantly repeated section names and repeated (in other words, multi-valued) keys.

    paths - a path to, or list thereof, the ini(s) to be parsed
    target_section - the name of the section to be matched (case sensitive)
    keys - a set of keys to get the values of (case sensitive)
    multivalued_keys - a set of keys for which multiple values are expected (duplicate keys in the section) (case sensitive)
    target_key - a key that the section must have to be matched (case sensitive)
    form_dict - form a lookup table instead of a list of dictionaries

    Returns a list of dicts, with each dict representing one matched section.
    This function aims to mimic the behaviour of Freelancer's ini parser: anything which it accepts should be accepted;
    anything else should throw an error."""

    if isinstance(paths, str):  # accept both single paths and lists of paths
        paths = [paths]

    if target_key:
        keys.add(target_key)

    result_container = []

    for path in paths:
        file_container = []
        # open file
        assert os.path.isfile(path)
        with open(path, 'rb') as f:
            data = f.read()
            # Check for 'BINI' magic number. This function can't read these files yet
            if data[:4] == b'BINI':
                raw = bini.dump(path).lower()
            else:
                raw = data.decode('windows-1252').lower()

        sections = raw.split(SECTION_NAME_START)

        for section in sections:
            if section:
                section_container = {key: [] for key in multivalued_keys}

                lines = section.splitlines()  # weirdly some files use UNIX \n and some the Windows \r\n
                section_name = lines.pop(0)[:-1]  # remove remaining ] off first line of section to reveal section name

                if section_name == target_section:
                    for line in lines:
                        # strip comments and whitespace
                        line = line.split(DELIMITER_COMMENT)[0].replace(' ', '').replace('\t', '')
                        key, delimiter, value = line.partition(DELIMITER_KEY_VALUE)  # split into key and value

                        if not delimiter:  # discard comment lines, empty lines and valueless keys
                            continue

                        try:
                            value = parse_value(value)
                        except ValueError as e:
                            warnings.warn(f"Couldn't parse line {line!r} in file {path!r}; {e.args[0]}")
                            continue

                        if key in multivalued_keys:
                            section_container[key].append(value)
                        elif key in keys:
                            section_container[key] = value

                        # break if we have everything we need from the section
                        if len(section_container) == len(keys) and not multivalued_keys:
                            break
                    if target_key and target_key not in section_container:
                        continue
                    file_container.append(section_container)
                else:
                    continue
        result_container.extend(file_container)
    return result_container


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
