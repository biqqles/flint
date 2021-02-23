"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file implements a platform-independent resource DLL reader, as
well as the logic that Freelancer uses to map those resources to
internal IDs. Additionally it implements conversion from RDL (used
for rich-text strings) to HTML.
"""
from typing import Dict
from os import SEEK_CUR

import deconstruct as c

from ..interface import rdl_to_html, rdl_to_plaintext
from .. import cached
from .. import paths
from . import WinStruct


resource_table: Dict[int, Dict[int, str]] = {}


@cached
def lookup(resource_id: int) -> str:
    """Looks up the text associated with a resource ID (string or HTML) in the resource dlls."""
    if resource_id is None:  # sometimes objects which should have infocards don't. Freelancer doesn't seem to care
        return ''

    # all references to string/html resources in the inis (strid or ids_info) use "external ids" which are based off the
    # positions of the dlls in Freelancer.ini/[Resources]
    dll_no = resource_id // 65536  # get the dll index the id refers to
    external_id_offset = dll_no * 65536  # the external id of position 0 in the dll

    if dll_no not in paths.dlls:  # likewise
        return ''

    # if dll has already been loaded
    if dll_no in resource_table:
        return resource_table[dll_no].get(resource_id, '')  # a resource id that maps to nothing is also an empty string

    # otherwise, load in the new dll, and call again
    dll_path = paths.dlls[dll_no]
    resource_table[dll_no] = parse(dll_path, external_id_offset)
    return lookup(resource_id)


@cached
def lookup_as_html(resource_id: int) -> str:
    """Looks up the given resource ID and translates RDL to HTML."""
    return rdl_to_html(lookup(resource_id))


@cached
def lookup_as_plain(resource_id: int) -> str:
    """Looks up the given resource ID and strips out all RDL tags. Paragraph tags are replaced with newlines."""
    return rdl_to_plaintext(lookup(resource_id))


def parse(path: str, external_strid_offset: int = 0) -> Dict[int, str]:
    """Read the DLL at the given path into a mapping of external ids to string/XML resources.
    Format reference: <https://docs.microsoft.com/en-gb/windows/win32/debug/pe-format>"""

    def read_rdt(entry_count: int):
        """Read the entries in a resource directory table starting at the file cursor."""
        rdt_entries = {}
        for e in range(entry_count):
            entry = ResourceDirectoryEntry(f.read(8))
            rdt_entries[entry.IntegerID] = entry.Offset & 0x7FFFFFFF  # only interested in lower 31 bits
        return rdt_entries

    def read_string_table():
        """Read a string table starting at the file cursor."""
        string_table = {}
        for s in range(16):  # sixteen strings are allocated per table
            resource_string = ResourceDirectoryString(f.read(2))
            if resource_string.Length:
                strid = (name - 1) * 16 + s + external_strid_offset
                text = f.read(resource_string.Length * 2).decode('utf-16')
                string_table[strid] = text
        return string_table

    with open(path, 'rb') as f:
        # read PE signature
        f.seek(0x3C)  # find offset to signature
        pe_signature_offset = ord(f.read(1))
        f.seek(pe_signature_offset)
        assert f.read(4) == b'PE\0\0'

        # read COFF header, which begins immediately after PE signature
        coff = CoffHeader(f.read(20))
        # skip the optional header (is irrelevant to us) to get to the section headers
        f.seek(coff.SizeOfOptionalHeader, SEEK_CUR)

        # go through section headers to find .rsrc
        for i in range(coff.NumberOfSections):
            section = SectionHeader(f.read(40))
            if section.Name.rstrip(b'\0') == b'.rsrc':
                rsrc_offset = section.PointerToRawData
                break
        else:
            raise EOFError('.rsrc section not found')

        # read Resource Directory Table header for .rsrc section
        f.seek(rsrc_offset)
        resource_directory_table = ResourceDirectoryTable(f.read(16))

        # remember that named entries precede ids

        # read type directory entries. For types, only ids are used, not string names
        resource_types = read_rdt(resource_directory_table.IdEntryCount)  # resource types to offsets

        # for each resource type, read its name table
        name_offsets = {}
        for resource_type, name_table_offset in resource_types.items():  # for each data type
            f.seek(name_table_offset + rsrc_offset)
            name_entries = ResourceDirectoryTable(f.read(16))
            name_offsets[resource_type] = read_rdt(name_entries.IdEntryCount)

        resources = {}

        for resource_type, name_offset in name_offsets.items():
            for name, description_offset in name_offset.items():
                f.seek(description_offset + rsrc_offset)
                # commence reading another section header - I actually have no idea why this is here but it matches
                data_section = SectionHeader(f.read(40))
                f.seek(rsrc_offset + data_section.PointerToRawData)  # jump there

                # read Resource Data Entry
                data = ResourceDataEntry(f.read(16))  # could also get codepage int here ?
                f.seek(data.DataRVA)

                if resource_type == RT_STRING:
                    resources.update(read_string_table())
                elif resource_type == RT_HTML:
                    strid = name + external_strid_offset
                    text = f.read(data.Size).decode('utf-16')
                    resources[strid] = text
                elif resource_type == RT_VERSION:
                    pass
                else:
                    raise NotImplementedError('Unexpected resource type:', hex(resource_type))
        return resources


# win32 resource types <https://docs.microsoft.com/en-us/windows/win32/menurc/resource-types>
RT_HTML = 0x17  # html resource type (in Freelancer, used for XML-encoded rich text)
RT_STRING = 0x06  # string table entry resource type
RT_VERSION = 0x10  # version information - ignored


# PE format structs
class CoffHeader(WinStruct):
    Machine: c.int16
    NumberOfSections: c.int16
    TimeDateStamp: c.int32
    PointerToSymbolTable: c.int32
    NumberOfSymbols: c.int32
    SizeOfOptionalHeader: c.int16
    Characteristics: c.int16


class SectionHeader(WinStruct):
    Name: c.char[8]
    VirtualSize: c.int32
    VirtualAddress: c.int32
    SizeOfRawData: c.int32
    PointerToRawData: c.int32
    PointerToRelocations: c.int32
    PointerToLinenumbers: c.int32
    NumberOfRelocations: c.int16
    NumberOfLinenumbers: c.int16
    Characteristics: c.int32


class ResourceDirectoryTable(WinStruct):
    Characteristics: c.int32
    TimeDateStamp: c.int32
    MajorVersion: c.int16
    MinorVersion: c.int16
    NameEntryCount: c.int16
    IdEntryCount: c.int16


class ResourceDirectoryEntry(WinStruct):
    IntegerID: c.int32
    Offset: c.int32  # if MSB is 0, this is the address of a leaf RDE. If 1, lower bits are the RDT one level down


class ResourceDataEntry(WinStruct):
    DataRVA: c.int32
    Size: c.int32
    Codepage: c.int32
    Reserved: c.int32


class ResourceDirectoryString(WinStruct):
    Length: c.int16
