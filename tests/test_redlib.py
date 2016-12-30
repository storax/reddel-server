"""Test redbaron specific library functions"""
import types

import redbaron

import reddel_server


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
