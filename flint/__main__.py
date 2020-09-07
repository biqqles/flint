"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file provides an interactive prompt for working with flint
(and therefore a Freelancer installation). Run with `python -i`,
e.g. `python -i interactive.py "<freelancer_dir>"`.

If running in PyCharm, ensure "Emulate terminal in output console"
is enabled in the run/debug configuration.
"""
import argparse
import os
import subprocess
import sys
import warnings

# if not running in interactive mode, make it so
# this trick allows the very handy "python -m flint.interactive" to bring up the interactive shell mode
if not sys.flags.interactive:
    subprocess.call([sys.executable, '-i', *sys.argv])
    exit(0)

# make flint available for import
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))

# override interpreter prompts
sys.ps1 = '(flint as fl) >>> '
sys.ps2 = '              ... '

# parse command line arguments
parser = argparse.ArgumentParser(description='flint, a parser for Freelancer and its formats')
parser.add_argument('freelancer_dir', help='Path to a working Freelancer install directory')
parser.add_argument('-d', '--discovery', help='Whether Freelancer dir is Discovery modded.', action='store_true')
parser.add_argument('-s', '--silent', help='Silence all warnings', action='store_true')
try:
    arguments = parser.parse_args()
except SystemExit:
    os._exit(1)

# configure warnings
warnings.simplefilter('ignore' if arguments.silent else 'always')

import flint as fl
fl.paths.set_install_path(arguments.freelancer_dir, arguments.discovery)
