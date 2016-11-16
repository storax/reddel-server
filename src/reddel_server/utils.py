from __future__ import absolute_import

import importlib
import logging

from . import exceptions

logger = logging.getLogger("reddel")


def get_attr_from_dotted_path(path):
    """Return the imported object from the given path.

    :param path: a dotted path where the last segement is the attribute of the module to return.
                 E.g. ``mypkg.mymod.MyClass``.
    :type path: str
    :returns: the object specified by the path
    :raises: :class:`reddel_server.ImportError`, :class:`reddel_server.AttributeError`, :class:`reddel_server.ValueError`
    """
    logger.debug("importing %s", path)
    if '.' not in path:
        msg = "Expected a dotted path (e.g. 'mypkg.mymod.MyClass') but got {0!r}".format(path)
        raise exceptions.RedValueError(msg)

    providermodname, providerclsname = path.rsplit('.', 1)
    try:
        providermod = importlib.import_module(providermodname)
    except ImportError as err:
        raise exceptions.RedImportError(*err.args)

    try:
        return getattr(providermod, providerclsname)
    except AttributeError as err:
        msg = "Could not get attribute {0!r} from module {1!r}. {2}".format(providerclsname, providermodname, err.args[0])
        raise exceptions.RedAttributeError(msg, *err.args[1:])
