"""
Contains the main EPC server class.
"""
import logging

import epc.handler
import epc.server
import six

__all__ = ['Server']

logger = logging.getLogger(__name__)


class Server(epc.server.EPCServer):
    """EPCServer that provides basic functionality.

    This is a simple :class:`epc.server.EPCServer` that exposes methods for clients to call remotely.
    You can use the python client to connect or call a method from within emacs.
    The exposed methods are defined by a :class:`Provider <reddel_server.ProviderBase>`.
    Call :meth:`reddel_server.Server.set_provider` to register the functions.

    If a provider can change it's methods dynamically,
    make sure to call :meth:`reddel_server.Server.set_provider` to reset the method cache.
    """
    allow_reuse_address = True

    def __init__(self, server_address=('localhost', 0), RequestHandlerClass=epc.handler.EPCHandler):
        """Initialize server serving the given address with the given handler.

        :param server_address: URL/IP and port
        :type server_address: tuple
        :param RequestHandlerClass: the handler class to use
        :type RequestHandlerClass: :class:`epc.server.EPCHandler`
        :raises: None
        """
        epc.server.EPCServer.__init__(self, server_address, RequestHandlerClass=RequestHandlerClass, log_traceback=True)
        self._provider = None
        self._set_funcs()

    def _set_funcs(self):
        """Register all functions from all providers."""
        logger.debug("resetting registered functions")
        self.funcs = {}
        self.register_function(self.set_logging_level)
        if self._provider:
            for name, f in self._provider._get_methods().items():
                self.register_function(f, name=name)
        logger.debug("registered the following functions: %s", self.funcs.keys())

    def set_logging_level(self, level):
        """Set logging level

        :param level: either ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, ``CRITICAL`` or integer
        :type level: :class:`str` | :class:`int`
        :returns: None
        :raises: None

        Can be called with integer or a string:

        .. doctest::

            >>> import logging
            >>> import reddel_server
            >>> server = reddel_server.Server()
            >>> server.set_logging_level("DEBUG")
            >>> server.set_logging_level(logging.INFO)
            >>> server.set_logging_level(10)
            >>> server.logger.level
            10

        The string has to be one of the builtin logging levels of :mod:`logging`,
        see `Logging Levels <https://docs.python.org/3/library/logging.html#logging-levels>`_.
        """
        if isinstance(level, six.string_types):
            try:
                getattr(logging, level)
            except AttributeError:
                raise ValueError("Invalid logging level %s" % level)
        self.logger.setLevel(level)
        logger.setLevel(level)

    def get_provider(self):
        """The :class:`reddel_server.ProviderBase` instance that provides methods."""
        return self._provider

    def set_provider(self, provider):
        """Set the provider and reset the registered functions.

        :param provider: the provider to set
        :type provider: :class:`reddel_server.ProviderBase`
        """
        logger.debug("setting provider to %s", provider)
        self._provider = provider
        self._set_funcs()
