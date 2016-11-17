"""Collection of validators"""
from __future__ import absolute_import

import abc

import six

from . import exceptions

__all__ = ['BaronTypeValidator', 'ValidatorInterface']


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
            def __call__(self, red):
                if len(red) != 1:
                    raise reddel_server.ValidationException("Expected only a single root node.")

        val = MyValidator()

        val(redbaron.RedBaron("a=2"))

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
    def __call__(self, red):  # pragma: no cover
        """Validate the given redbaron source

        :param red: the source
        :type red: :class:`redbaron.RedBaron`
        :raises: :class:`ValidationException <reddel_server.ValidationException>`
        """
        pass

    def transform(self, red):  # pragma: no cover
        """Transform the given red baron

        The base implementation just returns the source.
        See :meth:`reddel_server.BaronTypeValidator.transform` for an example.

        :param red: a red baron source or other nodes
        :returns: the transformed source
        """
        return red


class BaronTypeValidator(ValidatorInterface):
    """Validate that the given :class:`redbaron.RedBaron`
    contains the correct nodes and optionally that there is only a single root node.

    Examples:

    .. testcode::

        from redbaron import RedBaron
        import reddel_server

        val1 = reddel_server.BaronTypeValidator(['def'], single=True)
        # valid
        val1(RedBaron('def foo(): pass'))
        # invalid
        invalid_sources = [RedBaron('def foo(): pass\\ndef bar(): pass'),  # two are invalid
                           RedBaron('a=1')]  # not a function definition
        for src in invalid_sources:
            try:
                val1(src)
            except reddel_server.ValidationException:
                pass
            else:
                assert False, "Validator should have raised: %s" % src

    """
    def __init__(self, identifiers, single=False):
        """Initialize the validator

        :param identifiers: allowed identifiers for the redbaron source
        :type identifiers: sequence of :class:`str`
        :param single: If more than one top level node is valid
        :type single: :class:`bool`
        """
        self.identifiers = identifiers
        self.single = single
        """True if only a single root node is accepted as input source.
        :meth:`reddel_server.BaronTypeValidator.transform` will then return
        the first node.
        """

    def __call__(self, red):
        """Validate the given redbaron source

        :raises: :class:`ValidationException <reddel_server.ValidationException>`
        """
        if self.single:
            count = len(red)
            if count != 1:
                raise exceptions.ValidationException("Expected a single node but got %s" % count)
        for node in red:
            identifiers = node.generate_identifiers()
            if not any(i in identifiers for i in self.identifiers):
                raise exceptions.ValidationException("Expected identifier %s but got %s" %
                                                     (self.identifiers, identifiers))

    def transform(self, red):
        """When :data:`reddel_server.BaronTypeValidator.single` is ``True`` return the first node.

        When creating a :class:`redbaron.RedBaron` from a source,
        the root is a list of nodes:

        .. doctest::

            >>> import redbaron
            >>> src = redbaron.RedBaron("a=1")
            >>> src
            0   a=1
            <BLANKLINE>

        When :data:`reddel_server.BaronTypeValidator.single` is True
        this function will return:

        .. doctest::

            >>> src[0]
            a=1

        """
        if self.single:
            return red[0]
        return red
