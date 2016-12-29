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


def test_get_parents():
    """Test retrieving all parents from a node"""
    testsrc = redbaron.RedBaron("def foo(): a = 1+1")
    testnode = testsrc.find_by_position((1, 18))
    parents = reddel_server.get_parents(testnode)
    expected = [testnode.parent, testnode.parent.parent, testnode.parent.parent.parent,
                testnode.parent.parent.parent.parent]
    assert expected == list(parents)


def test_get_parents_generator():
    """Test that the function returns a generator"""
    testsrc = redbaron.RedBaron("1+1")
    parentgen = reddel_server.get_parents(testsrc)
    assert isinstance(parentgen, types.GeneratorType)


def test_get_node_of_region_bad_region():
    """Test get_node_of_region with an invalid region"""
    testsrc = redbaron.RedBaron("1+1")
    start = reddel_server.Position(0, 1)
    end = reddel_server.Position(1, 3)
    assert testsrc == reddel_server.get_node_of_region(testsrc, start, end)

def test_get_node_of_region_simple():
    """Test get_node_of_region for when start and end are part of a simple expression"""
    testsrc = redbaron.RedBaron("1+1")
    start = reddel_server.Position(1, 1)
    end = reddel_server.Position(1, 3)
    expected = testsrc[0]
    assert expected == reddel_server.get_node_of_region(testsrc, start, end)

def test_get_node_of_region_same():
    """Test get_node_of_region for when start and end are the same nodes"""
    testsrc = redbaron.RedBaron("lambda: 1+1")
    start = reddel_server.Position(1, 1)
    end = reddel_server.Position(1, 2)
    expected = testsrc[0]
    assert expected == reddel_server.get_node_of_region(testsrc, start, end)


def test_get_node_of_region_same_level():
    """Test get_node_of_region for when the nodes for start and end are on the same level"""
    testsrc = redbaron.RedBaron("1+1\n2*2")
    start = reddel_server.Position(1, 2)
    end = reddel_server.Position(2, 2)
    assert reddel_server.get_node_of_region(testsrc, start, end).dumps() == testsrc.dumps()


def test_get_node_of_region_different_level():
    """Test get_node_of_region for when the nodes for start and end are on different levels"""
    testsrc = redbaron.RedBaron("def foo(arg): a = 1+1")
    start = reddel_server.Position(1, 9)  # "arg"
    end = reddel_server.Position(1, 20)  # "+"
    assert reddel_server.get_node_of_region(testsrc, start, end) == testsrc[0]  # the function definition


def test_get_node_of_region_slice_list():
    """Test get_node_of_region for when the nodes are only a slice in a node list"""
    testsrc = redbaron.RedBaron("1+1\n"
                                "a=1\n"
                                "for i in range(10):\n"
                                "    b=i\n"
                                "c=3")
    start = reddel_server.Position(2, 3)  # a="1"
    end = reddel_server.Position(4, 6)  # b"="1
    expected = redbaron.NodeList(testsrc.node_list[2:5])
    assert expected.dumps() == reddel_server.get_node_of_region(testsrc, start, end).dumps()


def test_get_node_of_region_slice_for_loop():
    """Test get_node_of_region for when the nodes slice a for loop body"""
    testsrc = redbaron.RedBaron("for i in range(10):\n"
                                "    a = 1 + 2\n"
                                "    b = 4\n"
                                "    c = 5\n"
                                "    d = 7\n")
    start = reddel_server.Position(3, 7)
    end = reddel_server.Position(5, 8)
    expected = "b = 4\n    c = 5\n    d = 7"
    assert expected == reddel_server.get_node_of_region(testsrc, start, end).dumps()


def test_get_node_of_region_slice_list_declaration():
    """Test get_node_of_region for when the nodes slice a list declaration"""
    testsrc = redbaron.RedBaron("[1, 2, 3, 4, 5, 6]")
    start = reddel_server.Position(1, 8)
    end = reddel_server.Position(1, 14)
    expected = "3, 4, 5"
    assert expected == reddel_server.get_node_of_region(testsrc, start, end).dumps()


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
    validator = reddel_server.BaronTypeValidator(["def"], single=True)
    @reddel_server.red_validate([validator])
    def foo(*args, **kwargs):
        pass  # pragma: nocover

    assert foo.validators == [validator]


def test_red_validate_invalid():
    """Test that invalid values raise"""
    validator = reddel_server.BaronTypeValidator(["def"])
    @reddel_server.red_validate([validator])
    def foo(self, src):
        pass  # pragma: nocover

    src = redbaron.RedBaron("1+1")
    with pytest.raises(reddel_server.ValidationException):
        foo(None, src)


def test_red_validate_valid():
    """Test that valid values pass"""
    validator = reddel_server.BaronTypeValidator(["def"], single=True)
    @reddel_server.red_validate([validator])
    def foo(self, src):
        pass

    src = redbaron.RedBaron("def foo(): pass")
    foo(None, src)


def test_red_validate_transform():
    """Test that values get transformed"""
    validator = reddel_server.BaronTypeValidator(["def"], single=True)
    src = redbaron.RedBaron("def foo(): pass")

    @reddel_server.red_validate([validator])
    def foo(self, src):
        return src

    transformed = foo(None, src)
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

    assert redbaronprovider.rename_arg(src, "arg1", "newarg") == expected


def test_RedBaronProvider_rename_arg_raise(redbaronprovider):
    """Test that a wrong argument name raises a ValueError"""
    src = """def foo(arg1="arg1"):  # arg1 bla
    bla = "arg1"
    arg1 = 1 + arg1
    return arg1"""

    with pytest.raises(ValueError):
        redbaronprovider.rename_arg(src, "arg", "newarg")


def test_RedBaronProvider_get_args(redbaronprovider):
    src = """def foo(arg1, arg2, *args, kwarg1=1, kwarg2=3, kwarg3=None): pass"""
    expected = [("arg1", None),
                ("arg2", None),
                ("*args", None),
                ("kwarg1", '1'),
                ("kwarg2", '3'),
                ("kwarg3", "None")]

    assert redbaronprovider.get_args(src) == expected


def test_RedBaronProvider_add_arg(redbaronprovider):
    src = "def foo(arg1): pass\n"
    expected = "def foo(arg1, kwarg2=None): pass\n"
    assert redbaronprovider.add_arg(src, 1, "kwarg2=None") == expected


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
    assert redbaronprovider.get_parents(src, reddel_server.Position(5, 21)) == expected
