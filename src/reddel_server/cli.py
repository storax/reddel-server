"""
Module that contains the command line app.
"""
import click
import click_log

import reddel_server


@click.command()
@click.option('--address', type=str, default='localhost', help="address to bind the server to")
@click.option('--port', type=int, default=0, help="address to bind the server to")
@click.option('--provider', '-p', type=str, multiple=True, help="dotted path to a provider class")
@click_log.simple_verbosity_option()
def main(address, port, provider):
    server = reddel_server.Server((address, port))
    providers = [reddel_server.RedBaronProvider(server)]
    chainedprovider = reddel_server.ChainedProvider(server, providers=providers)
    server.set_provider(chainedprovider)
    click_log.init(server.logger)
    server.print_port()
    server.serve_forever()
    server.logger.info("server shutdown")
