"""
Module that contains the command line app.
"""
import click
import click_log

import reddel_server
from reddel_server import utils


@click.command()
@click.option('--address', type=str, default='localhost', help="address to bind the server to")
@click.option('--port', type=int, default=0, help="address to bind the server to")
@click.option('--provider', '-p', type=str, multiple=True, help="dotted path to a provider class")
@click_log.simple_verbosity_option()
def main(address, port, provider):
    server = reddel_server.Server((address, port))
    provider = provider + ('reddel_server.RedBaronProvider', 'reddel_server.Provider')
    providers = []
    for p in provider:
        providercls = utils.get_attr_from_dotted_path(p)
        providers.append(providercls(server))
    chainedprovider = reddel_server.ChainedProvider(server, providers=providers)
    server.register_instance(chainedprovider)
    click_log.init(server.logger)
    server.print_port()
    server.serve_forever()
    server.logger.info("server shutdown")
