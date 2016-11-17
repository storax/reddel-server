"""Provide functionality to reddel"""
from __future__ import absolute_import

import types

import redbaron

from . import exceptions
from . import utils
from . import validators

__all__ = ['ProviderBase', 'ChainedProvider', 'RedBaronProvider',
           'red_src', 'red_type', 'red_validate']


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
        @utils.redwraps(func)
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
        @utils.redwraps(func)
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


class ProviderBase(object):
    """Base class for all Providers.

    A provider exposes methods via the :class:`reddel_server.Server` to clients.
    By default all public methods (that do not start with an underscore) are exposed.

    Creating your own basic provider is very simple:

    .. testcode::

        import reddel_server

        class MyProvider(reddel_server.ProviderBase):
            def exposed(self):
                print("I'm exposed")
            def private(self):
                print("I'm private")

    .. testcode::

        server = reddel_server.Server()
        provider = MyProvider(server)
        server.set_provider(provider)

    When starting reddel from the command line via the command ``reddel``,
    it's automatically setup with a :class:`reddel_server.ChainedProvider`,
    which combines multiple providers together.
    It also gives you the ability to call :meth:`reddel_server.ChainedProvider.add_provider`
    from a client.

    You can get a list of all methods provided by a provider by calling
    :meth:`reddel_server.ProviderBase.list_methods`.
    """
    def __init__(self, server):
        """Initialize provider

        :param server: the server that is using the provider
        :type server: :class:`reddel_server.Server`
        """
        super(ProviderBase, self).__init__()
        self._server = server

    def __str__(self):
        return "<{classname} at {memloc}>".format(classname=self.__class__.__name__, memloc=hex(id(self)))

    def __repr__(self):
        return "{classname}({server!r})".format(classname=self.__class__.__name__,
                                                server=self.server)

    @property
    def server(self):
        return self._server

    def _get_methods(self, src=None):
        """Return a dictionary of all methods provided.

        :param source: if ``src`` return only compatible methods
        :type source: :class:`redbaron.RedBaron`
        :returns: dict method names and methods
        """
        d = {}
        for attrname in dir(self):
            attr = getattr(self, attrname)
            if not attrname.startswith('_') and isinstance(attr, (types.FunctionType, types.MethodType)):
                if src and hasattr(attr, 'validators'):
                    for v in (attr.validators or []):
                        try:
                            v(src)
                        except exceptions.ValidationException:
                            break
                    else:
                        d[attrname] = attr
                else:
                    d[attrname] = attr
        return d

    def list_methods(self, src=None):
        """Return a list of methods that this Provider exposes to clients

        To get more information for each method use :meth:`reddel_server.ProviderBase.help`.

        By default this returns all available methods.
        But it can also be used to only get methods that actually work on a given source.
        This feature might be handy to dynamically build UIs that adapt to the current context.

        To write your own methods that can be filtered in the same way, use the
        :func:`reddel_server.red_validate` or :func:`reddel_server.red_type` decorators.

        :param source: if ``src`` return only compatible methods
        :type source: :class:`str`
        :returns: list of :class:`str`
        """
        if src:
            src = redbaron.RedBaron(src)
        return sorted(self._get_methods(src=src).keys())

    def _get_method(self, name):
        return getattr(self, name)

    def help(self, name):
        """Return the docstring of the method

        :param name: the name of the method.
        :type name: :class:`str`

        Example:

        .. testcode::

            import reddel_server
            server = reddel_server.Server()
            p = reddel_server.ProviderBase(server)
            for m in p.list_methods():
                print(m + ":")
                print(p.help(m))

        .. testoutput::
            :hide:

            ...

        """
        method = getattr(self, name)
        return method.__doc__

    def reddel_version(self):
        """Return the reddel version"""
        import reddel_server
        return reddel_server.__version__

    def echo(self, echo):
        """Echo the given object

        Can be used for simple tests.
        For example to test if certain values can be send to
        and received from the server.

        :param echo: the object to echo
        :returns: the given echo
        """
        return echo


class ChainedProvider(ProviderBase):
    """Provider that can chain multiple other providers together

    This is the provider used by the command line client to combine
    :class:`reddel_server.RedBaronProvider` with third party providers.
    :meth:`reddel_server.ChainedProvider.add_provider` is a simple function
    to provide a simple plug-in system.

    Example:

    .. testcode::

        import reddel_server

        class FooProvider(reddel_server.ProviderBase):
            def foo(self): pass

        class BarProvider(reddel_server.ProviderBase):
            def bar(self): pass

        server = reddel_server.Server()
        providers = [FooProvider(server), BarProvider(server)]
        p = reddel_server.ChainedProvider(server, providers)
        methods = p.list_methods()
        assert "foo" in methods
        assert "bar" in methods

    Methods are cached in :data:`reddel_server.ChainedProvider._cached_methods`.
    :meth:`reddel_server.ChainedProvider._get_methods` will use the cached value unless it's ``None``.
    :meth:`reddel_server.ChainedProvider.add_provider` will reset the cache.
    """
    def __init__(self, server, providers=None):
        """Initialize a provider which acts as a combination of the given
        providers.

        :param server: the server that is using the provider
        :type server: :class:`reddel_server.Server`
        :param providers: list of providers.
                          A provider's methods at the front of the list will take precedence.
        :type providers: :class:`list` of :class:`ProviderBase`
        """
        super(ChainedProvider, self).__init__(server)
        self._providers = providers or []
        self._cached_methods = None

    def _get_method(self, name):
        """Return a method from any of the providers

        :param name: of the method
        :type name: :class:`str`
        :returns: the method
        """
        return self._get_methods()[name]

    def add_provider(self, dotted_path):
        """Add a new provider

        :param dotted_path: dotted path to provider class.
                            E.g. ``mypkg.mymod.MyProvider``.
        :type dotted_path: :class:`str`

        This provides a simple plug-in system.
        A client (e.g. Emacs) can call ``add_provider``
        with a dotted path to a class within a module.
        The module has to be importable. So make sure you installed it or
        added the directory to the ``PYTHONPATH``.

        .. testcode::

            import reddel_server
            cp = reddel_server.ChainedProvider(reddel_server.Server())
            cp.add_provider('reddel_server.RedBaronProvider')

        If the given provider has methods with the same name as the existing ones,
        it's methods will take precedence.

        This will invalidate the cached methods on this instance and also on the server.
        """
        providercls = utils.get_attr_from_dotted_path(dotted_path)
        self._providers.insert(0, providercls(self.server))
        self._cached_methods = None
        self.server._set_funcs()  # to reset the cache of the server

    def _get_methods(self, src=None):
        """Return all methods provided.

        :param source: if ``src`` return only compatible methods
        :type source: :class:`str`
        :returns: dict method names and methods
        """
        if self._cached_methods is None:
            self._cached_methods = {}
            for p in reversed(self._providers):
                self._cached_methods.update(p._get_methods(src=src))
            self._cached_methods.update(super(ChainedProvider, self)._get_methods(src=src))
        return self._cached_methods


class RedBaronProvider(ProviderBase):
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
    def get_parents(self, red, row, column):
        """Return a list of parents (scopes) relative to the given position

        .. table::

            +--------------+----------------+---------------+------------------+
            | source input | outputs source | allowed types | only single node |
            +==============+================+===============+==================+
            | Yes          | No             | Any           | No               |
            +--------------+----------------+---------------+------------------+

        :param red: the red baron source
        :type red: :class:`redbaron.RedBaron`
        :param row: line number of the position to query (starting with 1)
        :type row: :class:`int`
        :param column: column number (starting with 1)
        :type column: :class:`int`
        :returns: a list of parents starting with the element at position first.
        :rtype: :class:`list` of the parents.
                A parent is represented by a :class:`tuple` of the
                type, top-left, bottom-right position.
                Each position is a :class:`tuple` of two :class:`int` for
                row and column number.

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
            >>> pprint.pprint(p.get_parents(src, 7, 32))
            [('string', (7, 31), (7, 36)),
             ('call_argument', (7, 26), (7, 36)),
             ('call', (7, 25), (7, 37)),
             ('call_argument', (7, 18), (7, 37)),
             ('call', (7, 17), (7, 38)),
             ('atomtrailers', (7, 13), (7, 38)),
             ('except', (6, 9), (8, 0)),
             ('try', (4, 9), (8, 0)),
             ('ifelseblock', (3, 5), (8, 0)),
             ('def', (1, 1), (8, 0))]

        """
        parents = []
        current = red.find_by_position((row, column))
        while current != red:
            region = current.absolute_bounding_box
            nodetype = current.type
            tl = region.top_left.to_tuple()
            br = region.bottom_right.to_tuple()
            current = current.parent
            # if previous bounding box is the same take the parent higher in the hierachy
            if parents and parents[-1][1] == tl and parents[-1][2] == br:
                parents.pop()
            parents.append((nodetype, tl, br))
        return parents
