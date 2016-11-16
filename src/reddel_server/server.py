"""
Contains the main EPC server class.
"""
import logging

import epc.handler
import epc.server
import six


__all__ = ['Server']


class Server(epc.server.EPCServer):
    """EPCServer that provides basic functionality.

    If a provider can change it's mehtods dynamically, make sure to reassign it to :data:`Server.provider`
    to reset the method cache.
    """
    allow_reuse_address = True

    def __init__(self, server_address=('localhost', 0), RequestHandlerClass=epc.handler.EPCHandler):
        """Init server with the given handler.

        :param server_address: url/ip and port
        :type server_address: tuple
        :param RequestHandlerClass: the handler class to use
        :type RequestHandlerClass: :class:`epc.handler.EPCHandler`
        :raises: None
        """
        epc.server.EPCServer.__init__(self, server_address, RequestHandlerClass=RequestHandlerClass, log_traceback=True)
        self._provider = None
        self._set_funcs()

    def _set_funcs(self):
        """Register all functions from all providers."""
        self.funcs = {}
        self.register_function(self.set_logging_level)
        if self._provider:
            for name, f in self._provider._get_methods().items():
                self.register_function(f, name=name)

    def set_logging_level(self, level):
        """Set logging level

        :param level: either ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, ``CRITICAL`` or integer
        :type level: :class:`str` | :class:`int`
        :returns: None
        :raises: None
        """
        if isinstance(level, six.string_types):
            mapping = {"DEBUG": logging.DEBUG,
                       "INFO": logging.INFO,
                       "WARNING": logging.WARNING,
                       "ERROR": logging.ERROR,
                       "CRITICAL": logging.CRITICAL}
            try:
                level = mapping[level]
            except KeyError:
                raise ValueError("Invalid logging level %s" % level)
        self.logger.setLevel(level)

    def get_provider(self):
        """The :class:`reddel_server.Provider` instance that provides methods."""
        return self._provider

    def set_provider(self, provider):
        self._provider = provider
        self._set_funcs()
