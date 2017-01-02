"""The ``reddel_server`` package provides the complete supported API.

.. note:: It is not recommended to import any submodules as they are considered protected and
          might get breaking changes between minor and patch versions.

The API is divided into multiple domains:

  * `Server`_
  * `Providers`_

    * `RedBaron Provider`_

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
you can call remotely via the `Server`_.
:meth:`list_methods <reddel_server.ProviderBase.list_methods>` can be used to get all available
methods of a provider. You can also call it with a piece of source code to get all
methods that can operate on it.
This works by decorating a method with :func:`red_validate <reddel_server.red_validate>`
and providing some `Validators`_. There are more useful decorators listed below.

The :class:`ChainedProvider <reddel_server.ChainedProvider>` is useful for combining multiple providers.
The `Server`_ from the CLI uses such provider to combine
a :class:`RedBaronProvider <reddel_server.RedBaronProvider>` and any provider specified by the user.
By calling :meth:`add_provider <reddel_server.ChainedProvider.add_provider>` (also remotely) with a dotted
path you can add your own providers at runtime to extend reddel.

See:

  * :class:`ProviderBase <reddel_server.ProviderBase>`
  * :class:`ChainedProvider <reddel_server.ChainedProvider>`

+++++++++++++++++
RedBaron Provider
+++++++++++++++++

The :class:`RedBaronProvider <reddel_server.RedBaronProvider>` provides the built-in redbaron specific
functionality.
If you want to extend it or write your own provider, it's recommended to make use of the following decorators:

  * :func:`red_src <reddel_server.red_src>`
  * :func:`red_validate <reddel_server.red_validate>`

These decorators are the mini framework that allows the server to tell the client what actions are available for
a given piece of code.

There is also a small library with helper functions that might be useful when writing a provider:

  * :func:`get_parents <reddel_server.get_parents>`
  * :func:`get_node_of_region <reddel_server.get_node_of_region>`

See:

  * :class:`RedBaronProvider <reddel_server.RedBaronProvider>`
  * :func:`redwraps <reddel_server.redwraps>`
  * :func:`red_src <reddel_server.red_src>`
  * :func:`red_validate <reddel_server.red_validate>`
  * :func:`get_parents <reddel_server.get_parents>`
  * :func:`get_node_of_region <reddel_server.get_node_of_region>`

----------
Validators
----------

Validators are used to get all methods compatible for processing a given source.
E.g. if the source is a function, reddel can report to Emacs which functions can be applied to
functions and Emacs can use the information to dynamically build a UI.

Validators can transform the source as well.
The transformed source is passed onto the next validator when you use :func:`reddel_server.red_validate`.
All validators provided by ``reddel_server`` can be used as mix-ins.
When you create your own validator and you inherit from multiple builtin ones then
they are effectively combined since all of them perform the appropriate super call.

See:

  * :class:`ValidatorInterface <reddel_server.ValidatorInterface>`
  * :class:`OptionalRegionValidator <reddel_server.OptionalRegionValidator>`
  * :class:`MandatoryRegionValidator <reddel_server.MandatoryRegionValidator>`
  * :class:`SingleNodeValidator <reddel_server.SingleNodeValidator>`
  * :class:`TypeValidator <reddel_server.TypeValidator>`

----------
Exceptions
----------

Here is a list of custom exceptions raised in reddel:

  * :class:`ValidationException <reddel_server.ValidationException>`

---
API
---

"""

from __future__ import absolute_import

from .provider import *
from .redlib import *
from .redprovider import *
from .server import *
from .validators import *

__all__ = (server.__all__ +
           provider.__all__ +
           validators.__all__ +
           redprovider.__all__ +
           redlib.__all__)

__version__ = "0.2.0"
