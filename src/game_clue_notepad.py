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
import enum
import itertools
from collections import OrderedDict


class Character(enum.IntEnum):
    MissScarlet = 0
    Scarlet = 0  # alias
    Red = 0  # alias
    #
    MrGreen = 1
    Green = 1  # alias
    #
    ColonelMustard = 2
    Mustard = 2  # alias
    Yellow = 2  # alias
    #
    ProfessorPlum = 3
    ProfPlum = 3  # alias
    Plum = 3  # alias
    Purple = 3  # alias
    #
    MrsPeacock = 4
    Peacock = 4  # alias
    Blue = 4  # alias
    #
    MrsWhite = 5
    White = 5  # alias


class Weapon(enum.IntEnum):
    CandleStick = 0
    Knife = 1
    Dagger = 1  # alias
    LeadPipe = 2
    Pipe = 2  # alias
    Revolver = 3
    Rope = 4
    Wrench = 5


class Room(enum.IntEnum):
    Kitchen = 0
    Ballroom = 1
    Conservatory = 2
    DiningRoom = 3
    BillardRoom = 4
    Library = 5
    Lounge = 6
    Hall = 7
    Study = 8


def main() -> None:
    """Provide a whiteboard to track suspicions brought forward during a game of Clue(do)"""
    possibilities = __possibilities()
    players = __players()
    print(players)


def __possibilities() -> list:
    """Generate list of possibilities in random order, so every game is different"""
    possibilities = list(itertools.product(list(Character), list(Weapon), list(Room)))
    random.shuffle(possibilities)
    return possibilities


def __players() -> OrderedDict:
    """Ask user for list of players and the number of cards each has"""
    print('Enter each player nick name and number of cards.')
    print('Re-enter a name to update the number of cards.')
    print('Enter number of cards as 0 to remove a player.')
    print('Finish with an empty line.')
    player_parts = []
    prompt = ''
    while True:
        players = __players1(player_parts, prompt)
        prompt('Hit enter again or type in another player and number of cards: ')


def __players1(
        player_parts: list,
        prompt: str
) -> OrderedDict:
    """Ask user for list of players and the number of cards each has"""
    players = OrderedDict()
    while True:
        text = input(prompt).strip()
        if not text:
            break
        parts = text.split(' ')
        if len(parts) < 2:
            print('*** Must be nick name AND number of cards ***')
            continue
        if len(parts) > 2:
            print('*** Too many spaces -- nick name cannot have a space ***')
            continue
        if not parts[1].isdigit():
            print('*** Second parameter must be a number ***')
            continue
        number_of_cards = int(parts[1])
        key = parts[0].lower()
        if number_of_cards == 0:
            print('Removing player {} should they exist'.format(parts[0]))
            player_parts = [pp for pp in player_parts if pp[0] != key]
        else:
            if key in (pp[0] for pp in player_parts):
                print('Player {} already exists; updating number of cards'.format(parts[0]))
            # OrderedDict constructor will take care of the update
            player_parts.append((key, dict(name=parts[0], number_of_cards=number_of_cards)))
        players = OrderedDict(player_parts)
        prompt = 'Enter player {} nick name and number of cards: '.format(len(players) + 1)
    return players


main()
