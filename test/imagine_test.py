# Copyright (c) 2021 Robert Buff
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
# to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions
# of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


# Defines a decorator "imagine" that enables the user to temporarily set overrides on a function or
# method. We treat the function or override as a mapping, and redefine the mapping for certain points
# in the parameter space. The replacement lives for the duration of a "with" context. Each decorated
# function or method maintains its own global stack of "scenes" of overrides. The overrides bleed into
# other code and are not contained in the local scope, so this mechanism can be used to temporarily
# inject alternative values into calculations and recompute. This paradigm requires deep knowledge of
# the global namespace of functions and class methods. It's not advisable to use it for large software
# systems. I'd view it as an intellectual exercise only.

import unittest

from src.imagine import imagine


class TestImagine(unittest.TestCase):

    def test_nesting(self):
        """
        Test that nested imagined scenes shadow earlier imagined scenes.

        :return: None
        """

        @imagine
        def f(x):
            return -x

        self.assertEqual((f(1), f(2), f(3)), (-1, -2, -3))
        with f.at(1).imagine(2).at(2).imagine(3):
            self.assertEqual((f(1), f(2), f(3)), (2, 3, -3))
            with f.at(1).imagine(3):
                self.assertEqual((f(1), f(2), f(3)), (3, 3, -3))
                w = f.at(1).imagine(4).at(3).imagine(6)
                self.assertEqual((f(1), f(2), f(3)), (3, 3, -3))
                with w:
                    self.assertEqual((f(1), f(2), f(3)), (4, 3, 6))
                self.assertEqual((f(1), f(2), f(3)), (3, 3, -3))
                with w:
                    self.assertEqual((f(1), f(2), f(3)), (4, 3, 6))
                self.assertEqual((f(1), f(2), f(3)), (3, 3, -3))
            self.assertEqual((f(1), f(2), f(3)), (2, 3, -3))
        self.assertEqual((f(1), f(2), f(3)), (-1, -2, -3))

    def test_branchine(self):
        """
        Test that the construction of chains of scenes is functional, without side effects
        (except for the duration of a "with" context in which the stack of scenes is temporarily
        activated).

        :return: None
        """

        @imagine
        def f(x):
            return -x

        w = f.at(1).imagine(2)
        w1 = w.at(2).imagine(3)
        w2 = w.at(3).imagine(4)

        self.assertEqual((f(1), f(2), f(3)), (-1, -2, -3))
        with w:
            self.assertEqual((f(1), f(2), f(3)), (2, -2, -3))
        with w1:
            self.assertEqual((f(1), f(2), f(3)), (2, 3, -3))
        with w2:
            self.assertEqual((f(1), f(2), f(3)), (2, -2, 4))
        self.assertEqual((f(1), f(2), f(3)), (-1, -2, -3))


    def test_scoping(self):
        """
        Verify that scene creation is statically scoped in the same that the entire set of scenes
        for a function or method is determined at the time the scenes are defined.


        :return: None
        """

        @imagine
        def f(x):
            return -x

        w = f.at(1).imagine(2)
        w1 = f.at(2).imagine(3)
        w2 = f.at(3).imagine(4)

        self.assertEqual((f(1), f(2), f(3)), (-1, -2, -3))
        with w:
            self.assertEqual((f(1), f(2), f(3)), (2, -2, -3))
            with w1:
                # w1 is all overrides as of time of its creation
                self.assertEqual((f(1), f(2), f(3)), (-1, 3, -3))
            w11 = w1.dynamically_embedded()
            with w11:
                # w11 inherits all overrides currently active
                self.assertEqual((f(1), f(2), f(3)), (2, 3, -3))
            with w2:
                # w2 is all overrides as of time of its creation
                self.assertEqual((f(1), f(2), f(3)), (-1, -2, 4))
            w21 = w2.dynamically_embedded()
            with w21:
                # w11 inherits all overrides currently active
                self.assertEqual((f(1), f(2), f(3)), (2, -2, 4))
            self.assertEqual((f(1), f(2), f(3)), (2, -2, -3))
        self.assertEqual((f(1), f(2), f(3)), (-1, -2, -3))


if __name__ == '__main__':
    unittest.main()
