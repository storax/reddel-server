=============
Reddel-Server
=============

.. start-badges

- |license| |status| |issues|
- |stars| |fork|
- |docs|
- |travis| |coveralls|
- |version| |downloads| |wheel| |supported-versions| |supported-implementations|

.. |fork| image:: https://img.shields.io/github/forks/storax/reddel-server.svg?style=social&label=Fork
    :alt: Github Forks
    :target: https://github.com/storax/reddel-server/network

.. |stars| image:: https://img.shields.io/github/stars/storax/reddel-server.svg?style=social&label=Star
    :alt: Github Stars
    :target: https://github.com/storax/reddel-server/stargazers

.. |issues| image:: https://img.shields.io/github/issues/storax/reddel-server.svg
    :alt: Github Issues
    :target: https://github.com/storax/reddel-server/issues

.. |license| image:: https://img.shields.io/github/license/storax/reddel-server.svg
    :alt: License
    :target:  https://github.com/storax/reddel-server/blob/master/LICENSE

.. |docs| image:: https://readthedocs.org/projects/reddel-server/badge/?style=flat
    :target: http://reddel-server.readthedocs.io/en/latest/
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/storax/reddel-server.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/storax/reddel-server

.. |coveralls| image:: https://coveralls.io/repos/storax/reddel-server/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/github/storax/reddel-server

.. |version| image:: https://img.shields.io/pypi/v/reddel-server.svg?style=flat
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/reddel-server

.. |downloads| image:: https://img.shields.io/pypi/dm/reddel-server.svg?style=flat
    :alt: PyPI Package monthly downloads
    :target: https://pypi.python.org/pypi/reddel-server

.. |wheel| image:: https://img.shields.io/pypi/wheel/reddel-server.svg?style=flat
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/reddel-server

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/reddel-server.svg?style=flat
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/reddel-server

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/reddel-server.svg?style=flat
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/reddel-server

.. |status| image:: https://img.shields.io/pypi/status/reddel-server.svg?style=flat
    :alt: Project Status
    :target: https://pypi.python.org/pypi/reddel-server

.. end-badges

.. contents:: Table of Contents
    :local:

`Python EPC server component <http://python-epc.readthedocs.io/en/latest/>`_ for
`reddel <https://github.com/storax/reddel-server>`_.
It provides an easy way to send (python) source code from Emacs to the server,
inspect or transform it via `Redbaron <http://redbaron.readthedocs.io/en/latest/>`_ and send the result back.

An example on how to expose a simple function to add arguments::

  # file: myprovidermod.py
  import reddel_server

  class MyProvider(reddel_server.ProviderBase)
      @reddel_server.red_src()
      @reddel_server.red_validate([reddel_server.OptionalRegionValidator(),
                                   reddel_server.SingleNodeValidator(),
                                   reddel_server.TypeValidator(["def"])])
      def add_arg(self, red, start, end, index, arg):
          red.arguments.insert(index, arg)
          return red

Start the reddel server from Emacs::

  >>> (require 'epc)

  >>> (defvar my-epc (epc:start-epc "reddel" nil))

  >>> ;; make sure myprovidermod is in a directory within the PYTHONPATH
  >>> (epc:call-sync my-epc 'add_provider '("myprovidermod.MyProvider"))

  >>> (message (epc:call-sync my-epc 'add_arg '("def foo(arg1, arg3): pass" nil nil 1 "arg2")))
  "def foo(arg1, arg2, arg3): pass"

Redbaron provides a lossless format, so even formatting and comments are preserved.

Installation
============

At the command line::

    pip install reddel-server

Usage
=====

You can start a reddel server from within Emacs like shown above or start it from the command line.
A executable ``reddel`` is provided by this project, which should suitable for most use cases.
::

  $ reddel --help
  Usage: reddel [OPTIONS]

  Options:
    --address TEXT       address to bind the server to
    --port INTEGER       address to bind the server to
    -p, --provider TEXT  dotted path to a provider class
    -v, --verbosity LVL  Either CRITICAL, ERROR, WARNING, INFO or DEBUG
    --debug              Show tracebacks when erroring.
    --help               Show this message and exit.

.. list-table::

    * - ``--address TEXT``
      - Default is ``localhost``. Can be an IP or domain name.
    * - ``--port INTEGER``
      - Defaults to a random free port.
    * - ``-p, --provider TEXT``
      - Example: ``mypkg.mymod.MyProviderClass``
        You can provide this multiple times.
        Defines additional providers that are available from the start.
        More providers can be added at runtime via ``reddel_server.ChainedProvider.add_provider``.
    * - ``-v, --verbosity LVL``
      - Define the logging level.
    * - ``--debug``
      - By default all expected exceptions are only logged without the traceback.
        If this flag is set, the traceback is printed as well.
    * - ``--help``
      - Show the help message and exit.

Calling a function from within Emacs is very simple thanks to `epc <https://github.com/kiwanami/emacs-epc>`_::

    >>> (progn
    ...   (require 'epc)
    ...   (defvar my-epc (epc:start-epc "reddel" nil))
    ...   ;; list all methods compatible with the given source
    ...   (message (epc:call-sync my-epc 'list_methods '("def foo(arg1, arg3): pass"))))

``(epc:start-epc "reddel" nil)`` starts the server by executing ``reddel`` without any arguments (``nil``).
Then you can make calls to that server by referring to the manager returned from ``epc:start-epc``.
To execute a call, you can use ``(epc:call-sync <manager> <method> <arguments>)``,
where ``<manager>`` is the manager returned by ``epc:start-epc``, ``<method>`` is the function
and ``<arguments>`` is a list of arguments passed to ``<method>``.

The Builtin Functions section in the documentation provides a guide through all functions that ship with this package.
If you need advanced features check the reference documentation for help on how to write your own server.

Documentation
=============

https://reddel-server.readthedocs.io/

Bugs/Requests
=============

Please use the `GitHub issue tracker <https://github.com/storax/reddel-server/issues>`_ to submit bugs or request features.

Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox

License
=======

Copyright David Zuber, 2016.

Distributed under the terms of the `GNU General Public License version 3 <https://github.com/storax/reddel-server/blob/master/LICENSE>`_,
reddel-server is free and open source software.
