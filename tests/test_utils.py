"""Tests for the utils module"""
import logging

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

    return mocker.patch('importlib.import_module', importmock)


def test_get_attr_from_dotted_path(mocker):
    """Test the function call importlib correctly"""
    mockedimport = mockimport(mocker)
    result = utils.get_attr_from_dotted_path('test.this.path.MyClass')
    mockedimport.assert_called_once_with('test.this.path')
    assert result is mockedimport('test.this.path').MyClass


def test_get_attr_from_dotted_path_raise_import(mocker):
    mockedimport = mockimport(mocker, ImportError("No module named 'UNKNOWNMODULE'"))
    with pytest.raises(ImportError):
        utils.get_attr_from_dotted_path('UNKNOWNMODULE.stuff')
    mockedimport.assert_called_once_with('UNKNOWNMODULE')


def test_get_attr_from_dotted_path_raise_value(mocker):
    with pytest.raises(ValueError):
        utils.get_attr_from_dotted_path('UNKNOWNMODULE')


def test_get_attr_from_dotted_path_raise_attr(mocker):
    mockedimport = mockimport(mocker)
    with pytest.raises(AttributeError):
        utils.get_attr_from_dotted_path('test.this.path.NotExistentAttr')
    mockedimport.assert_called_once_with('test.this.path')


def test_redwraps_add_attrs():
    """Test that attibutes are added."""
    @reddel_server.redwraps(None)
    def foo():
        pass  # pragma: nocover
    assert all([hasattr(foo, attr) for attr in utils._RED_FUNC_ATTRS])


def test_redwraps_attr_value():
    """Test that attibutes values are transferred."""
    def bar():
        pass  # pragma: nocover

    bar.red = 'test'

    @reddel_server.redwraps(bar)
    def foo():
        pass  # pragma: nocover
    assert all([getattr(foo, attr) == getattr(bar, attr, None) for attr in utils._RED_FUNC_ATTRS])
