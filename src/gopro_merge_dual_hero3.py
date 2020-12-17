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
# adjustment of 16 pixels.) We also support lens correction if ffmpeg has
# the lensfun filter installed (by default, the brew formula for ffmpeg
# does not.)
#
# The folder and vertical error are either taken from the command line, or
# from a config file ~/whimsical_recipes, section [GoPro Dual Hero3]. See
# below in the function __settings() for details.
#
# Lens correction instructions are also taken from the command line, or
# the config file. This is a list, for each instruction we produce one
# output file with the appropriate base name suffix. Choices for lens
# correction are: unadjusted, rectilinear. The lens is hardwired to be
# the GoPro Hero3+ model.
#
# For GoPro Hero3+'s, the input resolution is HD, and the output resolution
# will be 4k, for full preservation of input resolution (4k is twice HD.)
# Vertically we will up-sample two times.
#
# If your ffmpeg doesn't have lensfun by default, download and build it from
# source. The following configuration works on MacOS:
#
# ./configure --prefix=YOUR_INSTALL_PATH --enable-shared --enable-pthreads
# --enable-version3 --enable-avresample --cc=clang --host-cflags=
# --host-ldflags= --enable-ffplay --enable-gnutls --enable-gpl --enable-libaom
# --enable-libbluray --enable-libdav1d --enable-libmp3lame --enable-libopus
# --enable-librav1e --enable-librubberband --enable-libsnappy --enable-libtesseract
# --enable-libtheora --enable-libvidstab --enable-libvorbis --enable-libvpx
# --enable-libwebp --enable-libx264 --enable-libx265 --enable-libxml2 --enable-libxvid
# --enable-lzma --enable-libfontconfig --enable-libfreetype --enable-frei0r
# --enable-libass --enable-libopencore-amrnb --enable-libopencore-amrwb
# --enable-libopenjpeg --enable-libspeex --enable-libsoxr --enable-videotoolbox
# --disable-libjack --disable-indev=jack --enable-liblensfun


import os
import re
import subprocess
import argparse

from gopro_functions import ask_go, environment


RECTILINEAR = 'rectilinear'
UNADJUSTED = 'unadjusted'

LENS_CORRECTION_SUFFIXES = {
    RECTILINEAR: ' (SbSr)',
    UNADJUSTED: ' (SbS)'
}


def main() -> None:
    """Find all left/right video pairs in interactive folder and merge to side-by-side"""
    common, folder, vertical_error, lens_corrections = __settings()
    targets = __targets(folder, lens_corrections)
    replace_default = None
    for target, props in targets.items():
        sides = dict(L=props['L'], R=props['R'])
        print('Pair for {}:\n    L={}\n    R={}'.format(target, sides['L'], sides['R']))
        go, replace_default = ask_go(target, replace_default)
        if go:
            if __go(common['ffmpeg'], folder, sides, target, vertical_error, props['lens_correction']) != 0:
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
    arg_parser.add_argument(
        '--lens_corrections',
        help='list of lens corrections to apply (out of rectilinear, unadjusted)'
    )
    args, config, common = environment(arg_parser)
    if args.folder is None:
        root = config.get('LeftRightSourceRoot', '')
        folder = '{}/{}'.format(root, input('Left/right source folder: {}/'.format(root)))
    else:
        folder = args.folder
    if args.vertical_error is None:
        vertical_error = int(config.get('VerticalError', 0))
    else:
        vertical_error = args.vertical_error
    if args.lens_corrections is None:
        lens_corrections = config.get('LensCorrections', UNADJUSTED)
    else:
        lens_corrections = args.lens_corrections
    vertical_error = vertical_error // 2 * 2
    lens_corrections = [lc.strip() for lc in lens_corrections.split(',')]
    print('Folder = {}\nVerticalError = {}\nLens Corrections = {}'.format(
        folder,
        vertical_error,
        ', '.join(lens_corrections)
    ))
    return common, folder, vertical_error, lens_corrections


def __targets(
        folder: str,
        lens_corrections: list
) -> dict:
    """Derive names of target files from names of input files with expected naming scheme"""
    files = sorted(os.listdir(folder))
    targets = dict()
    for file in files:
        # Expected naming scheme of input files: <alphanum or whitespace>[L|R]<num or whitespace>.mp4
        m = re.match('([a-zA-Z0-9 ]+)([LR])([0-9 ]+)(\\.mp4)', file)
        if m:
            prefix, side, suffix, extension = m.group(1), m.group(2), m.group(3), m.group(4)
            for lens_correction in lens_corrections:
                target = '{}{}{}{}'.format(
                    prefix.strip(),
                    suffix,
                    LENS_CORRECTION_SUFFIXES[lens_correction],
                    extension
                )
                if target not in targets:
                    targets[target] = dict(lens_correction=lens_correction)
                targets[target][side] = file
    targets = {'{}/{}'.format(folder, target): props for target, props in targets.items() if len(props) == 3}
    return targets


def __go(
        ffmpeg: str,
        folder: str,
        sides: dict,
        target: str,
        vertical_error: int,
        lens_correction: str
) -> int:
    """Use ffmpeg to merge the two sides to target file in folder, possibly after a lens correction"""
    print('Merging.')
    lc_filter = __lens_correction_filter(lens_correction)
    if lc_filter:
        lc_filter = lc_filter + ','
    ve_left, ve_right, shift_back = __vertical_error_filters(vertical_error)
    steps = [
        '-y',
        '-hide_banner -loglevel warning',
        '-i "{}/{}"'.format(folder, sides['L']),
        '-i "{}/{}"'.format(folder, sides['R']),
        '-filter_complex',
        '"[0:v]{}{}scale=w=iw:h=2*(ih+{}),setsar=1[left];'.format(lc_filter, ve_left, shift_back),
        '[1:v]{}{}scale=w=iw:h=2*(ih+{}),setsar=1[right];'.format(lc_filter, ve_right, shift_back),
        '[left][right]hstack[v];',
        '[0:a][1:a]amerge=inputs=2,pan=stereo|c0<c0+c1|c1<c2+c3[a]"',
        '-map "[v]" -map "[a]"',
        '-pix_fmt yuv420p'
    ]
    command = '{} {} "{}"'.format(ffmpeg, ' '.join(steps), target)
    print(command)
    return subprocess.call(command, shell=True)


def __lens_correction_filter(
        lens_correction: str
) -> str:
    """Make a filter that uses lensfun to correct for lens distortion"""
    if lens_correction == UNADJUSTED:
        return ''
    if lens_correction == RECTILINEAR:
        return 'lensfun=make=GoPro:model=HERO3+ Black:lens_model=fixed lens'
    raise RuntimeError('Unknown lens correction {}'.format(lens_correction))


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
