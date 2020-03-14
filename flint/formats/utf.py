"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file provides a read-only implementation of Universal Tree Format
(UTF), a hierarchical binary format developed by Digital Anvil. In
Freelancer it is used to store binary assets, like textures and icons.

Reference: <https://wiki.librelancer.net/utf:universal_tree_format>
"""
import deconstruct as c
from . import WinStruct


def parse(path):
    result = {}
    with open(path, 'rb') as f:
        header = UtfHeader(f.read(56))

        entry_count = header.TreeSize // header.EntrySize

        # read name dictionary
        f.seek(header.NamesOffset)
        dictionary = f.read(header.NamesUsedSize).split(b'\0')
        position = 0

        names = {}
        for name in dictionary:
            names[position] = name.decode('ascii')
            position += len(name) + 1

        # read data tree
        f.seek(header.TreeOffset)
        for e in range(entry_count):
            entry = UtfEntry(f.read(44))
            position = f.tell()
            name = names[entry.DictionaryNameOffset]
            f.seek(entry.ChildOrDataOffset + header.DataStartOffset)
            yield name, f.read(entry.UsedDataSize)
            f.seek(position)
        return result


def extract(path, target_directory):
    for dir_name, dir_data in parse(path):
        if dir_name == target_directory:
            return dir_data
    raise KeyError


def dump(path):
    return dict(parse(path))


TYPE_CHILD = 0x80  # utf tree types
TYPE_DATA = 0x10


class UtfHeader(WinStruct):
    Signature: c.uint32
    Version: c.uint32
    TreeOffset: c.uint32
    TreeSize: c.uint32
    _0: c.uint32
    EntrySize: c.uint32
    NamesOffset: c.uint32
    NamesAllocatedSize: c.uint32
    NamesUsedSize: c.uint32
    DataStartOffset: c.uint32
    _1: c.uint32
    _2: c.uint32
    FiletimeLow: c.uint32
    FiletimeHigh: c.uint32


class UtfEntry(WinStruct):
    NextSiblingOffset: c.uint32
    DictionaryNameOffset: c.uint32
    EntryType: c.uint32
    SharingAttributes: c.uint32
    ChildOrDataOffset: c.uint32
    AllocatedDataSize: c.uint32
    UsedDataSize: c.uint32
    UncompressedDataSize: c.uint32
    CreationTime: c.uint32
    LastAccessTime: c.uint32
    LastWriteTime: c.uint32
