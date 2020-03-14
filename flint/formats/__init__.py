"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This directory contains functions to read the file formats used by
Freelancer.
"""
import deconstruct as c


class WinStruct(c.Struct):
    __byte_order__ = c.ByteOrder.LITTLE_ENDIAN  # all formats native to Windows are little-endian
