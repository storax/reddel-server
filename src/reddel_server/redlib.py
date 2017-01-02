"""RedBaron specific library of functions"""
import collections

import redbaron

__all__ = ['Position', 'Parent', 'get_parents', 'get_node_of_region']


class Position(collections.namedtuple('Position', ['row', 'column'])):
    """Describes a position in the source code by line number and character position in that line.

    :param row: the line number
    :type row: :class:`int`
    :param column: the position in the line
    :type column: :class:`int`
    """
    __slots__ = ()


class Parent(collections.namedtuple('Parent', ['identifier', 'start', 'end'])):
    """Represents a node type with the bounding location.

    :param identifier: the node type
    :type identifier: :class:`str`
    :param start: the position where the node begins in the code
    :type start: :class:`Position`
    :param end: the position where the node ends in the code
    :type end: :class:`Position`
    """
    __slots__ = ()


def get_parents(red):
    """Yield the parents of the given red node

    :param red: the red baron source
    :type red: :class:`redbaron.base_nodes.Node` | :class:`redbaron.RedBaron`
    :returns: each parent of the given node
    :rtype: Generator[:class:`redbaron.base_nodes.Node`]
    :raises: None
    """
    current = red.parent
    while current:
        yield current
        current = current.parent


def get_node_of_region(red, start, end):
    """Get the node that contains the given region

    :param red: the red baron source
    :type red: :class:`redbaron.RedBaron`
    :param start: position of the beginning of the region
    :type start: :class:`Position`
    :param end: position of the end of the region
    :type end: :class:`Position`
    :returns: the node that contains the region
    :rtype: :class:`redbaron.base_nodes.Node`

    First the nodes at start and end are gathered. Then the common parent is selected.
    If the common parent is a list, the minimum slice is used.
    This makes it easier for the user because he can partially select nodes and
    still gets what he most likely intended to get.

    For example if your region partially selects several lines in a for loop
    and you want to extract them (``|`` shows the region bounds)::

        for i in range(10):
            a = 1 + 2
            b |= 4
            c = 5
            d =| 7

    then we expect to get back::

        b = 4
            c = 5
            d = 7

    Note that the leading tab is missing because it doesn't belong to the ``b = 4`` node.

    .. doctest::

        >>> import redbaron
        >>> import reddel_server
        >>> testsrc = ("for i in range(10):\\n"
        ...            "    a = 1 + 2\\n"
        ...            "    b = 4\\n"
        ...            "    c = 5\\n"
        ...            "    d = 7\\n")
        >>> start = (3, 7)
        >>> end = (5, 8)
        >>> reddel_server.get_node_of_region(redbaron.RedBaron(testsrc), start, end).dumps()
        'b = 4\\n    c = 5\\n    d = 7'

    You can also partially select a list:

    .. doctest::

       >>> testsrc = "[1, 2, 3, 4, 5, 6]"
       >>> start = (1, 8)  # "3"
       >>> end = (1, 14)  # "5"
       >>> reddel_server.get_node_of_region(redbaron.RedBaron(testsrc), start, end).dumps()
       '3, 4, 5'

    """
    snode = red.find_by_position(start)
    enode = red.find_by_position(end)
    if snode == enode:
        return snode
    snodes = [snode] + list(get_parents(snode))
    enodes = [enode] + list(get_parents(enode))
    previous = red
    for snode, enode in list(zip(reversed(snodes), reversed(enodes))):
        # both list of parents should end with the root node
        # so we iterate over the parents in reverse until we
        # reach a parent that is not common.
        # the previous parent then has to encapsulate both
        if snode != enode:
            if hasattr(previous, "node_list"):
                # For lists we want the minimum slice of the list.
                # E.g. the region spans over 2 functions in a big module
                # the common parent would be the root node.
                # We only want the part containing the 2 functions and not everything.
                # Unfortunately we might loose some information if we slice the proxy list.
                # When we use node_list then we keep things like new lines etc.
                try:
                    sindex = previous.node_list.index(snode)
                    eindex = previous.node_list.index(enode)
                except ValueError:
                    # if one of the nodes is not in the list, it means it's not part of
                    # previous value. E.g. previous is a function definition and snode
                    # is part of the arguments while enode is part of the function body.
                    # in that case we take the whole previous node (e.g. the whole function)
                    pass
                else:
                    previous = redbaron.NodeList(previous.node_list[sindex:eindex + 1])
            break
        previous = snode
    return previous
