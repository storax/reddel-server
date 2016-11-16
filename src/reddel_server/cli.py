"""
Module that contains the command line app.
"""
from __future__ import absolute_import

import logging

import click
import click_log

import reddel_server

from . import exceptions
from . import utils

logger = logging.getLogger("reddel")


@click.command()
@click.option('--address', type=str, default='localhost', help="address to bind the server to")
@click.option('--port', type=int, default=0, help="address to bind the server to")
@click.option('--provider', '-p', type=str, multiple=True, help="dotted path to a provider class")
@click_log.simple_verbosity_option()
@click.option('--debug', is_flag=True, help="Show tracebacks when erroring.")
@click_log.init("reddel")
def main(address, port, provider, debug):
    epclogger = logging.getLogger("epc")
    click_log.basic_config(epclogger)
    epclogger.setLevel(logger.level)

    try:
        server = reddel_server.Server((address, port))
        server.print_port()

        provider = provider + ("reddel_server.RedBaronProvider", )
        logger.info("setting the following providers %s", provider)

        providers = []
        for p in provider:
            providercls = utils.get_attr_from_dotted_path(p)
            providers.append(providercls(server))
        logger.debug("all providers initialized")

        logger.debug("creating chained provider")
        chainedprovider = reddel_server.ChainedProvider(server, providers=providers)
        server.set_provider(chainedprovider)
        logger.debug("serve forever")
        server.serve_forever()
    except exceptions.RedBaseException as err:
        if debug:
            logger.exception("%s", err)
        else:
            logger.error('%s', err)
        raise SystemExit(1)
    server.logger.info("server shutdown")
