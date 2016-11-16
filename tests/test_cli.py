import pytest
from click.testing import CliRunner

import reddel_server
from reddel_server import cli


@pytest.fixture(scope='function')
def mock_server(mocker):
    mocker.patch.object(reddel_server.Server, 'serve_forever', autospec=True)
    mocker.spy(reddel_server.Server, 'print_port')


def test_main(mock_server):
    """Some basic checks to see that cli executes."""
    runner = CliRunner()
    result = runner.invoke(cli.main, [])
    assert reddel_server.Server.print_port.call_count == 1
    assert reddel_server.Server.serve_forever.call_count == 1
    assert result.exit_code == 0
