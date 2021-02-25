"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This module provides utilities for working with Freelancer's paths.
"""
from typing import Dict, Tuple, Optional
import os

from .formats import ini
from . import cached

install: Optional[str] = None
inis: Dict[str, Tuple[str]] = {}  # ini category (defined in freelancer.ini) to a list of paths
dlls: Dict[int, str] = {}  # dll number to path


def set_install_path(new_path, discovery=False):
    """Set the path to the installation"""
    global install
    if not os.path.exists(new_path):
        raise FileNotFoundError(new_path)
    assert is_probably_freelancer(new_path, discovery)
    install = new_path
    generate_index()


def install_path_set() -> bool:
    """Whether an install path has been set (see `set_install_path`)."""
    return install is not None


@cached
def fix_path_case(path: str) -> str:
    """Thanks to the nature of Windows' file systems, Freelancer frequently uses apparently arbitrary casing for many
    paths. This function takes an absolute path and returns it with the casing as it really is on the filesystem.

    This function mixes iteration/recursion to make the use of dynamic programming more effective. If one recursive
    function with an additional tail accumulator was used, it would prevent the cache from being effective at storing
    precomputed known-correct paths."""

    @cached
    def correct_subpath(path_: str) -> str:
        """Recursively reduce a path from its end until it diverges from the filesystem's structure. Then, find the
        correct case for that divergent level and return the subpath."""
        head, tail = os.path.split(path_)
        if os.path.exists(head):  # go back till divergence
            #  tail is now divergent level; find its correct case (taking the first match)
            correct_case = next(filter(lambda s: s.casefold() == tail.casefold(), os.listdir(head)), None)
            if correct_case is None:  # if no match possible
                raise FileNotFoundError
            return os.path.join(head, correct_case)
        return correct_subpath(head)

    path = path.rstrip(r'\/')  # remove trailing slashes which mess up path.split
    if os.name == 'nt':
        return path  # on Windows path.exists ignores case, so no point in continuing

    result = correct_subpath(path)
    while len(result) != len(path):
        result = correct_subpath(result + path[len(result):])
    return result


def is_probably_freelancer(path, discovery=False):
    """Verifies that the given directory is (probably) an actual Freelancer installation, by checking that identifying
    files and directories are present."""
    identifiers = {'DATA', 'DLLS', 'EXE'}
    if discovery:
        identifiers |= {'DSLauncher.exe'}
    return os.path.isdir(path) and identifiers.issubset(os.listdir(path))


def construct_path(*subpath):
    """Form an absolute path to a file in the install directory based on a subpath relative to its root."""
    candidate = os.path.join(install, *subpath).replace('\\', '/')
    try:
        return fix_path_case(candidate)
    except FileNotFoundError:  # todo: hacky, should not handle invalid path silently
        return candidate


def generate_index():
    """Use freelancer.ini to build an index of inis and dlls."""
    freelancer_ini = os.path.join(install, 'EXE/freelancer.ini')
    parsed = ini.sections(freelancer_ini, fold_values=False)

    resources = ['resources.dll', *parsed['resources'][0]['dll']]  # resources.dll is hardcoded as DLL 0

    data = parsed['data'][0]
    root = parsed['freelancer'][0]  # todo: also look at 'data path'
    data.update(root)

    dlls.update({i: construct_path('EXE', f) for i, f in enumerate(resources)})
    inis.update({category: tuple(construct_path('DATA', f) for f in files) for category, files in data.items()})
