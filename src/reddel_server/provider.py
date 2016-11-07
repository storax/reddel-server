"""Provide functionality to reddel"""
from __future__ import absolute_import

import functools
import types

import redbaron

from . import exceptions
from . import utils
from . import validators

__all__ = ['ProviderBase', 'Provider', 'ChainedProvider', 'RedBaronProvider',
           'redwraps', 'red_src', 'red_type', 'red_validate']


_RED_FUNC_ATTRS = ['red', 'validators']


def redwraps(towrap):
    """Use this when creating decorators instead of :func:`functools.wraps`

    Makes sure to transfer special reddel attributes to the wrapped function.
    On top of that uses :func:`functools.wraps`.

    :param towrap: the function to wrap
    :type towrap: function
    :returns: the decorator
    :rtype: function
    """
    def redwraps_dec(func):
        wrapped = functools.wraps(towrap)(func)
        for attr in _RED_FUNC_ATTRS:
            val = getattr(towrap, attr, None)
            setattr(wrapped, attr, val)
        return wrapped
    return redwraps_dec


def red_src(dump=True):
    """Create decorator that converts the first arg into a red baron src

    :param dump: if True, dump the return value from the wrapped function.
                 Expectes the return type to be a :class:`redbaron.RedBaron` object.
    :type dump: :class:`boolean`
    :returns: the decorator
    :rtype: function
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
                v(red)
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
    :rtype: functions
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

    def __repr__(self):
        return "{classname}()".format(classname=self.__class__.__name__)

    @property
    def server(self):
        return self._server

    @property
    def log(self):
        return self._server.logger

    def _get_methods(self, src=None):
        """Return a dictionary of all methods provided.

        :param source: if src return only compatible methods
        :type source: :class:`str`
        :returns: dict method names and methods
        """
        if src:
            red = redbaron.RedBaron(src)
        d = {}
        for attrname in dir(self):
            attr = getattr(self, attrname)
            if not attrname.startswith('_') and isinstance(attr, types.MethodType):
                if src and hasattr(attr, 'validators'):
                    for v in (attr.validators or []):
                        try:
                            v(red)
                        except exceptions.ValidationError:
                            break
                    else:
                        d[attrname] = attr
                else:
                    d[attrname] = attr
        return d

    def list_methods(self, src=None):
        """Return a list of methods

        :param source: if src return only compatible methods
        :type source: :class:`str`
        :returns: list of :class:`str`
        """
        return list(self._get_methods(src=src).keys())

    def _get_method(self, name):
        return getattr(self, name)

    def help(self, name):
        """Return the docstring of the method

        :param name: the name of the method.
        :type name: :class:`str`
        """
        method = getattr(self, name)
        return method.__doc__


class Provider(ProviderBase):
    """Provide basic functionality"""

    def reddel_version(self):
        """Return the reddel version"""
        import reddel_server
        return reddel_server.__version__

    def version(self):
        """Return the provider version"""
        return self.reddel_version()

    def echo(self, echo):
        """Echo the given string

        :param echo: the string to echo
        :type echo: :class:`str`
        :returns: echo
        :rtype: :class:`str`
        """
        return echo


class ChainedProvider(ProviderBase):
    """Provider that can chain multiple other providers together"""
    def __init__(self, server, providers=()):
        """Init provider

        :param server: the server that is using the provider
        :type server: :class:`reddel_server.Server`
        :param providers: list of providers
        :type providers: :class:`list` of :class:`ProviderBase`
        """
        super(ChainedProvider, self).__init__(server)
        self._providers = providers

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
        self._providers = self._providers.insert(0, providercls(self.server))
        self.server.provider = self

    def _get_methods(self, src=None):
        """Return all methods provided.

        :param source: if src return only compatible methods
        :type source: :class:`str`
        :returns: dict method names and methods
        """
        d = super(ChainedProvider, self)._get_methods(src=src)
        for p in reversed(self._providers):
            d.update(p._get_methods(src=src))
        return d


class RedBaronProvider(ProviderBase):
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
        """Return a list of args."""
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
