import pytest
import redbaron

import reddel_server
from reddel_server import provider
from reddel_server import utils


TEST_DECORATORS = [
    provider.red_src(dump=False),
    provider.red_src(dump=True),
    provider.red_validate([]),
]


class SpamProvider(reddel_server.ProviderBase):
    def spam(self):
        return "spam"

    def foo(self):
        return "spammy foo"


@pytest.fixture(scope="module")
def server():
    server = reddel_server.Server(('localhost', 0))
    yield server
    server.server_close()


@pytest.mark.parametrize('decorator', TEST_DECORATORS)
def test_decorator_add_attrs(decorator):
    """Test that all attributes are added."""
    @decorator
    def foo(*args, **kwargs):
        pass  # pragma: nocover
    assert all([hasattr(foo, attr) for attr in utils._RED_FUNC_ATTRS])


@pytest.mark.parametrize('decorator', TEST_DECORATORS)
def test_decorator_attr_value(decorator):
    """Test that attributes values are transferred."""
    def foo(*args, **kwargs):
        pass  # pragma: nocover
    foo.red = True
    foo = decorator(foo)
    assert foo.red is True


@pytest.mark.parametrize('decorator,values', zip(
    TEST_DECORATORS,
    [None, None, [None, []]]))
def test_decorator_attr_defaults(decorator, values):
    """Test that attributes keep previous value."""
    @decorator
    def foo(*args, **kwargs):
        pass  # pragma: nocover

    got = [getattr(foo, attr) for attr in utils._RED_FUNC_ATTRS]
    expected = values or [None for _ in utils._RED_FUNC_ATTRS]
    assert  got == expected


def test_red_src_dump_false():
    """Test that red_src decorator converts to RedBaron"""
    @provider.red_src(dump=False)
    def foo(self, src):
        return src

    src = "1+1"
    assert isinstance(foo(None, src), redbaron.RedBaron)


def test_red_src_dump_true():
    """Test that red_src decorator dumps the return value"""
    @provider.red_src(dump=True)
    def foo(self, src):
        assert isinstance(src, redbaron.RedBaron)
        return src

    src = "1+1"
    red = redbaron.RedBaron(src)
    assert src == foo(None, src)


def test_red_validate_attr():
    """Test that the validators attribute is applied."""
    validator = reddel_server.BaronTypeValidator(["def"], single=True)
    @provider.red_validate([validator])
    def foo(*args, **kwargs):
        pass  # pragma: nocover

    assert foo.validators == [validator]


def test_red_validate_invalid():
    """Test that invalid values raise"""
    validator = reddel_server.BaronTypeValidator(["def"])
    @provider.red_validate([validator])
    def foo(self, src):
        pass  # pragma: nocover

    src = redbaron.RedBaron("1+1")
    with pytest.raises(reddel_server.ValidationException):
        foo(None, src)


def test_red_validate_valid():
    """Test that valid values pass"""
    validator = reddel_server.BaronTypeValidator(["def"], single=True)
    @provider.red_validate([validator])
    def foo(self, src):
        pass

    src = redbaron.RedBaron("def foo(): pass")
    foo(None, src)


def test_red_validate_transform():
    """Test that values get transformed"""
    validator = reddel_server.BaronTypeValidator(["def"], single=True)
    src = redbaron.RedBaron("def foo(): pass")

    @provider.red_validate([validator])
    def foo(self, src):
        return src

    transformed = foo(None, src)
    assert src[0] == transformed


def test_ProviderBase_repr(server):
    pb = provider.ProviderBase(server)
    assert repr(pb) == "ProviderBase({0!r})".format(server)


def test_ProviderBase_str(server):
    pb = provider.ProviderBase(server)
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
    """Test that all methods from all providers are present."""
    methdict = foobarprovider._get_methods()
    assert methdict is foobarprovider._get_methods()


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


@pytest.fixture(scope='module')
def redprovider(server):
    return reddel_server.RedBaronProvider(server)


def test_RedBaronProvider_analyze(redprovider):
    """Test output of analyze function."""
    expected = """AssignmentNode()
  # identifiers: assign, assignment, assignment_, assignmentnode
  operator=''
  target ->
    NameNode()
      # identifiers: name, name_, namenode
      value='a'
  value ->
    BinaryOperatorNode()
      # identifiers: binary_operator, binary_operator_, binaryoperator, binaryoperatornode
      value='+'
      first ->
        IntNode() ...
      second ->
        IntNode() ..."""
    assert redprovider.analyze("a = 1+1") == expected


def test_RedBaronProvider_rename_arg(redprovider):
    src = """def foo(arg1="arg1"):  # arg1 bla
    bla = "arg1"
    arg1 = 1 + arg1
    return arg1\n"""

    expected = """def foo(newarg="arg1"):  # arg1 bla
    bla = "arg1"
    newarg = 1 + newarg
    return newarg\n"""

    assert redprovider.rename_arg(src, "arg1", "newarg") == expected


def test_RedBaronProvider_rename_arg_raise(redprovider):
    """Test that a wrong argument name raises a ValueError"""
    src = """def foo(arg1="arg1"):  # arg1 bla
    bla = "arg1"
    arg1 = 1 + arg1
    return arg1"""

    with pytest.raises(ValueError):
        redprovider.rename_arg(src, "arg", "newarg")


def test_RedBaronProvider_get_args(redprovider):
    src = """def foo(arg1, arg2, *args, kwarg1=1, kwarg2=3, kwarg3=None): pass"""
    expected = [("arg1", None),
                ("arg2", None),
                ("*args", None),
                ("kwarg1", '1'),
                ("kwarg2", '3'),
                ("kwarg3", "None")]

    assert redprovider.get_args(src) == expected


def test_RedBaronProvider_add_arg(redprovider):
    src = "def foo(arg1): pass\n"
    expected = "def foo(arg1, kwarg2=None): pass\n"
    assert redprovider.add_arg(src, 1, "kwarg2=None") == expected


def test_RedBaronProvider_get_parents(redprovider):
    src = """def foo():
    if True:
        def bar():
            for x in []:
                dir(help)"""
    expected = [('call_argument', (5, 21), (5, 24)),
                ('call', (5, 20), (5, 25)),
                ('atomtrailers', (5, 17), (5, 25)),
                ('for', (4, 13), (6, 0)),
                ('def', (3, 9), (6, 0)),
                ('ifelseblock', (2, 5), (6, 0)),
                ('def', (1, 1), (6, 0))]
    assert redprovider.get_parents(src, 5, 21) == expected
