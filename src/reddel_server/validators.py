"""Collection of validators
"""
from __future__ import absolute_import

from . import exceptions

__all__ = ['BaronTypeValidator']


class ValidatorInterface(object):
    def __call__(self, red):
        """Validate the given redbaron source

        :raises: :class:`ValidationError`
        """
        pass


class BaronTypeValidator(ValidatorInterface):
    def __init__(self, identifiers, single=False):
        """Initialize the validator

        :param identifiers: allowed identifiers for the redbaron source
        :type identifiers: sequence of :class:`str`
        :param single: If more than one top level node is valid
        :type single: :class:`boolean`
        """
        self.identifiers = identifiers
        self.single = single

    def __call__(self, red):
        """Validate the given redbaron source

        :raises: :class:`ValidationError`
        """
        if self.single:
            count = len(red)
            if count != 1:
                raise exceptions.ValidationError("Expected a single node but got %s" % count)
        for node in red:
            identifiers = node.generate_identifiers()
            if not any(i in identifiers for i in self.identifiers):
                raise exceptions.ValidationError("Expected identifier %s but got %s" %
                                                 (self.identifiers, identifiers))
