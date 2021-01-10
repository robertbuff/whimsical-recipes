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
#    with Test.a.at(t, 0).imagine(2).at(t, 1).imagine(3):
#        print(t.a(0), t.a(1), t.a(2))
#    print(t.a(0), t.a(1), t.a(2))
#
# "at" and "imagined" can also be separated:
#
#    new_world = Test.a.at(t, 0).imagine(2).at(t, 1).imagine(3)
#    with new_world:
#        print(t.a(0), t.a(1), t.a(2))
#    # we can use new_world again:
#    with new_world:
#        print(t.a(0), t.a(1), t.a(2))
#
# Here's another sequence and what it prints, showing nesting:
#
#    @imagine def f(x): return x + 1
#
#    print(f(0))  # prints 1
#    with f.at(0).imagine(-1):
#        print(f(0))  # prints -1
#        with f.at(0).imagine(-2):
#            print(f(0))  # prints -2
#        w = f.at(0).imagine(-2)
#        with w:
#            print(f(0))  # prints -2
#        print(f(0))  # prints -1
#    print(f(0))  # prints 1

from typing import Any, Union
from types import FunctionType, LambdaType


def imagine(body: FunctionType) -> FunctionType:
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
    f = _Stack(body)

    def wrapper(*args, **kwargs) -> Any:
        return f(*args, **kwargs)

    wrapper.at = lambda *args, **kwargs: f.at(*args, **kwargs)
    wrapper.imagine = lambda value: f.imagine(value)
    return wrapper


class _Cursor:
    """
    A helper class for a shared object holding the top pointer into the stack of overrides.
    Imagines "scenes" pushed onto the stack are temporarily activated inside "with" contexts,
    as follows::

        new_world = f.at(0).imagine(1)
        print(f{0)) # prints old value
        with new_world:
            print(f{0}} # prints 1

    This scheme is functional until the point the "with" context is entered, when the underlying
    function or method is modified to consult the overrides. This temporary change dynamically
    applies globally, in the entire code space. The temporary changes are "injected" into the
    function or method.
    """

    def __init__(self) -> None:
        """
        Initialize top pointer to None.
        """
        self.top = None


class _Scene:
    """
    A helper class holding one assignment, or "scene", containing a new, temporary mapping of a point
    in parameter space to a value. Scenes are stored in a singly-linked list.
    """

    def __init__(self, parent: Union['_Scene, None'], guard: Union[FunctionType, LambdaType, None], value: Any):
        """
        Scenes are linked in a singly-linked list.

        :param parent: the previous scene, or None if this is the same scene for this function or method
        :param guard: a function checking arguments, returning True oif the override holds for them; None
        means the override holds everywhere
        :param value: the override value
        """
        self.__parent = parent
        self.__guard = guard
        self.__value = value

    def applies(self, *args, **kwargs) -> bool:
        """
        An oracle that returns True if the passed-in arguments, positional and keyword, identify the point
        or sub-space for which an override is defined.

        :param args: the positional components of the point in parameter space for which
        an override is defined
        :param kwargs: the keyword components of the point in parameter space for which
        an override is defined
        :return: True if this is the imagined point, False otherwise
        """
        return self.__guard is None or self.__guard(*args, **kwargs)

    @property
    def value(self):
        """
        Accessor.

        :return: the value
        """
        return self.__value

    @property
    def parent(self):
        """
        Accessor

        :return: the parent or None
        """
        return self.__parent


class _At:
    """
    A helper class that separates the definition of the point in parameter space for
    which we define an override from the announcement of the override value. We can
    think of an override action as adding a "scene" consisting of a "guard" and a
    "value." An instance of "_At" embodies a guard that checks for a particular
    point. We can picture guards that check for ranges or other types of sub-domains.
    """

    def __init__(self, cursor: _Cursor, top: _Scene, *args, **kwargs) -> None:
        """
        An instance of 'At' is used to freeze a point in parameter space for which we
        imagine a different mapping, replacing any calculated function value. This
        instance is typically consumed immediately, but it's conceivable to use it
        like this::

            at = f.at(x, y, z)
            for i in (0, 1, 2):
                with at.imagine(i):
                    print(f(i))

        :param cursor: the shared object holding pointers used for managing stack positions;
        updated with global effect as "with" contexts are entered and exited
        :param top: the top of the scene stack at the time we identify the point in parameter
        space for which a new imagined value is defined
        :param args: the positional components of the point in parameter space for which
        an override is defined
        :param kwargs: the keyword components of the point in parameter space for which
        an override is defined
        """
        self.__cursor = cursor
        self.__top = top
        self.__args = args
        self.__kwargs = kwargs

    def imagine(self, value: Any) -> '_Imagine':
        """
        Registers a value for the point in parameter space identified in this object.
        The value will be pushed IN-PLACE onto the stack of scenes belonging to the
        decorated function or method. We expect this function to be called inside a
        "with" context. The return value will take care of the removal of the scene
        at exit of the context.

        :param value: value of any type
        :return: a context exit handler that pops the value off the stack of scenes
        """

        def guard(*args, **kwargs) -> bool:
            # We use __eq__ to test equality
            return args == self.__args and kwargs == self.__kwargs

        return _Imagine(self.__cursor, _Scene(self.__top, guard, value))


class _Imagine:
    """
    A helper class that holds the temporary assignment of a point or otherwise
    defined sub-space in parameter space to an alternate value. "_Imagine" completes
    "_At." This helper class is also responsible for popping off the temporary
    assignment when the enclosing "with" context ends.
    """

    def __init__(self, cursor: _Cursor, top: _Scene) -> None:
        """
        Used inside a "with" context, pushes a new override value, and turns on and
        removes temporary scenes from the stack of scenes as "with" contexts are entered
        and exited.

        :param cursor: the shared object holding pointers used for managing stack positions
        :param top: the top of the scene stack at the time we identify the point in parameter
        space for which a new imagined value is defined
        """
        self.__cursor = cursor
        self.__last = None
        self.__top = top

    def at(self, *args, **kwargs) -> _At:
        """
        Allow chaining of more than one override. There's two ways to define more than
        one function or method override if they sit on the same function or method f::
        
            with f.at(0).imagine(1), f.at(1).imagine(2):
                pass
            with f.at(0).imagine(1).at(1).imagine(2):
                pass

        :param args: the positional components of the point in parameter space for which
        an override is defined
        :param kwargs: the keyword components of the point in parameter space for which
        an override is defined
        :return: a helper object on which we can call 'imagine' in order to define the override
        """
        return _At(self.__cursor, self.__top, *args, **kwargs)

    def __enter__(self) -> '_Imagine':
        """
        Turns on recently added imagined values by moving the global top pointer of the shared cursor
        object to the top constructed during the assembly of "_At" and "_Imagine" objects.

        :return: self
        """
        self.__last = self.__cursor.top
        self.__cursor.top = self.__top
        return self

    def __exit__(self, *_) -> None:
        """
        Call when the "with" context is exited, and removes those scenes with imagined
        function or method values from the stack that have been put there when the
        "with" context was entered.

        :param _: ignored, what we do is unconditional
        :return: None
        """
        self.__cursor.top = self.__last


class _Stack:
    """
    A helper class that stores a LIFO stack of "scenes" identifying points in
    parameter space for which we override the functional specification of the
    decorated function or method. The stack of scenes is a global variable.
    A new scene is effective in the entire code base from the moment it is
    created at the beginning of a "with" context, and only removed when the
    context is exited.
    """

    def __init__(self, body: FunctionType) -> None:
        """
        Initialize wrapper class with original function or method, and prepare stack
        of pretend mappings. Stack frames are created and removed inside with contexts.

        :param body: original function or method for which new mappings can be defined
        """
        self.__body = body
        self.__cursor = _Cursor()

    def __call__(self, *args, **kwargs) -> Any:
        """
        Before calling the original function or methods, go through the stack of scenes
        and try to find a temporary, "imagined" value for (*args, **kwargs). If none exist
        we proceed and evaluate the original. Scenes are consulted in LIFO order.

        :param args: positional arguments, including "self" if we decorated a method
        :param kwargs: keyword arguments
        :return: the imagined mapping, or the value yielded by the evaluation of the original
        """
        p = self.__cursor.top
        while p is not None:
            if p.applies(*args, **kwargs):
                return p.value
            p = p.parent
        return self.__body(*args, **kwargs)

    def at(self, *args, **kwargs) -> _At:
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
        return _At(self.__cursor, self.__cursor.top, *args, **kwargs)

    def imagine(self, value: Any) -> _Imagine:
        """
        Registers a scene in which the provided value will be used in place of any calculated or
        previously imagined value for all argument combinations, Turns the function or method
        into a constant. This is done IN-PLACE.

        :param value: new value to substitute throughout
        :return: a helper object used by the context manager to pop imagined scenes
        """
        return _Imagine(self.__cursor, _Scene(self.__cursor.top, None, value))
