"""Provide functionality to reddel"""
import functools
import types

import redbaron

from reddel_server import utils

__all__ = ["ProviderBase", "Provider", "ChainedProvider", "RedBaronProvider"]


class ProviderBase(object):
    """Provide minimal functionality"""

    def __init__(self, server):
        """Init provider

        :param server: the server that is using the provider
        :type server: :class:`reddel_server.Server`
        """
        super(ProviderBase, self).__init__()
        self._server = server

    @property
    def server(self):
        return self._server

    @property
    def log(self):
        return self._server.logger

    def _get_methods(self):
        """Return a dictionary of all methods provided."""
        d = {}
        for attrname in dir(self):
            attr = getattr(self, attrname)
            if not attrname.startswith('_') and isinstance(attr, types.MethodType):
                d[attrname] = attr
        return d

    def list_methods(self):
        """Return a list of methods"""
        return self._get_methods().keys()

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

    def _get_methods(self):
        """Return all methods provided."""
        d = super(ChainedProvider, self)._get_methods()
        for p in reversed(self._providers):
            d.update(p._get_methods())
        return d


def red_src(dump=True):
    """Create decorator that converts the first arg into a red baron src

    :param dump: if True, dump the return value from the wrapped function.
                 Expectes the return type to be a :class:`redbaron.RedBaron` object.
    :type dump: :class:`boolean`
    """
    def red_src_dec(func):
        @functools.wraps(func)
        def wrapped(self, src, *args, **kwargs):
            red = redbaron.RedBaron(src)
            retval = func(self, red, *args, **kwargs)
            if dump and retval:
                retval = retval.dumps()
            return retval
        return wrapped
    return red_src_dec


def red_type(identifier, single=True):
    """Create decorator that checks if the root is identified by identifier

    :param identifier: red baron node identifiers
    :type identifier: :class:`str`
    :param single: expect a single node in the initial node list. Pass on the first node.
    :type single: :class:`bool`
    """
    def red_type_dec(func):
        @functools.wraps(func)
        def wrapped(self, red, *args, **kwargs):
            for node in red:
                identifiers = node.generate_identifiers()
                if identifier not in identifiers:
                    raise ValueError("Expected identifier %s but got %s" % (identifier, identifiers))
            if single:
                count = len(red)
                if count != 1:
                    raise ValueError("Expected a single node but got %s" % count)
                red = red[0]
            return func(self, red, *args, **kwargs)
        return wrapped
    return red_type_dec


class RedBaronProvider(ProviderBase):
    @red_src(dump=False)
    def analyze(self, red, deep=2, with_formatting=False):
        return "\n".join(red.__help__(deep=deep, with_formatting=False))

    @red_src()
    @red_type("def")
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
    @red_type("def")
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
    @red_type("def")
    def add_arg(self, red, index, arg):
        red.arguments.insert(index, arg)
        return red
