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

import random
import itertools


def main(
) -> None:
    colors = ["Red", "Green", "Blue", "Yellow", "White", "Black"]
    random.shuffle(colors)
    possible_permutations = list(itertools.permutations(colors, 4))
    random.shuffle(possible_permutations)
    evidence = []
    location_and_color_matches = None
    for permutation in possible_permutations:
        is_candidate = all(map(
            lambda e:
                e[1] == sum(x == y for x, y in zip(e[0], permutation)) and
                e[2] == sum(x in permutation for x in e[0]),
            evidence
        ))
        if is_candidate:
            print(permutation)
            location_and_color_matches = int(
                input("How many exact matches in color and location? ")
            )
            color_but_not_location_matches = int(
                input("How many matches in color only, but not location? ")
            )
            evidence.append([
                permutation,
                location_and_color_matches,
                location_and_color_matches + color_but_not_location_matches
            ])
    if location_and_color_matches != 4:
        print("Hey, you cheated with your evaluations!")


main()