"""Tests for the utils module"""
import pytest

import reddel_server
from reddel_server import utils


def mockimport(mocker, sideeffect=None):
    class MyClass(object):
        pass

    importmock = mocker.Mock()
    modmock = mocker.Mock(object)
    modmock.MyClass = MyClass
    importmock.return_value = modmock
    if sideeffect:
        importmock.side_effect = sideeffect

    return mocker.patch("importlib.import_module", importmock)


def test_get_attr_from_dotted_path(mocker):
    """Test the function call importlib correctly"""
    mockedimport = mockimport(mocker)
    result = utils.get_attr_from_dotted_path("test.this.path.MyClass")
    mockedimport.assert_called_once_with('test.this.path')
    assert result is mockedimport("test.this.path").MyClass


def test_get_attr_from_dotted_path_raise_import(mocker):
    mockedimport = mockimport(mocker, ImportError("No module named 'UNKNOWNMODULE'"))
    with pytest.raises(reddel_server.RedImportError):
        utils.get_attr_from_dotted_path("UNKNOWNMODULE.stuff")
    mockedimport.assert_called_once_with("UNKNOWNMODULE")


def test_get_attr_from_dotted_path_raise_value(mocker):
    with pytest.raises(reddel_server.RedValueError):
        utils.get_attr_from_dotted_path("UNKNOWNMODULE")


def test_get_attr_from_dotted_path_raise_attr(mocker):
    mockedimport = mockimport(mocker)
    with pytest.raises(reddel_server.RedAttributeError):
        utils.get_attr_from_dotted_path("test.this.path.NotExistentAttr")
    mockedimport.assert_called_once_with('test.this.path')
