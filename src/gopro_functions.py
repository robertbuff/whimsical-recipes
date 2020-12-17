# MIT License
#
# Copyright (c) 2020 Robert Buff
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# This script contains helper functions for the conversion of GoPro Hero3+
# stereo footage.

import os
import sys
import argparse
import configparser


def environment(
        arg_parser: argparse.ArgumentParser
) -> tuple:
    """Return args, config section, and common properties such as name of ffmpeg executable"""
    arg_parser.add_argument('--ffmpeg', help='path to ffmpeg executable')
    args = arg_parser.parse_args(sys.argv[1:])
    config_parser = configparser.ConfigParser()
    config_parser.read(os.path.expanduser('~/.whimsical_recipes'))
    config = config_parser['GoPro Dual Hero3'] if 'GoPro Dual Hero3' in config_parser else dict()
    ffmpeg = config.get('Ffmpeg', 'ffmpeg') if args.ffmpeg is None else args.ffmpeg
    return args, config, dict(ffmpeg=ffmpeg)


def ask_go(
        target: str,
        replace_default: str
) -> tuple:
    """Ask user whether to override existing target file"""
    if os.path.exists(target):
        if replace_default is None:
            replace = None
            while replace not in ('y', 'Y', 'n', 'N'):
                replace = input('Replace [y|Y|n|N] ? ')
                if replace == 'y':
                    go = True
                if replace == 'Y':
                    go = True
                    replace_default = True
                if replace == 'n':
                    go = False
                if replace == 'N':
                    go = False
                    replace_default = False
        else:
            go = replace_default
    else:
        go = True
    return go, replace_default
