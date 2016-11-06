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
    """
    def __init__(self, server_address=('localhost', 0), RequestHandlerClass=epc.handler.EPCHandler):
        """Init server with the given handler.

        :param server_address: url/ip and port
        :type server_address: tuple
        :param RequestHandlerClass: the handler class to use
        :type RequestHandlerClass: :class:`epc.handler.EPCHandler`
        :raises: None
        """
        super(Server, self).__init__(server_address, RequestHandlerClass, log_traceback=True)
        self.register_function(self.set_logging_level)

    def set_logging_level(self, level):
        """Set logging level

        :param level: either "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL" or integer
        :type level: :class:`str`|:class:`int`
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
