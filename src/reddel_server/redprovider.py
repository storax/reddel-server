"""RedBaron specific functionality for reddel"""
from __future__ import absolute_import

import functools

import redbaron

from . import provider
from . import redlib
from . import validators

__all__ = ['RedBaronProvider', 'red_src', 'red_validate', 'redwraps']

_RED_FUNC_ATTRS = ['red', 'validators']


def redwraps(towrap):
    """Use this when creating decorators instead of :func:`functools.wraps`

    :param towrap: the function to wrap
    :type towrap: :data:`types.FunctionType`
    :returns: the decorator
    :rtype: :data:`types.FunctionType`

    Makes sure to transfer special reddel attributes to the wrapped function.
    On top of that uses :func:`functools.wraps`.

    Example:


    .. testcode::

        import reddel_server

        def my_decorator(func):
            @reddel_server.redwraps(func)  # here you would normally use functools.wraps
            def wrapped(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapped

    """
    def redwraps_dec(func):
        if towrap:
            func = functools.wraps(towrap)(func)
        for attr in _RED_FUNC_ATTRS:
            val = getattr(towrap, attr, None)
            setattr(func, attr, val)
        return func
    return redwraps_dec


def red_src(dump=True):
    """Create decorator that converts the first argument into a red baron source

    :param dump: if True, dump the return value from the wrapped function.
                 Expects the return type to be a :class:`redbaron.RedBaron` object.
    :type dump: :class:`bool`
    :returns: the decorator
    :rtype: :data:`types.FunctionType`

    Example:

    .. testcode::

        import redbaron
        import reddel_server

        class MyProvider(reddel_server.ProviderBase):
            @reddel_server.red_src(dump=False)
            def inspect_red(self, red):
                assert isinstance(red, redbaron.RedBaron)
                red.help()

        MyProvider(reddel_server.Server()).inspect_red("1+1")

    .. testoutput::

        0 -----------------------------------------------------
        BinaryOperatorNode()
          # identifiers: binary_operator, binary_operator_, binaryoperator, binaryoperatornode
          value='+'
          first ->
            IntNode()
              # identifiers: int, int_, intnode
              value='1'
          second ->
            IntNode()
              # identifiers: int, int_, intnode
              value='1'

    By default the return value is expected to be a transformed :class:`redbaron.RedBaron` object
    that can be dumped. This is useful for taking a source as argument, transforming it and returning it back
    so that it the editor can replace the original source:

    .. doctest::

        >>> import redbaron
        >>> import reddel_server

        >>> class MyProvider(reddel_server.ProviderBase):
        ...     @reddel_server.red_src(dump=True)
        ...     def echo(self, red):
        ...         assert isinstance(red, redbaron.RedBaron)
        ...         return red

        >>> MyProvider(reddel_server.Server()).echo("1+1")
        '1+1'

    """
    def red_src_dec(func):
        @redwraps(func)
        def wrapped(self, src, *args, **kwargs):
            red = redbaron.RedBaron(src)
            retval = func(self, red, *args, **kwargs)
            if dump and retval:
                retval = retval.dumps()
            return retval
        return wrapped
    return red_src_dec


def red_validate(validators):
    """Create decorator that adds the given validators to the wrapped function

    :param validators: the validators
    :type validators: :class:`reddel_server.ValidatorInterface`

    Validators can be used to provide sanity checks.
    :meth:`reddel_server.ProviderBase.list_methods` uses them to filter
    out methods that are incompatible with the given input, which can be used
    to build dynamic UIs.

    To use this validator is very simple.
    Create one or more validator instances (have to inherit from :class:`reddel_server.ValidatorInterface`)
    and provide them as the argument:

    .. testcode::

        import reddel_server

        validator1 = reddel_server.SingleNodeValidator()
        validator2 = reddel_server.TypeValidator(["def"])
        class MyProvider(reddel_server.ProviderBase):
            @reddel_server.red_src()
            @reddel_server.red_validate([validator1, validator2])
            def foo(self, red, start, end):
                assert red.type == 'def'

        provider = MyProvider(reddel_server.Server())

        provider.foo("def bar(): pass", start=None, end=None)  # works

        try:
            provider.foo("1+1", start=None, end=None)
        except reddel_server.ValidationException:
            pass
        else:
            assert False, "Validator should have raised"

    On top of that validators also can implement a :meth:`reddel_server.ValidatorInterface.transform`
    function to transform the red source on the way down.
    The transformed value is passed to the next validator and eventually into the function.

    See `Validators`_.
    """
    def red_validate_dec(func):
        @redwraps(func)
        def wrapped(self, red, start, end, *args, **kwargs):
            transformed = red
            for v in validators:
                v(transformed, start, end)
                transformed, start, end = v.transform(transformed, start, end)
            return func(self, transformed, start, end, *args, **kwargs)
        wrapped.validators = wrapped.validators or []
        wrapped.validators.extend(validators)
        return wrapped
    return red_validate_dec


class RedBaronProvider(provider.ProviderBase):
    """Provider for inspecting and transforming source code via redbaron."""

    @red_src(dump=False)
    def analyze(self, red, deep=2, with_formatting=False):
        """Return the red baron help string for the given source

        .. table::

            +--------------+----------------+--------+------------------+---------------+
            | source input | outputs source | region | only single node | allowed types |
            +==============+================+========+==================+===============+
            | Yes          | No             | No     | No               | Any           |
            +--------------+----------------+--------+------------------+---------------+

        :param red: the red baron source
        :type red: :class:`redbaron.RedBaron`
        :param deep: how deep the nodes get printed
        :type deep: :class:`int`
        :param with_formatting: also analyze formatting nodes
        :type with_formatting: :class:`bool`
        :returns: the help text
        :rtype: :class:`str`

        Example:

        .. doctest::

            >>> import reddel_server
            >>> p = reddel_server.RedBaronProvider(reddel_server.Server())
            >>> print(p.analyze("1+1"))
            BinaryOperatorNode()
              # identifiers: binary_operator, binary_operator_, binaryoperator, binaryoperatornode
              value='+'
              first ->
                IntNode()
                  # identifiers: int, int_, intnode
                  value='1'
              second ->
                IntNode()
                  # identifiers: int, int_, intnode
                  value='1'

        """
        return "\n".join(red.__help__(deep=deep, with_formatting=False))

    @red_src()
    @red_validate([validators.OptionalRegionValidator(),
                   validators.SingleNodeValidator(),
                   validators.TypeValidator(["def"])])
    def rename_arg(self, red, start, end, oldname, newname):
        """Rename a argument

        .. table::

            +--------------+----------------+----------+------------------+---------------+
            | source input | outputs source | region   | only single node | allowed types |
            +==============+================+==========+==================+===============+
            | Yes          | Yes            | Optional | Yes              | def           |
            +--------------+----------------+----------+------------------+---------------+

        :param red: the red baron source
        :type red: :class:`redbaron.RedBaron`
        :param start: the start position of the selected region, if any.
        :type start: :class:`reddel_server.Position` | ``None``
        :param end: the end position of the selected region, if any.
        :type end: :class:`reddel_server.Position` | ``None``
        :param oldname: name of the argument to rename
        :type oldname: :class:`str`
        :param newname: new name for the argument
        :type newname: :class:`str`
        :returns: the transformed source code
        :rtype: :class:`redbaron.RedBaron`

        Example:

        .. doctest::

            >>> import reddel_server
            >>> p = reddel_server.RedBaronProvider(reddel_server.Server())
            >>> src = \"\"\"def foo(arg1, arg2, kwarg2=1):  # arg2
            ...     arg2 = arg2 or ""
            ...     return arg2 + func(arg1, "arg2 arg2") + kwarg2
            ... \"\"\"
            >>> print(p.rename_arg(src, None, None, "arg2", "renamed"))
            def foo(arg1, renamed, kwarg2=1):  # arg2
                renamed = renamed or ""
                return renamed + func(arg1, "arg2 arg2") + kwarg2
            <BLANKLINE>
        """
        for arg in red.arguments:
            if arg.target.value == oldname:
                arg.target.value = newname
                break
        else:
            raise ValueError("Expected argument %s to be one of %s"
                             % (oldname, [arg.target.value for arg in red.arguments]))
        namenodes = red.value.find_all("name", value=oldname)
        for node in namenodes:
            node.value = newname
        return red

    @red_src(dump=False)
    @red_validate([validators.OptionalRegionValidator(),
                   validators.SingleNodeValidator(),
                   validators.TypeValidator(["def"])])
    def get_args(self, red, start, end):
        """Return a list of args and their default value (if any) as source code

        .. table::

            +--------------+----------------+----------+------------------+---------------+
            | source input | outputs source | region   | only single node | allowed types |
            +==============+================+==========+==================+===============+
            | Yes          | No             | Optional | Yes              | def           |
            +--------------+----------------+----------+------------------+---------------+

        :param red: the red baron source
        :type red: :class:`redbaron.RedBaron`
        :param start: the start position of the selected region, if any.
        :type start: :class:`reddel_server.Position` | ``None``
        :param end: the end position of the selected region, if any.
        :type end: :class:`reddel_server.Position` | ``None``
        :returns: list of argument name and default value.
        :rtype: :class:`list` of :class:`tuple` with :class:`str` and :class:`str` | ``None`` in it.

        The default value is always a string, except for arguments without one which will be
        represented as None.

        .. doctest::

            >>> import reddel_server
            >>> p = reddel_server.RedBaronProvider(reddel_server.Server())
            >>> src = \"\"\"def foo(arg1, arg2, kwarg1=None, kwarg2=1, kwarg3='None'):
            ...     arg2 = arg2 or ""
            ...     return arg2 + func(arg1, "arg2 arg2") + kwarg2
            ... \"\"\"
            >>> p.get_args(src, None, None)
            [('arg1', None), ('arg2', None), ('kwarg1', 'None'), ('kwarg2', '1'), ('kwarg3', "'None'")]

        """
        args = []
        for arg in red.arguments:
            if isinstance(arg, (redbaron.ListArgumentNode, redbaron.DictArgumentNode)):
                args.append((arg.dumps(), None))
                continue
            target = arg.target.value
            if arg.value:
                value = arg.value.dumps()
            else:
                value = None
            args.append((target, value))
        return args

    @red_src()
    @red_validate([validators.OptionalRegionValidator(),
                   validators.SingleNodeValidator(),
                   validators.TypeValidator(["def"])])
    def add_arg(self, red, start, end, index, arg):
        """Add a argument at the given index

        .. table::

            +--------------+----------------+----------+------------------+---------------+
            | source input | outputs source | region   | only single node | allowed types |
            +==============+================+==========+==================+===============+
            | Yes          | Yes            | Optional | Yes              | Yes           |
            +--------------+----------------+----------+------------------+---------------+

        :param red: the red baron source
        :type red: :class:`redbaron.RedBaron`
        :param start: the start position of the selected region, if any.
        :type start: :class:`reddel_server.Position` | ``None``
        :param end: the end position of the selected region, if any.
        :type end: :class:`reddel_server.Position` | ``None``
        :param index: position of the argument. ``0`` would mean to put the argument in the front.
        :type index: :class:`int`
        :param arg: the argument to add
        :type arg: :class:`str`
        :returns: the transformed source code
        :rtype: :class:`redbaron.RedBaron`

        Example:

        .. doctest::

            >>> import reddel_server
            >>> p = reddel_server.RedBaronProvider(reddel_server.Server())
            >>> src = \"\"\"def foo(arg1, arg2, kwarg2=1):
            ...     arg2 = arg2 or ""
            ...     return arg2 + func(arg1, "arg2 arg2") + kwarg2
            ... \"\"\"
            >>> print(p.add_arg(src, start=None, end=None, index=3, arg="kwarg3=123"))
            def foo(arg1, arg2, kwarg2=1, kwarg3=123):
                arg2 = arg2 or ""
                return arg2 + func(arg1, "arg2 arg2") + kwarg2
            <BLANKLINE>

        """
        red.arguments.insert(index, arg)
        return red

    @red_src(dump=False)
    @red_validate([validators.MandatoryRegionValidator()])
    def get_parents(self, red, start, end):
        """Return a list of parents (scopes) relative to the given position

        .. table::

            +--------------+----------------+-----------+------------------+---------------+
            | source input | outputs source | region    | only single node | allowed types |
            +==============+================+===========+==================+===============+
            | Yes          | No             | Mandatory | No               | Any           |
            +--------------+----------------+-----------+------------------+---------------+

        :param red: the red baron source
        :type red: :class:`redbaron.RedBaron`
        :param start: the start position of the selected region.
        :type start: :class:`reddel_server.Position`
        :param end: the end position of the selected region.
        :type end: :class:`reddel_server.Position`
        :returns: a list of parents starting with the element at position first.
        :rtype: :class:`list` of the parents.
                A parent is represented by a :class:`Parent` of the
                type, top-left, bottom-right position.
                Each position is a :class:`Position` object.

        .. doctest::

            >>> import reddel_server
            >>> import pprint
            >>> p = reddel_server.RedBaronProvider(reddel_server.Server())
            >>> src = \"\"\"def foo(arg1):
            ...     arg2 = arg2 or ""
            ...     if Ture:
            ...         try:
            ...             pass
            ...         except:
            ...             func(subfunc(arg1="asdf"))
            ... \"\"\"
            >>> pprint.pprint(p.get_parents(src, reddel_server.Position(7, 32), reddel_server.Position(7, 32)))
            [Parent(identifier='string', start=Position(row=7, column=31), end=Position(row=7, column=36)),
             Parent(identifier='call_argument', start=..., end=...),
             Parent(identifier='call', start=..., end=...),
             Parent(identifier='call_argument', start=..., end=...),
             Parent(identifier='call', start=..., end=...),
             Parent(identifier='atomtrailers', start=..., end=...),
             Parent(identifier='except', start=..., end=...),
             Parent(identifier='try', start=..., end=...),
             Parent(identifier='ifelseblock', start=..., end=...),
             Parent(identifier='def', start=..., end=...)]

        """
        parents = []
        current = redlib.get_node_of_region(red, start, end)
        while current != red:
            region = current.absolute_bounding_box
            nodetype = current.type
            start = redlib.Position(*region.top_left.to_tuple())
            end = redlib.Position(*region.bottom_right.to_tuple())
            current = current.parent
            # if previous bounding box is the same take the parent higher in the hierachy
            if parents and parents[-1].start == start and parents[-1].end == end:
                parents.pop()
            parents.append(redlib.Parent(nodetype, start, end))
        return parents
