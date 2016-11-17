=================
Builtin Functions
=================

Here is a list of all builtin functions the server provides.


Basic Functions
===============

The following functions are useful for introspection of reddel:

.. automethod:: reddel_server.ProviderBase.list_methods
   :noindex:
.. automethod:: reddel_server.ProviderBase.help
   :noindex:
.. automethod:: reddel_server.ProviderBase.reddel_version
   :noindex:
.. automethod:: reddel_server.ProviderBase.echo
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

.. automethod:: reddel_server.RedBaronProvider.add_arg
   :noindex:
.. automethod:: reddel_server.RedBaronProvider.rename_arg
   :noindex:
