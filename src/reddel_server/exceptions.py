"""Collection of exceptions"""

__all__ = ['RedBaseException', 'ValidationException']


class RedBaseException(Exception):
    """All exceptions should share this common base class."""
    pass


class ValidationException(RedBaseException):
    """Raised when calling :class:`reddel_server.ValidatorInterface` and a source is invalid."""
    pass
