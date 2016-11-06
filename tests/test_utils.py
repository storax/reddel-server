"""Tests for the utils module"""
import pytest

from reddel_server import utils


def test_get_attr_from_dotted_path(mocker):
    """Test the function call importlib correctly"""
    class MyClass:
        pass

    importmock = mocker.Mock()
    modmock = mocker.Mock()
    modmock.MyClass = MyClass
    importmock.return_value = modmock

    mockedimport = mocker.patch("importlib.import_module", importmock)
    result = utils.get_attr_from_dotted_path("test.this.path.MyClass")
    assert result is MyClass
    mockedimport.assert_called_once_with('test.this.path')
