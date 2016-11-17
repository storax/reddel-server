"""The ``reddel_server`` package provides the complete supported API.

.. note:: It is not recommended to import any submodules as they are considered protected and
          might get breaking changes between minor and patch versions.

The API is divided into multiple domains:

  * `Server`_
  * `Providers`_
  * `Validators`_
  * `Exceptions`_

------
Server
------

The :class:`Server <reddel_server.Server>` is used to provide functions
via `EPC <http://python-epc.readthedocs.io/en/latest/>`_ that a client like Emacs can call.
The server is automatically created by the ``reddel`` script, which gets installed with
this package. If you need a custom server with more functionality like threading or
authentication (I don't know what kids need these days) you can use this as a base.
Most functions the server provides come from a :class:`provider <reddel_server.ProviderBase>` (see `Providers`_).

See:

  * :class:`Server <reddel_server.Server>`

---------
Providers
---------

:class:`Providers <reddel_server.ProviderBase>` are the heart of reddel. They provide methods that
you can remotely call via the `Server`_.
:meth:`list_methods <reddel_server.ProviderBase.list_methods>` can be used to get all available
methods of a provider. You can also call it with a piece of source code to get all
methods that can operate on it.
This works by decorating a method with :func:`red_validate <reddel_server.red_validate>`
and providing some `Validators`_. There are more useful decorators listed below.

The :class:`ChainedProvider <reddel_server.ChainedProvider>` is useful for combining multiple providers.
The `Server`_ from the CLI uses such provider to combine
a :class:`RedBaronProvider <reddel_server.RedBaronProvider>` and :class:`Provider <reddel_server.Provider>`.
By calling :meth:`add_provider <reddel_server.ChainedProvider.add_provider>` (also remotely) with a dotted
path you can add your own providers at runtime to extend reddel.

See:

  * :class:`ProviderBase <reddel_server.ProviderBase>`
  * :class:`ChainedProvider <reddel_server.ChainedProvider>`
  * :class:`RedBaronProvider <reddel_server.RedBaronProvider>`
  * :func:`redwraps <reddel_server.redwraps>`
  * :func:`red_src <reddel_server.red_src>`
  * :func:`red_validate <reddel_server.red_validate>`
  * :func:`red_type <reddel_server.red_type>`

.. _Validators:

----------
Validators
----------

Validators are used to get all methods compatible on processing a given source.
E.g. if the source is a function, reddel can report to Emacs which functions can be applied to
functions and Emacs can use the information to dynamically build a UI.

Validators can transform the source as well (see :meth:`transform <reddel_server.BaronTypeValidator.transform>`).

See:

  * :class:`ValidatorInterface <reddel_server.ValidatorInterface>`
  * :class:`BaronTypeValidator <reddel_server.BaronTypeValidator>`

----------
Exceptions
----------

Custom exceptions raised in reddel.
They all inherit from :class:`RedBaseException <reddel_server.RedBaseException>`.

See:

  * :class:`RedBaseException <reddel_server.RedBaseException>`
  * :class:`ValidationException <reddel_server.ValidationException>`

"""

from __future__ import absolute_import

from .exceptions import *
from .provider import *
from .server import *
from .utils import *
from .validators import *

__all__ = (exceptions.__all__ +
           server.__all__ +
           provider.__all__ +
           utils.__all__ +
           validators.__all__)

__version__ = "0.1.0"
