"""Provider expose functionality to a reddel server"""
from __future__ import absolute_import

import importlib
import logging
import types

import redbaron

from . import validators

__all__ = ['ProviderBase', 'ChainedProvider']

logger = logging.getLogger(__name__)


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
            def _private(self):
                print("I'm private")

    .. testcode::

        server = reddel_server.Server()
        provider = MyProvider(server)
        server.set_provider(provider)
        methods = provider.list_methods()
        assert "exposed" in methods
        assert "_private" not in methods

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
                        except validators.ValidationException:
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
        :func:`reddel_server.red_validate` decorators.

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
    :meth:`reddel_server.ChainedProvider.add_provider` is a function
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
    Keep that in mind when building dynamic providers because the cache might become invalid.
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
        providercls = get_attr_from_dotted_path(dotted_path)
        self._providers.insert(0, providercls(self.server))
        self._cached_methods = None
        self.server._set_funcs()  # to reset the cache of the server

    def _get_methods(self, src=None):
        """Return all methods provided.

        :param source: if ``src`` return only compatible methods
        :type source: :class:`str`
        :returns: dict method names and methods
        """
        methods = {}
        if src or self._cached_methods is None:
            for p in reversed(self._providers):
                methods.update(p._get_methods(src=src))
            methods.update(super(ChainedProvider, self)._get_methods(src=src))
            if self._cached_methods is None:
                self._cached_methods = methods
        else:
            methods = self._cached_methods
        return methods


def get_attr_from_dotted_path(path):
    """Return the imported object from the given path.

    :param path: a dotted path where the last segement is the attribute of the module to return.
                 E.g. ``mypkg.mymod.MyClass``.
    :type path: str
    :returns: the object specified by the path
    :raises: :class:`ImportError`, :class:`AttributeError`, :class:`ValueError`
    """
    logger.debug("importing %s", path)
    if '.' not in path:
        msg = "Expected a dotted path (e.g. 'mypkg.mymod.MyClass') but got {0!r}".format(path)
        raise ValueError(msg)

    providermodname, providerclsname = path.rsplit('.', 1)
    providermod = importlib.import_module(providermodname)

    return getattr(providermod, providerclsname)
