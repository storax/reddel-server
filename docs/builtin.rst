=================
Builtin Functions
=================

Here is a list of all builtin functions the server provides.
Some functions that work on code have a table like this in the docstring:

.. table::

    +--------------+----------------+-----------+------------------+---------------+
    | source input | outputs source | region    | only single node | allowed types |
    +==============+================+===========+==================+===============+
    | Yes          | No             | Mandatory | No               | Any           |
    +--------------+----------------+-----------+------------------+---------------+

- ``source input``: ``Yes`` means, that the function expects source code as first argument
- ``outputs source``: ``Yes``  means that the function returns source code back
- ``region``: ``No`` means that this function does not accept regions. ``Optional`` means that
  if a region is specified, only the region will be considered. If no region is specified, the whole
  source is used. ``Mandatory`` always requires a region.
- ``only single node``: ``Yes`` means only a single node on root level is allowed.
- ``allowed types``: a list of allowed identifiers on root level. E.g. ``def`` means only function
  definitions are valid.

See :func:`reddel_server.red_src`, :func:`reddel_server.red_validate`.

Basic Functions
===============

The following functions are useful for introspection of reddel:

.. automethod:: reddel_server.ProviderBase.list_methods
   :noindex:
.. automethod:: reddel_server.ProviderBase.help
   :noindex:
.. automethod:: reddel_server.ProviderBase.echo
   :noindex:
.. automethod:: reddel_server.ProviderBase.reddel_version
   :noindex:

Some very simple logging control at runtime:

.. automethod:: reddel_server.Server.set_logging_level
   :noindex:

Extend the provider at runtime:

.. automethod:: reddel_server.ChainedProvider.add_provider
   :noindex:

Code Introspection
==================

The following functions are useful for inspecting source code:

.. rubric:: Any source

.. automethod:: reddel_server.RedBaronProvider.analyze
   :noindex:
.. automethod:: reddel_server.RedBaronProvider.get_parents
   :noindex:

.. rubric:: Function Definitions

.. automethod:: reddel_server.RedBaronProvider.get_args
   :noindex:

Code Transformation
===================

The following functions transform source code:

.. rubric:: Function Definitions

.. automethod:: reddel_server.RedBaronProvider.rename_arg
   :noindex:
.. automethod:: reddel_server.RedBaronProvider.add_arg
   :noindex:
