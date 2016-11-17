"""Collection of exceptions"""

__all__ = ['RedBaseException', 'ValidationException']


class RedBaseException(Exception):
    """All exceptions should share this common base class."""
    pass


class ValidationException(RedBaseException):
    pass
