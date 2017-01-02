"""
Module that contains the command line app.

The app has the following structure:
:func:`main` is the main entry point. Logging is initialized first.
Then the server is created and the port is printed so that the epc client can connect to it.
Afterwards the logging level is set to the user specified level. If we use debug logging when the
server starts, connecting with the client will fail.

After the server has been created, the providers are loaded and combined
with a :class:`reddel_server.ChainedProvider`.
Afterwards the server starts serving.
"""
from __future__ import absolute_import

import contextlib
import logging

import click
import click_log

import reddel_server
from . import provider

logger = logging.getLogger(__name__)


# If you change any arguments, make sure to update the readme documentation.
@click.command()
@click.option('--address', type=str, default='localhost', help="address to bind the server to")
@click.option('--port', type=int, default=0, help="address to bind the server to")
@click.option('--provider', '-p', type=str, multiple=True, help="dotted path to a provider class")
@click_log.simple_verbosity_option()
@click.option('--debug', is_flag=True, help="Show tracebacks when erroring.")
@click_log.init("reddel_server")
def main(address, port, provider, debug):
    # Silence the loggers before we print the port
    # We wouldn't be able to connect from emacs via epc otherwise
    epclogger = logging.getLogger("epc")
    click_log.basic_config(epclogger)
    epclogger.setLevel(logger.level)

    with logging_level([logger, epclogger], logging.ERROR):
        server = reddel_server.Server((address, port))
        server.print_port()

    provider = provider + ("reddel_server.RedBaronProvider", )
    logger.info("setting the following providers %s", provider)

    providers = load_providers(provider, server, debug)
    logger.debug("all providers initialized: %s", providers)

    logger.debug("creating chained provider")
    chainedprovider = reddel_server.ChainedProvider(server, providers=providers)
    server.set_provider(chainedprovider)

    logger.debug("serve forever")
    server.serve_forever()
    server.logger.info("server shutdown")


def load_providers(providers, server, debug=False):
    """Take a list of dotted paths and return the imported and initialized providers.

    :param providers: the dotted paths to import
    :type providers: :class:`list` of :class:`str`
    :param server: the server for the providers to initialize
    :type server: :class:`reddel_server.Server`
    :param debug: If Ture, log the exception else just log an error.
    :type debug: :class:`bool`
    :returns: a list of provider instances
    :rtype: :class:`list` of :class:`reddel_server.ProviderBase`
    """
    loaded = []
    for p in providers:
        try:
            providercls = provider.get_attr_from_dotted_path(p)
        except (ImportError, ValueError, AttributeError) as err:
            msg = "Unable to load provider %s. Provider will not be loaded. %s"
            if debug:
                logger.exception(msg, p, err)
            else:
                logger.error(msg, p, err)
        else:
            loaded.append(providercls(server))
    return loaded


@contextlib.contextmanager
def logging_level(loggers, level):
    """Set the level of the given loggers to the given level

    This will restore the logging level afterwards and is useful
    for temporarly chaning the logging level.

    :param loggers: a list of loggers
    :type loggers: :class:`list`
    :param level: the logging level to set
    :type level: :class:`str` | :class:`int`
    """
    levels = {logger: logger.level for logger in loggers}
    for logger in loggers:
        logger.setLevel(level)
    try:
        yield
    finally:
        for logger, lvl in levels.items():
            logger.setLevel(lvl)
