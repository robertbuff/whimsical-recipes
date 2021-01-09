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
#
# The following is an example:
#
#    class Test:
#        @imagine
#        def a(self, x):
#            return x + 1
#
#    t = Test()
#    print(t.a(0), t.a(1), t.a(2))
#    # Test.a is the reference to the function, and t is passed in because
#    # the override is specific to an instance of Test.
#    with Test.a.at(t, 0).imagine(2), Test.a.at(t, 1).imagine(3):
#        print(t.a(0), t.a(1), t.a(2))
#    print(t.a(0), t.a(1), t.a(2))

from typing import Any, Union
import types


def imagine(body: types.FunctionType) -> types.FunctionType:
    """
    Decorate a function for which imagined mappings can then be defined.
    If f is the decorated function or method, we can then compute function values
    under new mapping assumptions with::

        with f.at(x).imagine(y):
            print(f(x))
        with obj.f.at(obj, x).imagine(y):
            print(obj.f(x))

    The reach of the definition extends dynamically beyond the body of the with statement
    to the entire code base, so this is NOT a function or method redefinition in a local
    scope. It is a temporary redefinition of the original function or method body itself,
    in a dynamic scope created in a "with" context. We are mixing static and dynamic
    scoping! This is not solidly in the functional programming paradigm, it's a paradigm
    of code injection that becomes necessary if the code base into which the override is
    injected does not provide an API that's sufficiently powerful to allow the open passing
    of altered scenes. Think of below as a thought experiment. Be careful when using it as
     a design principle in larger software systems.

    :param body: function or method to be decorated
    :returns: a wrapper function with new methods 'at', 'imagine'
    """
    f = __Imagine(body)

    def wrapper(*args, **kwargs) -> Any:
        return f(*args, **kwargs)

    wrapper.at = lambda *args, **kwargs: f.at(*args, **kwargs)
    wrapper.imagine = lambda value: f.imagine(value)
    return wrapper


class __Imagine:
    """
    A helper class that stores a LIFO stack of "scenes" identifying points in
    parameter space for which we override the functional specification of the
    decorated function or method. The stack of scenes is a global variable.
    A new scene is effective in the entire code base from the moment it is
    created at the beginning of a "with" context, and only removed when the
    context is exited.
    """

    class Pop:

        def __init__(self, scenes: list, high_water_mark: int) -> None:
            """
            Used inside a "with" context and removes temporary scenes from the stack
            of scenes.

            :param scenes: the stack with scenes in FIFO order
            :param high_water_mark: to what level should we pop scenes at exit
            """
            self.__scenes = scenes
            self.__high_water_mark = high_water_mark

        def __enter__(self) -> 'WakeUp':
            """
            No-op.
            :return: self
            """
            return self

        def __exit__(self, *_) -> None:
            """
            Call when the "with" context is exited, and removes those scenes with imagined
            function or method values from the stack that have been put there when the
            "with" context was created.

            :param _: ignored, what we do is unconditional
            :return: None
            """
            while len(self.__scenes) > self.__high_water_mark:
                self.__scenes.pop()

    class At:
        """
        A helper class that separates the definition of the point in parameter space for
        which we define an override from the announcement of the override value. We can
        think of an override action as adding a "scene" consisting of a "guard" and a
        "value." An instance of "At" embodies a guard that checks for a particular
        point. We can picture guards that check for ranges or other types of sub-domains.
        """

        def __init__(self, owner: '__Imagine', *args, **kwargs) -> None:
            """
            An instance of 'At' is used to freeze a point in parameter space for which we
            imagine a different mapping, replacing any calculated function value. This
            instance is typically consumed immediately, but it's conceivable to use it
            like this::

                at = f.at(x, y, z)
                for i in (0, 1, 2):
                    with at.imagine(i):
                        print(f(i))

            :param owner: the object used for storage by the wrapper decorator
            :param args: the positional components of the point in parameter space for which
            an override is defined
            :param kwargs: the keyword components of the point in parameter space for which
            an override is defined
            """
            self.__owner = owner
            self.__args = args
            self.__kwargs = kwargs

        def imagine(self, value: Any) -> Any:
            """
            Registers a value for the point in parameter space identified in this object.
            The value will be pushed IN-PLACE onto the stack of scenes belonging to the
            decorated function or method. We expect this function to be called inside a
            "with" context. The return value will take care of the removal of the scene
            at exit of the contect.

            :param value: value of any type
            :return: a context exit handler that pops the value off the stack of scenes
            """

            def guard(*args, **kwargs) -> bool:
                # We use __eq__ to test equality
                return args == self.__args and kwargs == self.__kwargs

            return self.__owner.imagine_at(guard, value)

    def __init__(self, body: types.FunctionType) -> None:
        """
        Initialize wrapper class with original function or method, and prepare stack
        of pretend mappings. Stack frames are created and removed inside with contexts.

        :param body: original function or method for which new mappings can be defined
        """
        self.__body = body
        self.__scenes = []

    def __call__(self, *args, **kwargs) -> Any:
        """
        Before calling the original function or methods, go through the stack of scenes
        and try to find a temporary, "imagined" value for (*args, **kwargs). If none exist
        we proceed and evaluate the original. Scenes are consulted in LIFO order.

        :param args: positional arguments, including "self" if we decorated a method
        :param kwargs: keyword arguments
        :return: the imagined mapping, or the value yielded by the evaluation of the original
        """
        for guard, value in reversed(self.__scenes):
            if guard is None or guard(*args, **kwargs):
                return value
        return self.__body(*args, **kwargs)

    def at(self, *args, **kwargs):
        """
        Define the point in parameter space for which we define a temporary mapping, ignoring
        any previous computations performed by the original function. "f.at()" is followed by
        "imagine()", which specifies the enw value.

        Note that keyword defaults are not consulted,
        so the omission of a keyword in kwargs defines a point that's different from a keyword
        combination with an explicit default value, even if it happens to be equal to the default.

        Also note that we don't have to limit an imagined override to a single point. We can call
        "f.imagine()" on the function or method directly.

        :param args: the positional components in the parameter space for which we define a new value
        :param kwargs: the keyword components in the parameter space for which we define a new value
        :return: a class object with one useful method: "imagine"
        """
        return self.At(self, *args, **kwargs)

    def imagine(self, value: Any) -> Pop:
        """
        Registers a scene in which the provided value will be used in place of any calculated or
        previously imagined value for all argument combinations, Turns the function or method
        into a constant. This is done IN-PLACE.

        :param value: new value to substitute throughout
        :return: a helper object used by the context manager to pop imagined scenes
        """
        return self.imagine_at(None, value)

    def imagine_at(self, guard: Union[types.FunctionType, types.LambdaType], value: Any) -> Pop:
        """
        Registers a scene in which the provided value will be used in place of any calculated or
        previously imagined value for the provided point in arg space. The point is defined by
        the guard function which checks supplied parameters. Using a guard in this manner allows
        to use this technology for ranges and other sub-domains later. We are modifying the
        decorated function or method IN-PLACE.

        The scope of this override extends to the end of the current "with" context.

        :param guard: a function that takes positionals (including "self") and keyword arguments
        and returns Trye if the function value should be substituted
        :param value: new value to substitute in place of any calculated value, provided
        the guard allows it
        :return: a helper object used by the context manager to pop imagined scenes
        """
        high_water_mark = len(self.__scenes)
        self.__scenes.append((guard, value))
        return self.Pop(self.__scenes, high_water_mark)
