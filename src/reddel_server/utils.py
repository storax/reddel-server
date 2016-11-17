from __future__ import absolute_import

import functools
import importlib
import logging

__all__ = ['redwraps']

logger = logging.getLogger("reddel")

_RED_FUNC_ATTRS = ['red', 'validators']


def get_attr_from_dotted_path(path):
    """Return the imported object from the given path.

    :param path: a dotted path where the last segement is the attribute of the module to return.
                 E.g. ``mypkg.mymod.MyClass``.
    :type path: str
    :returns: the object specified by the path
    :raises: :class:`ImportError`, :class:`AttributeError`, :class:`ValueError`
    """
    logger.debug("importing %s", path)
    if '.' not in path:
        msg = "Expected a dotted path (e.g. 'mypkg.mymod.MyClass') but got {0!r}".format(path)
        raise ValueError(msg)

    providermodname, providerclsname = path.rsplit('.', 1)
    providermod = importlib.import_module(providermodname)

    return getattr(providermod, providerclsname)


def redwraps(towrap):
    """Use this when creating decorators instead of :func:`functools.wraps`

    :param towrap: the function to wrap
    :type towrap: :data:`types.FunctionType`
    :returns: the decorator
    :rtype: :data:`types.FunctionType`

    Makes sure to transfer special reddel attributes to the wrapped function.
    On top of that uses :func:`functools.wraps`.

    Example:


    .. testcode::

        import reddel_server

        def my_decorator(func):
            @reddel_server.redwraps(func)  # here you would normally use functools.wraps
            def wrapped(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapped

    """
    def redwraps_dec(func):
        if towrap:
            func = functools.wraps(towrap)(func)
        for attr in _RED_FUNC_ATTRS:
            val = getattr(towrap, attr, None)
            setattr(func, attr, val)
        return func
    return redwraps_dec
