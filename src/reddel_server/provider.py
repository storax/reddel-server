"""Provide functionality to reddel"""
import functools
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

    def list_methods(self):
        """Return a list of methods"""
        l = []
        for attr in dir(self):
            if not attr.startswith('_') and callable(getattr(self, attr)):
                l.append(attr)
        self.log.error('%s', l)
        return l

    def _get_method(self, name):
        return getattr(self, name)

    def help(self, name):
        """Return the docstring of the method

        :param name: the name of the method.
        :type name: :class:`str`

        asdfasdf
        """
        method = getattr(self, name)
        self.log.error(method.__doc__)
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
        if not hasattr(self, name):
            for provider in self._providers:
                method = getattr(provider, name, None)
                if callable(method):
                    return method
        return getattr(self, name)

    def add_provider(self, dotted_path):
        """Add a new provider

        :param dotted_path: dotted path to provider class
        :type dotted_path: :class:`str`
        """
        providercls = utils.get_attr_from_dotted_path(dotted_path)
        self._providers = self._providers.insert(0, providercls(self.server))

    def list_methods(self):
        """Return a list of methods"""
        l = set([])
        for p in self._providers:
            l.update(p.list_methods())
        l.update(super(ChainedProvider, self).list_methods())
        return list(l)


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
    @red_src()
    @red_type("def")
    def add_arg(self, red, index, arg):
        red.arguments.insert(index, arg)
        return red
