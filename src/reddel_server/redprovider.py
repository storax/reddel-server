"""RedBaron specific functionality for reddel"""
from __future__ import absolute_import

import collections
import functools

import redbaron

from . import provider
from . import validators

__all__ = ['Position', 'Parent', 'get_parents', 'get_node_of_region', 'RedBaronProvider',
           'red_src', 'red_type', 'red_validate', 'redwraps']

_RED_FUNC_ATTRS = ['red', 'validators']


class Position(collections.namedtuple('Position', ['row', 'column'])):
    """Describes a position in the source code by line number and character position in that line.

    :param row: the line number
    :type row: :class:`int`
    :param column: the position in the line
    :type column: :class:`int`
    """
    __slots__ = ()


class Parent(collections.namedtuple('Parent', ['identifier', 'start', 'end'])):
    """Represents a node type with the bounding location.

    :param identifier: the node type
    :type identifier: :class:`str`
    :param start: the position where the node begins in the code
    :type start: :class:`Position`
    :param end: the position where the node ends in the code
    :type end: :class:`Position`
    """
    __slots__ = ()


def get_parents(red):
    """Yield the parents of the given red node

    :param red: the red baron source
    :type red: :class:`redbaron.base_nodes.Node` | :class:`redbaron.RedBaron`
    :returns: each parent of the given node
    :rtype: Generator[:class:`redbaron.base_nodes.Node`]
    :raises: None
    """
    current = red.parent
    while current:
        yield current
        current = current.parent


def get_node_of_region(red, start, end):
    """Get the node that contains the given region

    :param red: the red baron source
    :type red: :class:`redbaron.RedBaron`
    :param start: position of the beginning of the region
    :type start: :class:`Position`
    :param end: position of the end of the region
    :type end: :class:`Position`
    :returns: the node that contains the region
    :rtype: :class:`redbaron.base_nodes.Node`

    First the nodes at start and end are gathered. Then the common parent is selected.
    If the common parent is a list, the minimum slice is used.
    This makes it easier for the user because he can partially select nodes and
    still gets what he most likely intended to get.

    For example if your region partially selects several lines in a for loop
    and you want to extract them (``|`` shows the region bounds)::

        for i in range(10):
            a = 1 + 2
            b |= 4
            c = 5
            d =| 7

    then we expect to get back::

        b = 4
            c = 5
            d = 7

    Note that the leading tab is missing because it doesn't belong to the ``b = 4`` node.

    .. doctest::

        >>> import redbaron
        >>> import reddel_server
        >>> testsrc = ("for i in range(10):\\n"
        ...            "    a = 1 + 2\\n"
        ...            "    b = 4\\n"
        ...            "    c = 5\\n"
        ...            "    d = 7\\n")
        >>> start = (3, 7)
        >>> end = (5, 8)
        >>> reddel_server.get_node_of_region(redbaron.RedBaron(testsrc), start, end).dumps()
        'b = 4\\n    c = 5\\n    d = 7'

    You can also partially select a list:

    .. doctest::

       >>> testsrc = "[1, 2, 3, 4, 5, 6]"
       >>> start = (1, 8)  # "3"
       >>> end = (1, 14)  # "5"
       >>> reddel_server.get_node_of_region(redbaron.RedBaron(testsrc), start, end).dumps()
       '3, 4, 5'

    """
    snode = red.find_by_position(start)
    enode = red.find_by_position(end)
    if snode == enode:
        return snode
    snodes = [snode] + list(get_parents(snode))
    enodes = [enode] + list(get_parents(enode))
    previous = red
    for snode, enode in list(zip(reversed(snodes), reversed(enodes))):
        # both list of parents should end with the root node
        # so we iterate over the parents in reverse until we
        # reach a parent that is not common.
        # the previous parent then has to encapsulate both
        if snode != enode:
            if hasattr(previous, "node_list"):
                # For lists we want the minimum slice of the list.
                # E.g. the region spans over 2 functions in a big module
                # the common parent would be the root node.
                # We only want the part containing the 2 functions and not everything.
                # Unfortunately we might loose some information if we slice the proxy list.
                # When we use node_list then we keep things like new lines etc.
                try:
                    sindex = previous.node_list.index(snode)
                    eindex = previous.node_list.index(enode)
                except ValueError:
                    # if one of the nodes is not in the list, it means it's not part of
                    # previous value. E.g. previous is a function definition and snode
                    # is part of the arguments while enode is part of the function body.
                    # in that case we take the whole previous node (e.g. the whole function)
                    pass
                else:
                    previous = redbaron.NodeList(previous.node_list[sindex:eindex + 1])
            break
        previous = snode
    return previous


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

        validator = reddel_server.BaronTypeValidator(["def"], single=True)
        class MyProvider(reddel_server.ProviderBase):
            @reddel_server.red_src()
            @reddel_server.red_validate([validator])
            def foo(self, red):
                assert red.type == 'def'

        provider = MyProvider(reddel_server.Server())

        provider.foo("def bar(): pass")  # works

        try:
            provider.foo("1+1")
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
        def wrapped(self, red, *args, **kwargs):
            transformed = red
            for v in validators:
                v(transformed)
                transformed = v.transform(transformed)
            return func(self, transformed, *args, **kwargs)
        wrapped.validators = wrapped.validators or []
        wrapped.validators.extend(validators)
        return wrapped
    return red_validate_dec


def red_type(identifiers, single=True):
    """Create decorator that checks if the root is identified by identifier

    Simple shortcut for doing:

    .. testsetup::

        import reddel_server

        identifiers = ['def', 'ifelseblock']
        single=True

    .. testcode::

        reddel_server.red_validate([reddel_server.BaronTypeValidator(identifiers, single=single)])

    See :func:`reddel_server.red_validate`.

    :param identifiers: red baron node identifiers
    :type identifiers: list of :class:`str`
    :param single: expect a single node in the initial node list. Pass on the first node.
    :type single: :class:`bool`
    :returns: the decorator
    :rtype: :data:`types.FunctionType`
    """
    return red_validate([validators.BaronTypeValidator(identifiers, single=single)])


class RedBaronProvider(provider.ProviderBase):
    """Provider for inspecting and transforming source code via redbaron."""

    @red_src(dump=False)
    def analyze(self, red, deep=2, with_formatting=False):
        """Return the red baron help string for the given source

        .. table::

            +--------------+----------------+---------------+------------------+
            | source input | outputs source | allowed types | only single node |
            +==============+================+===============+==================+
            | Yes          | No             | Any           | No               |
            +--------------+----------------+---------------+------------------+

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
    @red_type(["def"])
    def rename_arg(self, red, oldname, newname):
        """Rename a argument

        .. table::

            +--------------+----------------+---------------+------------------+
            | source input | outputs source | allowed types | only single node |
            +==============+================+===============+==================+
            | Yes          | Yes            | def           | Yes              |
            +--------------+----------------+---------------+------------------+

        :param red: the red baron source
        :type red: :class:`redbaron.RedBaron`
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
            >>> print(p.rename_arg(src, "arg2", "renamed"))
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
    @red_type(["def"])
    def get_args(self, red):
        """Return a list of args and their default value (if any) as source code

        .. table::

            +--------------+----------------+---------------+------------------+
            | source input | outputs source | allowed types | only single node |
            +==============+================+===============+==================+
            | Yes          | No             | def           | Yes              |
            +--------------+----------------+---------------+------------------+

        :param red: the red baron source
        :type red: :class:`redbaron.RedBaron`
        :returns: list of argument name and default value.
        :rtype: :class:`list` of :class:`tuple` or :class:`str` and :class:`str` | ``None``

        The default value is always a string, except for arguments without one which will be
        represented as None.

        .. doctest::

            >>> import reddel_server
            >>> p = reddel_server.RedBaronProvider(reddel_server.Server())
            >>> src = \"\"\"def foo(arg1, arg2, kwarg1=None, kwarg2=1, kwarg3='None'):
            ...     arg2 = arg2 or ""
            ...     return arg2 + func(arg1, "arg2 arg2") + kwarg2
            ... \"\"\"
            >>> p.get_args(src)
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
    @red_type(["def"])
    def add_arg(self, red, index, arg):
        """Add a argument at the given index

        .. table::

            +--------------+----------------+---------------+------------------+
            | source input | outputs source | allowed types | only single node |
            +==============+================+===============+==================+
            | Yes          | Yes            | def           | Yes              |
            +--------------+----------------+---------------+------------------+

        :param red: the red baron source
        :type red: :class:`redbaron.RedBaron`
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
            >>> print(p.add_arg(src, 3, "kwarg3=123"))
            def foo(arg1, arg2, kwarg2=1, kwarg3=123):
                arg2 = arg2 or ""
                return arg2 + func(arg1, "arg2 arg2") + kwarg2
            <BLANKLINE>

        """
        red.arguments.insert(index, arg)
        return red

    @red_src(dump=False)
    def get_parents(self, red, pos):
        """Return a list of parents (scopes) relative to the given position

        .. table::

            +--------------+----------------+---------------+------------------+
            | source input | outputs source | allowed types | only single node |
            +==============+================+===============+==================+
            | Yes          | No             | Any           | No               |
            +--------------+----------------+---------------+------------------+

        :param red: the red baron source
        :type red: :class:`redbaron.RedBaron`
        :param pos: the position to query
        :type pos: :class:`Position`
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
            >>> pprint.pprint(p.get_parents(src, reddel_server.Position(7, 32)))
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
        current = red.find_by_position(pos)
        while current != red:
            region = current.absolute_bounding_box
            nodetype = current.type
            tl = Position(*region.top_left.to_tuple())
            br = Position(*region.bottom_right.to_tuple())
            current = current.parent
            # if previous bounding box is the same take the parent higher in the hierachy
            if parents and parents[-1][1] == tl and parents[-1][2] == br:
                parents.pop()
            parents.append(Parent(nodetype, tl, br))
        return parents
