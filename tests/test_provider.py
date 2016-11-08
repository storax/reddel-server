import pytest
import redbaron

import reddel_server
from reddel_server import provider


TEST_DECORATORS = [
    provider.red_src(dump=False),
    provider.red_src(dump=True),
    provider.red_validate([]),
]


@pytest.mark.parametrize('decorator', TEST_DECORATORS)
def test_decorator_add_attrs(decorator):
    """Test that all attributes are added."""
    @decorator
    def foo(*args, **kwargs):
        pass  # pragma: nocover
    assert all([hasattr(foo, attr) for attr in provider._RED_FUNC_ATTRS])


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

    got = [getattr(foo, attr) for attr in provider._RED_FUNC_ATTRS]
    expected = values or [None for _ in provider._RED_FUNC_ATTRS]
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
