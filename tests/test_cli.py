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


def test_main_incorrect_provider(mock_server):
    """Check that incorrect provider arugments are only logged."""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["-p" "asdf"])
    assert "Traceback (most recent call last)" not in result.output, (
        "Import errors should only get logged"
        "and the traceback should only be shown if the debug flag is set."
    )
    expected = "Expected a dotted path (e.g. 'mypkg.mymod.MyClass') but got {0!r}".format(u'asdf')
    assert expected in result.output
    assert result.exit_code == 0


def test_main_incorect_provider_debug(mock_server):
    """Check that the traceback is logged with the debug flag."""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["-p" "asdf", "--debug"])
    assert "Traceback (most recent call last)" in result.output
    assert result.exit_code == 0
