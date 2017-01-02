"""Test red baron specific functionality"""
import types

import pytest
import redbaron

import reddel_server
from reddel_server import redprovider


TEST_DECORATORS = [
    redprovider.red_src(dump=False),
    redprovider.red_src(dump=True),
    redprovider.red_validate([]),
]


def test_redwraps_add_attrs():
    """Test that attibutes are added."""
    @reddel_server.redwraps(None)
    def foo():
        pass  # pragma: nocover
    assert all([hasattr(foo, attr) for attr in redprovider._RED_FUNC_ATTRS])


def test_redwraps_attr_value():
    """Test that attibutes values are transferred."""
    def bar():
        pass  # pragma: nocover

    bar.red = 'test'

    @reddel_server.redwraps(bar)
    def foo():
        pass  # pragma: nocover
    assert all([getattr(foo, attr) == getattr(bar, attr, None) for attr in redprovider._RED_FUNC_ATTRS])


@pytest.mark.parametrize('decorator', TEST_DECORATORS)
def test_decorator_add_attrs(decorator):
    """Test that all attributes are added."""
    @decorator
    def foo(*args, **kwargs):
        pass  # pragma: nocover
    assert all([hasattr(foo, attr) for attr in redprovider._RED_FUNC_ATTRS])


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

    got = [getattr(foo, attr) for attr in redprovider._RED_FUNC_ATTRS]
    expected = values or [None for _ in redprovider._RED_FUNC_ATTRS]
    assert  got == expected


def test_red_src_dump_false():
    """Test that red_src decorator converts to RedBaron"""
    @reddel_server.red_src(dump=False)
    def foo(self, src):
        return src

    src = "1+1"
    assert isinstance(foo(None, src), redbaron.RedBaron)


def test_red_src_dump_true():
    """Test that red_src decorator dumps the return value"""
    @reddel_server.red_src(dump=True)
    def foo(self, src):
        assert isinstance(src, redbaron.RedBaron)
        return src

    src = "1+1"
    red = redbaron.RedBaron(src)
    assert src == foo(None, src)


def test_red_validate_attr():
    """Test that the validators attribute is applied."""
    validator = reddel_server.OptionalRegionValidator()
    @reddel_server.red_validate([validator])
    def foo(*args, **kwargs):
        pass  # pragma: nocover

    assert foo.validators == [validator]


def test_red_validate_invalid():
    """Test that invalid values raise"""
    validator = reddel_server.TypeValidator(['def'])
    @reddel_server.red_validate([validator])
    def foo(self, src, start, end):
        pass  # pragma: nocover

    src = redbaron.RedBaron("1+1")
    with pytest.raises(reddel_server.ValidationException):
        foo(None, src, None, None)


def test_red_validate_valid():
    """Test that valid values pass"""
    validator = reddel_server.TypeValidator(["def"])
    @reddel_server.red_validate([validator])
    def foo(self, src, start, end):
        pass

    src = redbaron.RedBaron("def foo(): pass")
    foo(None, src, None, None)


def test_red_validate_transform():
    """Test that values get transformed"""
    validator = reddel_server.SingleNodeValidator()
    src = redbaron.RedBaron("def foo(): pass")

    @reddel_server.red_validate([validator])
    def foo(self, src, start, end):
        return src

    transformed = foo(None, src, None, None)
    assert src[0] == transformed


@pytest.fixture(scope='module')
def redbaronprovider(server):
    return reddel_server.RedBaronProvider(server)


def test_RedBaronProvider_analyze(redbaronprovider):
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
    assert redbaronprovider.analyze("a = 1+1") == expected


def test_RedBaronProvider_rename_arg(redbaronprovider):
    src = """def foo(arg1="arg1"):  # arg1 bla
    bla = "arg1"
    arg1 = 1 + arg1
    return arg1\n"""

    expected = """def foo(newarg="arg1"):  # arg1 bla
    bla = "arg1"
    newarg = 1 + newarg
    return newarg\n"""

    assert redbaronprovider.rename_arg(src, None, None, "arg1", "newarg") == expected


def test_RedBaronProvider_rename_arg_raise(redbaronprovider):
    """Test that a wrong argument name raises a ValueError"""
    src = """def foo(arg1="arg1"):  # arg1 bla
    bla = "arg1"
    arg1 = 1 + arg1
    return arg1"""

    with pytest.raises(ValueError):
        redbaronprovider.rename_arg(src, None, None, "arg", "newarg")


def test_RedBaronProvider_get_args(redbaronprovider):
    src = """def foo(arg1, arg2, *args, kwarg1=1, kwarg2=3, kwarg3=None): pass"""
    expected = [("arg1", None),
                ("arg2", None),
                ("*args", None),
                ("kwarg1", '1'),
                ("kwarg2", '3'),
                ("kwarg3", "None")]

    assert redbaronprovider.get_args(src, None, None) == expected


def test_RedBaronProvider_add_arg(redbaronprovider):
    src = "def foo(arg1): pass\n"
    expected = "def foo(arg1, kwarg2=None): pass\n"
    assert expected == redbaronprovider.add_arg(src, None, None, 1, "kwarg2=None")


def test_RedBaronProvider_get_parents(redbaronprovider):
    src = """def foo():
    if True:
        def bar():
            for x in []:
                dir(help)"""
    expected = [('call_argument', reddel_server.Position(5, 21), reddel_server.Position(5, 24)),
                ('call', (5, 20), (5, 25)),
                ('atomtrailers', (5, 17), (5, 25)),
                ('for', (4, 13), (6, 0)),
                ('def', (3, 9), (6, 0)),
                ('ifelseblock', (2, 5), (6, 0)),
                ('def', (1, 1), (6, 0))]
    result = redbaronprovider.get_parents(src, reddel_server.Position(5, 21), reddel_server.Position(5, 21))
    assert expected == result
