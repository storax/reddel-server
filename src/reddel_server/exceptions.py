"""Collection of exceptions
"""

__all__ = ['RedBaseException', 'RedValueError', 'RedImportError', 'RedAttributeError', 'ValidationException']


class RedBaseException(Exception):
    """All exceptions should share this common base class."""
    pass


class RedValueError(RedBaseException, ValueError):
    pass


class RedImportError(RedBaseException, ImportError):
    pass


class RedAttributeError(RedBaseException, AttributeError):
    pass


class ValidationException(RedBaseException):
    pass
