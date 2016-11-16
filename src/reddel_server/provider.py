"""Provide functionality to reddel"""
from __future__ import absolute_import

import functools
import types

import redbaron

from . import exceptions
from . import utils
from . import validators

__all__ = ['ProviderBase', 'ChainedProvider', 'RedBaronProvider',
           'redwraps', 'red_src', 'red_type', 'red_validate']


_RED_FUNC_ATTRS = ['red', 'validators']


def redwraps(towrap):
    """Use this when creating decorators instead of :func:`functools.wraps`

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

    :param towrap: the function to wrap
    :type towrap: :data:`types.FunctionType`
    :returns: the decorator
    :rtype: :data:`types.FunctionType`
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

    :param dump: if True, dump the return value from the wrapped function.
                 Expects the return type to be a :class:`redbaron.RedBaron` object.
    :type dump: :class:`bool`
    :returns: the decorator
    :rtype: :data:`types.FunctionType`
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
    :type validators: :class:`validators.ValidatorInterface`
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

    :param identifiers: red baron node identifiers
    :type identifiers: list of :class:`str`
    :param single: expect a single node in the initial node list. Pass on the first node.
    :type single: :class:`bool`
    :returns: the decorator
    :rtype: :data:`types.FunctionType`
    """
    return red_validate([validators.BaronTypeValidator(identifiers, single=single)])


class ProviderBase(object):
    """Provide minimal functionality"""

    def __init__(self, server):
        """Init provider

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

    @property
    def log(self):
        return self._server.logger

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

        To get more information for each method use :meth:`ProviderBase.help`.

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

        :param name: the name of the method.
        :type name: :class:`str`
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

    Methods are cached in :data:`ChainedProvider._cached_methods`.
    :meth:`ChainedProvider._get_methods` will use the cached value unless it's ``None``.
    :meth:`Chained.Provider.add_provider` will reset the cache.
    """
    def __init__(self, server, providers=()):
        """Init provider

        :param server: the server that is using the provider
        :type server: :class:`reddel_server.Server`
        :param providers: list of providers
        :type providers: :class:`list` of :class:`ProviderBase`
        """
        super(ChainedProvider, self).__init__(server)
        self._providers = providers
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

        :param dotted_path: dotted path to provider class
        :type dotted_path: :class:`str`
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
    """Provider for transforming source code via redbaron."""

    @red_src(dump=False)
    def analyze(self, red, deep=2, with_formatting=False):
        return "\n".join(red.__help__(deep=deep, with_formatting=False))

    @red_src()
    @red_type(["def"])
    def rename_arg(self, red, oldname, newname):
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
        """Return a list of args and their default value (if any) as source code."""
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
        red.arguments.insert(index, arg)
        return red

    @red_src()
    def get_current(self, red, row, column):
        return red.find_by_position((row, column))

    @red_src(dump=False)
    def get_parents(self, red, row, column):
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
