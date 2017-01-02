import pytest
import redbaron

import reddel_server
from reddel_server import provider


class SpamProvider(reddel_server.ProviderBase):
    def spam(self):
        return "spam"

    def foo(self):
        return "spammy foo"


def test_ProviderBase_repr(server):
    pb = reddel_server.ProviderBase(server)
    assert repr(pb) == "ProviderBase({0!r})".format(server)


def test_ProviderBase_str(server):
    pb = reddel_server.ProviderBase(server)
    assert str(pb) == "<ProviderBase at {0}>".format(hex(id(pb)))


def test_ProviderBase_list_methods(server):
    """Test all expected methods are listed"""
    pb = reddel_server.ProviderBase(server)
    expected = ["echo", "help", "list_methods", "reddel_version"]
    assert pb.list_methods() == expected


def test_ProviderBase_list_methods_functions(server):
    """Test that functions are returned as well"""
    pb = reddel_server.ProviderBase(server)
    def foo():
        pass  # pragma: nocover
    pb.func = foo

    assert "func" in pb.list_methods()


def test_ProviderBase_list_methods_lambda(server):
    """Test that lambdas are returned as well"""
    pb = reddel_server.ProviderBase(server)
    pb.lambdafunc = lambda: True  # pragma: nocover

    assert "lambdafunc" in pb.list_methods()

@pytest.fixture(scope='module')
def pbwithvalidator(server):
    """A provider base with foo as test function.

    The validator on foo only marks the source ``valid``
    as valid.
    """
    pb = reddel_server.ProviderBase(server)
    def foo():
        pass # pragma: nocover

    def validator(src):
        if "valid" != src.dumps():
            raise reddel_server.ValidationException

    foo.validators = [validator]
    pb.func = foo
    return pb


def test_ProviderBase_list_methods_validator_success(pbwithvalidator):
    """Test that methods that pass validation are not filtered out."""
    assert "func" in pbwithvalidator.list_methods(src="valid")


def test_ProviderBase_list_methods_validator_invalid(pbwithvalidator):
    """Test that methods are filtered out."""
    assert "func" not in pbwithvalidator.list_methods(src="invalid")


def test_ProviderBase_get_method(server):
    """Test _get_method returns the methods."""
    pb = reddel_server.ProviderBase(server)
    methods = pb.list_methods()
    expected = [getattr(pb, m) for m in pb.list_methods()]
    assert [pb._get_method(m) for m in pb.list_methods()]


def test_Providerbase_help(server):
    """Test that help returns the docstring."""
    pb = reddel_server.ProviderBase(server)
    def foo():
        """Test docstring"""
        pass  # pragma: nocover
    pb.foo = foo

    assert pb.help("foo") == "Test docstring"


def test_ProviderBase_reddel_version(server):
    assert reddel_server.ProviderBase(server).reddel_version() == reddel_server.__version__


def test_ProviderBase_echo(server):
    expected = "test this"
    assert reddel_server.ProviderBase(server).echo(expected) is expected


@pytest.fixture(scope='function')
def foobarprovider(server, fooprovider, barprovider):
    return reddel_server.ChainedProvider(server, [fooprovider, barprovider])


def test_ChainedProvider_get_methods(foobarprovider, fooprovider, barprovider):
    """Test that all methods from all providers are present."""
    methdict = foobarprovider._get_methods()
    expected = {"add_provider": foobarprovider.add_provider,
                "echo": foobarprovider.echo,
                "help": foobarprovider.help,
                "list_methods": foobarprovider.list_methods,
                "foo": fooprovider.foo,
                "bar": barprovider.bar,
                "reddel_version": foobarprovider.reddel_version
    }
    assert methdict == expected


def test_ChainedProvider_get_methods_cached(foobarprovider):
    """Test that methods get cached."""
    methdict = foobarprovider._get_methods()
    assert methdict is foobarprovider._get_methods()


def test_ChainedProvider_get_methods_cached_src(foobarprovider):
    """Test that methods do not get cached when calling with a source."""
    methdict = foobarprovider._get_methods('1+1')
    assert methdict is not foobarprovider._get_methods('1+1')


def test_ChainedProvider_get_methods_cached_src_fresh(foobarprovider):
    """Test that methods do not get cached when calling with a source
    when calling without source first."""
    methdict = foobarprovider._get_methods()
    assert methdict is not foobarprovider._get_methods('1+1')


@pytest.mark.parametrize("method", ["foo", "bar"])
def test_ChainedProvider_get_method(foobarprovider, method):
    """Test that name resolution works"""
    assert foobarprovider._get_method(method)() == method


def test_ChainedProvider_add_provider(foobarprovider):
    """Test that additional methods are added."""
    foobarprovider.add_provider("test_provider.SpamProvider")
    assert foobarprovider._get_method("spam")() == "spam"


def test_ChainedProvider_add_provider_empty(server):
    """Test that additional methods are added."""
    cp = reddel_server.ChainedProvider(server)
    cp.add_provider("test_provider.SpamProvider")
    assert cp._get_method("spam")() == "spam"


def test_ChainedProvider_add_provider_override(foobarprovider):
    """Test that adding a provider can override existing methods."""
    foobarprovider.add_provider("test_provider.SpamProvider")
    assert foobarprovider._get_method("foo")() == "spammy foo", \
        "Adding a provider should override existing clashing methods."


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
    result = provider.get_attr_from_dotted_path('test.this.path.MyClass')
    mockedimport.assert_called_once_with('test.this.path')
    assert result is mockedimport('test.this.path').MyClass


def test_get_attr_from_dotted_path_raise_import(mocker):
    mockedimport = mockimport(mocker, ImportError("No module named 'UNKNOWNMODULE'"))
    with pytest.raises(ImportError):
        provider.get_attr_from_dotted_path('UNKNOWNMODULE.stuff')
    mockedimport.assert_called_once_with('UNKNOWNMODULE')


def test_get_attr_from_dotted_path_raise_value(mocker):
    with pytest.raises(ValueError):
        provider.get_attr_from_dotted_path('UNKNOWNMODULE')


def test_get_attr_from_dotted_path_raise_attr(mocker):
    mockedimport = mockimport(mocker)
    with pytest.raises(AttributeError):
        provider.get_attr_from_dotted_path('test.this.path.NotExistentAttr')
    mockedimport.assert_called_once_with('test.this.path')
