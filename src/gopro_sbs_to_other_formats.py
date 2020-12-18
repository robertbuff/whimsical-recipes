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


# This script searches for all videos in a given folder with a naming
# pattern that matches "ANYTHING (SbS).EXTENSION", where we interpret
# SbS to mean side-b-side. Each video will then be converted into two
# additional stereoscopic formats, red-cyan anaglyph and a cropped
# left/right version for stereoscopes (inexpensive viewers into which
# one generally slides a cellphone player.) The stereoscope will have
# a black center gap to help separate the two images. Its width is
# configurable.
#
# The folder and width of the stereoscopic center gap are either taken
# from the command line, or from a config file ~/whimsical_recipes,
# section [GoPro Dual Hero3]. See below in the function __settings() for
# details.
#
# The red/cyan anaglyph is generated with explicit pixel format yuv420p.
# The filter stereo3d produces yuv444p, which couldn't be viewed in
# QuickTime on my MacBook Pro.


import os
import re
import subprocess
import argparse

from gopro_functions import ask_go, environment


def main() -> None:
    """Find all side-by-side rendered movies and convert them to anaglyph and stereoscopic formats"""
    common, folder, stereoscope_center_gap = __settings()
    sources = __sources(folder)
    replace_default = None
    for source, parts in sources.items():
        for tag, action in [('Anaglyph', __go_anaglyph), ('Stereoscope', __go_stereoscope)]:
            target = '{}{}({}){}'.format(folder, parts[0], tag, parts[1])
            print('Propose {} -> {}'.format(source, target))
            go, replace_default = ask_go(target, replace_default)
            if go:
                if action(common['ffmpeg'], source, target, stereoscope_center_gap) != 0:
                    print('Error -- aborting')
                    break
            else:
                print('Skipping.')
            print('')


def __settings() -> tuple:
    """Find out which folder to look for input files in"""
    arg_parser = argparse.ArgumentParser(
        description='Convert side-by-side stereo file to anaglyph and stereoscopic formats'
    )
    arg_parser.add_argument('folder', help='folder with input files', nargs='?')
    arg_parser.add_argument(
        '--stereoscope_center_gap',
        type=int,
        help='gap in pixels between left and right sides'
    )
    args, config, common = environment(arg_parser)
    if args.folder is None:
        root = config.get('SideBySideSourceRoot', '')
        folder = '{}/{}'.format(root, input('Side-by-side input folder: {}/'.format(root)))
    else:
        folder = args.folder
    folder = '{}/'.format(folder) if not folder.endswith('/') else folder
    if args.stereoscope_center_gap is None:
        stereoscope_center_gap = int(config.get('StereoscopeCenterGap', 0))
    else:
        stereoscope_center_gap = args.stereoscope_center_gap
    stereoscope_center_gap = stereoscope_center_gap // 8 * 8
    print('Folder = {}\nStereoscopeCenterGap = {}'.format(folder, stereoscope_center_gap))
    return common, folder, stereoscope_center_gap


def __sources(
        folder: str
) -> dict:
    """Derive names of target movies from names of input side-by-side files with expected naming scheme"""
    files = sorted(os.listdir(folder))
    sources = dict()
    for file in files:
        # Expected naming scheme of rendered side-by-side movies: <anything>(sBs).<extension>
        m = re.match(r'^([^\(]+)\(SbS\)(\.\w+)$', file)
        if m:
            prefix, suffix = m.group(1), m.group(2)
            sources['{}{}'.format(folder, file)] = (prefix, suffix)
    return sources


def __go_anaglyph(
        ffmpeg: str,
        source: str,
        target: str,
        *_
) -> int:
    """Use ffmpeg to convert the source file to red/cyan anaglyph format"""
    print('Converting.')
    steps = [
        '-y',
        '-hide_banner -loglevel warning',
        '-i "{}"'.format(source),
        '-filter_complex',
        '"[0:v]stereo3d=sbs2l:arcg,scale=w=2*iw:h=ih,setsar=1[v]"',
        '-map "[v]" -map "0:a"',
        '-pix_fmt yuv420p'
    ]
    command = '{} {} "{}"'.format(ffmpeg, ' '.join(steps), target)
    print(command)
    return subprocess.call(command, shell=True)


def __go_stereoscope(
        ffmpeg: str,
        source: str,
        target: str,
        stereoscope_center_gap: int
) -> int:
    """Use ffmpeg to convert the source file to stereoscope format"""
    print('Converting.')
    quarter_gap = stereoscope_center_gap // 8
    steps = [
        '-y',
        '-hide_banner -loglevel warning',
        '-i "{}"'.format(source),
        '-filter_complex',
        '"[0:v]crop=iw/4:ih:iw/8+{}:0,fillborders=right={}:mode=fixed,scale=w=2*iw:h=ih,setsar=1[left];'.format(
            quarter_gap,
            quarter_gap * 2
        ),
        '[0:v]crop=iw/4:ih:5*iw/8-{}:0,fillborders=left={}:mode=fixed,scale=w=2*iw:h=ih,setsar=1[right];'.format(
            quarter_gap,
            quarter_gap * 2
        ),
        '[left][right]hstack[v]"',
        '-map "[v]" -map "0:a"'
    ]
    command = '{} {} "{}"'.format(ffmpeg, ' '.join(steps), target)
    print(command)
    return subprocess.call(command, shell=True)


main()
