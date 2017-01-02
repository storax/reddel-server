import pytest

import reddel_server


@pytest.fixture(scope="module")
def server():
    server = reddel_server.Server(('localhost', 0))
    yield server
    server.server_close()


@pytest.fixture(scope='function')
def fooprovider(server):
    class FooProvider(reddel_server.ProviderBase):
        def foo(self):
            return "foo"
    return FooProvider(server)


@pytest.fixture(scope='function')
def barprovider(server):
    class BarProvider(reddel_server.ProviderBase):
        def bar(self):
            return "bar"
    return BarProvider(server)
