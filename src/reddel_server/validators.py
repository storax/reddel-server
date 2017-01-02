"""Collection of validators"""
from __future__ import absolute_import

import abc

import redbaron
import six

from . import redlib


__all__ = ['ValidatorInterface', 'OptionalRegionValidator', 'MandatoryRegionValidator',
           'SingleNodeValidator', 'TypeValidator', 'ValidationException']


class ValidationException(Exception):
    """Raised when calling :class:`reddel_server.ValidatorInterface` and a source is invalid."""
    pass


class ValidatorInterface(six.with_metaclass(abc.ABCMeta, object)):
    """Validator interface

    A validator checks a given source input and raises a
    :class:`ValidationException <reddel_server.ValidationException>`
    if the input is invalid.
    This can be used to check, which methods of a provider are compatible
    with a given input (see :func:`reddel_server.red_validate`).

    Creating your own validator is simple.
    Just subclass from this class and override :meth:`reddel_server.ValidatorInterface.__call__`.

    .. testcode::

        import redbaron
        import reddel_server

        class MyValidator(reddel_server.ValidatorInterface):
            def __call__(self, red, start=None, end=None):
                if not (start and end):
                    raise reddel_server.ValidationException("Expected a region.")
                if len(red) != 1:
                    raise reddel_server.ValidationException("Expected only a single root node.")

        val = MyValidator()

        val(redbaron.RedBaron("a=2"), reddel_server.Position(1, 1), reddel_server.Position(1, 3))

        try:
            val(redbaron.RedBaron("a=2+1\\nb=3"))
        except reddel_server.ValidationException:
            pass
        else:
            assert False, 'Validator should have raised.'

    A Validator can also implement a :meth:`transformation <reddel_server.ValidatorInterface.transform>`.
    This transformation is used in :func:`reddel_server.red_validate`.
    """
    @abc.abstractmethod
    def __call__(self, red, start=None, end=None):  # pragma: no cover
        """Validate the given redbaron source

        :param red: the source
        :type red: :class:`redbaron.RedBaron`
        :param start: the start position of the selected region, if any.
        :type start: :class:`reddel_server.Position` | ``None``
        :param end: the end position of the selected region, if any.
        :type end: :class:`reddel_server.Position` | ``None``
        :raises: :class:`ValidationException <reddel_server.ValidationException>`
        """
        pass

    def transform(self, red, start=None, end=None):  # pragma: no cover
        """Transform the given red baron

        The base implementation just returns the source.
        See :meth:`reddel_server.TypeValidator.transform` for an example.

        :param red: a red baron source or other nodes
        :param start: the start position of the selected region, if any.
        :type start: :class:`reddel_server.Position` | ``None``
        :param end: the end position of the selected region, if any.
        :type end: :class:`reddel_server.Position` | ``None``
        :returns: the transformed source, start and end
        """
        return red, start, end


class OptionalRegionValidator(ValidatorInterface):
    """Used for functions that either use the given source code or only the
    specified region if a region is specified.

    If a region is specified the source is transformed to only contain the region.

    Examples:

    .. doctest::

        >>> from redbaron import RedBaron
        >>> import reddel_server
        >>> val1 = reddel_server.OptionalRegionValidator()
        >>> src, start, end = val1.transform(RedBaron('def foo(): pass'), start=None, end=None)
        >>> src.dumps(), start, end
        ('def foo(): pass\\n', None, None)
        >>> src, start, end = val1.transform(RedBaron('a=1\\nb=1'), start=(2,1), end=(2,3))
        >>> src.dumps(), start, end
        ('b=1', Position(row=1, column=1), Position(row=1, column=3))

    """
    def __call__(self, red, start=None, end=None):
        """Validate the given redbaron source

        :param red: the source
        :type red: :class:`redbaron.RedBaron`
        :param start: the start position of the selected region, if any.
        :type start: :class:`reddel_server.Position` | ``None``
        :param end: the end position of the selected region, if any.
        :type end: :class:`reddel_server.Position` | ``None``
        :raises: :class:`ValidationException <reddel_server.ValidationException>`
        """
        return super(OptionalRegionValidator, self).__call__(red, start, end)

    def transform(self, red, start=None, end=None):
        """Extract the region from red if any region is specified

        :param red: a red baron source or other nodes
        :param start: the start position of the selected region, if any.
        :type start: :class:`reddel_server.Position` | ``None``
        :param end: the end position of the selected region, if any.
        :type end: :class:`reddel_server.Position` | ``None``
        :returns: the transformed source, start and end
        """
        red, start, end = super(OptionalRegionValidator, self).transform(red, start, end)
        if start and end:
            red = redlib.get_node_of_region(red, start, end)
            bbox = red.bounding_box
            start = redlib.Position(*bbox.top_left.to_tuple())
            end = redlib.Position(*bbox.bottom_right.to_tuple())
        return red, start, end


class MandatoryRegionValidator(ValidatorInterface):
    """Used for functions that expect a region"""
    def __call__(self, red, start=None, end=None):
        """Validate that a region is specified

        :param red: the source
        :type red: :class:`redbaron.RedBaron`
        :param start: the start position of the selected region, if any.
        :type start: :class:`reddel_server.Position` | ``None``
        :param end: the end position of the selected region, if any.
        :type end: :class:`reddel_server.Position` | ``None``
        :raises: :class:`ValidationException <reddel_server.ValidationException>` if start or end is ``None``.
        """
        super(MandatoryRegionValidator, self).__call__(red, start, end)
        if not (start and end):
            raise ValidationException("No region specified.")


class SingleNodeValidator(ValidatorInterface):
    """Validate that only one single node is provided.

    If a list of nodes is provided, validate that it contains only one element.
    Transform the source to only a single node.

    .. doctest::

        >>> from redbaron import RedBaron
        >>> import reddel_server
        >>> val1 = reddel_server.SingleNodeValidator()
        >>> val1(redbaron.RedBaron("a=1+1"))
        >>> val1.transform(redbaron.RedBaron("a=1+1"))
        (a=1+1, None, None)
        >>> try:
        ...     val1(redbaron.RedBaron("a=1+1\\nb=2"))
        ... except reddel_server.ValidationException:
        ...     pass
        ... else:
        ...     assert False, "Validator should have raised"

    By default, when creating a :class:`redbaron.RedBaron` source,
    you always get a list even for a single expression.
    If you always want the single node, this validator will handle the transformation.
    """
    def __call__(self, red, start=None, end=None):
        """Validate the given redbaron source

        :param red: the source
        :type red: :class:`redbaron.RedBaron`
        :param start: the start position of the selected region, if any.
        :type start: :class:`reddel_server.Position` | ``None``
        :param end: the end position of the selected region, if any.
        :type end: :class:`reddel_server.Position` | ``None``
        :raises: :class:`ValidationException <reddel_server.ValidationException>`
        """
        super(SingleNodeValidator, self).__call__(red, start, end)
        if start and end:
            red = redlib.get_node_of_region(red, start, end)
        if isinstance(red, (redbaron.NodeList, redbaron.ProxyList)) and len(red) > 1:
            raise ValidationException("Expected single node but got: %s" % red)

    def transform(self, red, start=None, end=None):
        """Extract the single node red is a list

        :param red: a red baron source or other nodes
        :param start: the start position of the selected region, if any.
        :type start: :class:`reddel_server.Position` | ``None``
        :param end: the end position of the selected region, if any.
        :type end: :class:`reddel_server.Position` | ``None``
        :returns: the transformed source, start and end
        """
        red, start, end = super(SingleNodeValidator, self).transform(red, start, end)
        if not (start and end) and isinstance(red, (redbaron.NodeList, redbaron.ProxyList)):
            red = red[0]
        return red, start, end


class TypeValidator(ValidatorInterface):
    """Validate that the given source contains the correct type of nodes.

    If a region is specified, only the region is checked.
    If a list of nodes is given, e.g. a :class:`redbaron.RedBaron` object,
    all nodes will be checked.

    Examples:

    .. testcode::

        from redbaron import RedBaron
        import reddel_server

        val1 = reddel_server.TypeValidator(['def'])

        # valid
        val1(RedBaron('def foo(): pass'))
        val1(RedBaron('def foo(): pass\\ndef bar(): pass'))

        # invalid
        try:
            val1(RedBaron('def foo(): pass\\na=1+1'))
        except reddel_server.ValidationException:
            pass
        else:
            assert False, "Validator should have raised"

    """
    def __init__(self, identifiers):
        """Initialize the validator

        :param identifiers: allowed identifiers for the redbaron source
        :type identifiers: sequence of :class:`str`
        """
        super(TypeValidator, self).__init__()
        self.identifiers = identifiers

    def __call__(self, red, start=None, end=None):
        """Validate the given redbaron source

        :param red: the source
        :type red: :class:`redbaron.RedBaron`
        :param start: the start position of the selected region, if any.
        :type start: :class:`reddel_server.Position` | ``None``
        :param end: the end position of the selected region, if any.
        :type end: :class:`reddel_server.Position` | ``None``
        :raises: :class:`ValidationException <reddel_server.ValidationException>`
        """
        super(TypeValidator, self).__call__(red, start, end)
        if start and end:
            red = redlib.get_node_of_region(red, start, end)
        if not isinstance(red, (redbaron.NodeList, redbaron.ProxyList)):
            red = (red,)

        for node in red:
            identifiers = node.generate_identifiers()
            if not any(i in identifiers for i in self.identifiers):
                raise ValidationException("Expected identifier %s but got %s" %
                                          (self.identifiers, identifiers))
