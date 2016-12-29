from __future__ import absolute_import

import importlib
import logging

logger = logging.getLogger("reddel")


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
