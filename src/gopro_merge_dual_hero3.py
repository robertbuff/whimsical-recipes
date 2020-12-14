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

# This script searches for all matching left/right video patterns in a given
# folder and uses ffmpeg to merge them into side-by-side clips, possible with
# an adjustment for a predefined vertical displacement (my pair requires an
# adjustment of 16 pixels.)
#
# The folder and vertical error are either taken from the command line, or
# from a config file ~/whimsical_recipes, section [GoPro Dual Hero3]. See
# below in the function __settings() for details.
#
# For GoPro Hero3+'s, the input resolution is HD, and the output resolution
# will be 4k, for full preservation of input resolution (4k is twice HD.)
# Vertically we will up-sample two times.


import os
import re
import sys
import subprocess
import argparse
import configparser


def main() -> None:
    """Find all left/right video pairs in interactive folder and merge to side-by-side"""
    folder, vertical_error = __settings()
    targets = __targets(folder)
    replace_default = None
    for target, sides in targets.items():
        print('Pair for {}:\n    L={}\n    R={}'.format(target, sides['L'], sides['R']))
        go, replace_default = __ask_go(target, replace_default)
        if go:
            if __go(folder, sides, target, vertical_error) != 0:
                print('Error -- aborting')
                break
        else:
            print('Skipping.')
        print('')


def __settings() -> tuple:
    """Find out which folder to look for input files in"""
    arg_parser = argparse.ArgumentParser(description='Merge left/right mp4 video pairs')
    arg_parser.add_argument('folder', help='folder with input files', nargs='?')
    arg_parser.add_argument(
        '--vertical_error',
        type=int,
        help='vertical displacement in pixels (positive: right video is too low)'
    )
    args = arg_parser.parse_args(sys.argv[1:])
    config = configparser.ConfigParser()
    config.read(os.path.expanduser('~/.whimsical_recipes'))
    s = config['GoPro Dual Hero3'] if 'GoPro Dual Hero3' in config else dict()
    if args.folder is None:
        root = s.get('InputRoot', '')
        folder = '{}/{}'.format(root, input('Clip folder: {}/'.format(root)))
    else:
        folder = args.folder
    if args.vertical_error is None:
        vertical_error = int(s.get('VerticalError', 0))
    else:
        vertical_error = args.vertical_error
    vertical_error = vertical_error // 2 * 2
    print('Folder = {}\nVerticalError = {}'.format(folder, vertical_error))
    return folder, vertical_error


def __targets(
        folder: str
) -> dict:
    """Derive names of target files from names of input files with expected naming scheme"""
    files = sorted(os.listdir(folder))
    targets = dict()
    for file in files:
        # Expected naming scheme of input files: <alphanum or whitespace>[L|R]<num or whitespace>.mp4
        m = re.match('([a-zA-Z0-9 ]+)([LR])([0-9 ]+\\.mp4)', file)
        if m:
            prefix, side, suffix = m.group(1), m.group(2), m.group(3)
            target = '{}{}'.format(prefix.strip(), suffix)
            if target not in targets:
                targets[target] = dict()
            targets[target][side] = file
    targets = {'{}/{}'.format(folder, target): sides for target, sides in targets.items() if len(sides) == 2}
    return targets


def __ask_go(
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


def __go(
        folder: str,
        sides: dict,
        target: str,
        vertical_error: int
) -> int:
    """Use ffmpeg to merge the two sides to target file in folder"""
    print('Merging.')
    ve_left, ve_right, shift_back = __vertical_error_filters(vertical_error)
    steps = [
        '-y',
        '-i "{}/{}"'.format(folder, sides['L']),
        '-i "{}/{}"'.format(folder, sides['R']),
        '-filter_complex',
        '"[0:v]{}scale=w=iw:h=2*(ih+{}),setsar=1[left];'.format(ve_left, shift_back),
        '[1:v]{}scale=w=iw:h=2*(ih+{}),setsar=1[right];'.format(ve_right, shift_back),
        '[left][right]hstack[v];',
        '[0:a][1:a]amerge=inputs=2,pan=stereo|c0<c0+c1|c1<c2+c3[a]"',
        '-map "[v]" -map "[a]"'
    ]
    command = 'ffmpeg {} "{}"'.format(' '.join(steps), target)
    print(command)
    return subprocess.call(command, shell=True)


def __vertical_error_filters(
        vertical_error: int
) -> tuple:
    """Make filters that correct for a vertical error between the cameras"""
    if vertical_error > 0:
        # Right video is too low
        ve_left = 'crop=iw:ih-{}:0:{},'.format(vertical_error, vertical_error)
        ve_right = 'crop=iw:ih-{}:0:0,'.format(vertical_error)
        return ve_left, ve_right, vertical_error
    if vertical_error < 0:
        # Left image is too low
        ve_left = 'crop=iw:ih-{}:0:0,'.format(-vertical_error)
        ve_right = 'crop=iw:ih-{}:0:{},'.format(-vertical_error, -vertical_error)
        return ve_left, ve_right, -vertical_error
    return '', '', abs(vertical_error)

main()
