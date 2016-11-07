"""Collection of validators
"""
from __future__ import absolute_import

import abc

import six

from . import exceptions

__all__ = ['BaronTypeValidator', 'ValidatorInterface']


class ValidatorInterface(six.with_metaclass(abc.ABCMeta, object)):
    """Validator interface.

    Override :meth:`ValidatorInterface.__call__`.
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

        :param red: a red baron or other nodes
        """
        return red


class BaronTypeValidator(ValidatorInterface):
    """Validate that the given :class:`redbaron.RedBaron`
    contains the correct nodes and optionally that there is only a single root node.
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

    def __call__(self, red):
        """Validate the given redbaron source

        :raises: :class:`ValidationException <reddel_server.ValidationException`
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
        """If :data:`BaronTypeValidator.single` is True return the first node."""
        if self.single:
            return red[0]
        return red
