"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file implements a reader for Freelancer's "BINI" (binary INI)
format. Thanks to Bas Westerbaan for providing excellent
documentation available here: <http://blog.w-nz.com/uploads/bini.pdf>.
"""
from typing import Dict, List
from collections import defaultdict
from struct import unpack
from os.path import getsize, isfile

VALUE_TYPES = {1: 'i', 2: 'f', 3: 'i'}  # maps a byte value type to a struct format string


def parse_file(path: str, fold_values=True, lower=True):
    """Read the BINI file at `path` and produce an output of the form
    {section_name -> [{entry_name -> entry_values}]}"""
    result = []
    string_table = {}
    file_size = getsize(path)

    with open(path, 'rb') as f:
        # read file header
        magic, version, str_table_offset = unpack('4sII', f.read(12))
        assert magic == b'BINI', version == 1

        # read string table, which stretches from str_table_offset to EOF
        f.seek(str_table_offset)
        raw_table = f.read(file_size - str_table_offset - 1)

        count = 0
        for s in raw_table.split(b'\0'):
            string_table[count] = s.decode('cp1252').lower()
            count += len(s) + 1

        # return to end of header to read sections
        f.seek(12)

        while f.tell() < str_table_offset:
            # read section header
            section_name_ptr, entry_count = unpack('hh', f.read(4))
            section_name = string_table[section_name_ptr]

            section_entries = []
            for e in range(entry_count):
                # read entry
                entry_name_ptr, value_count = unpack('hb', f.read(3))
                entry_name = string_table[entry_name_ptr]
                entry_values = []

                for v in range(value_count):
                    # read value
                    value_type, = unpack('b', f.read(1))
                    value_data, = unpack(VALUE_TYPES[value_type], f.read(4))

                    if value_type == 3:
                        # it is a pointer relative to the string table
                        value_data = string_table[value_data]

                    entry_values.append(value_data)

                if value_count > 1:
                    entry_value = tuple(entry_values)
                elif value_count == 1:
                    entry_value = entry_values[0]
                else:
                    continue

                section_entries.append((entry_name, entry_value))
            result.append((section_name, section_entries))

    return tuple(result)


def dump(path: str) -> str:
    """Dump the BINI file at `path` to an INI-formatted string."""
    bini = parse_file(path, fold_values=False)

    lines = []
    for section_name, sections in bini:
        for entry in sections:
            lines.append(f'[{section_name}]')
            # convert the entries in this section to strings and add to output
            for key, values in entry:
                # form key value pairs for each entry value. Expand tuples to remove quotes and brackets
                entries = [f'{key} = {", ".join(map(str, v)) if isinstance(v, tuple) else v}' for v in values]
                lines.extend(entries)
            lines.append('')  # add a blank line after each section
    return '\n'.join(lines)


def is_bini(path: str) -> bool:
    """Returns whether the (.ini) file at `path` is a BINI by checking its magic number."""
    with open(path, 'rb') as f:
        data = f.read(4)
    return data[:4] == b'BINI'
