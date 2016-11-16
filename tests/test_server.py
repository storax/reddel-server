import logging

import pytest

import reddel_server


@pytest.fixture(scope="function")
def server():
    server = reddel_server.Server(('localhost', 0))
    yield server
    server.server_close()


def test_Server_init_funcs(server):
    """Test the initial registered functions."""
    assert server.funcs == {'set_logging_level': server.set_logging_level}


def test_Server_set_provider(server, fooprovider):
    """Test the provider property"""
    server.set_provider(fooprovider)
    assert server.get_provider() is fooprovider


def test_Server_set_provider_funcs(server, fooprovider):
    """Test that functions are registerd when provider is set."""
    server = reddel_server.Server(('localhost', 0))
    server.server_close()
    server.set_provider(fooprovider)
    expected = {'set_logging_level': server.set_logging_level}
    expected.update(fooprovider._get_methods())
    assert server.funcs == expected

@pytest.mark.parametrize("level,expected", [("DEBUG", logging.DEBUG),
                                            ("INFO", logging.INFO),
                                            ("WARNING", logging.WARNING),
                                            ("ERROR", logging.ERROR),
                                            ("CRITICAL", logging.CRITICAL),
                                            (24, 24)])
def test_Server_set_logging_level(server, level, expected):
    """Test setting logging level"""
    server.set_logging_level(level)
    assert server.logger.level == expected


def test_Server_set_logging_level_raise(server):
    """Test setting logging level with an invalid string value raises a ValueError."""
    with pytest.raises(ValueError):
        server.set_logging_level("Invalid")
