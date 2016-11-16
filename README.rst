=============
Reddel-Server
=============

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - |travis| |coveralls|
    * - package
      - |version| |downloads| |wheel| |supported-versions| |supported-implementations|

.. |docs| image:: https://readthedocs.org/projects/reddel-server/badge/?style=flat
    :target: https://readthedocs.org/projects/reddel-server
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


.. end-badges

`Python EPC server component <http://python-epc.readthedocs.io/en/latest/>`_ for reddel.
It provides an easy way to send (python) source code from Emacs to the server,
inspect or transform it via `Redbaron <http://redbaron.readthedocs.io/en/latest/>`_ and send the result back.

An example on how to expose a simple function to add arguments::

  # file: myprovidermod.py
  import reddel_server

  class MyProvider(reddel_server.ProviderBase)
      @reddel_server.red_src()
      @reddel_server.red_type(["def"])
      def add_arg(self, red, index, arg):
          red.arguments.insert(index, arg)
          return red

Start the reddel server from Emacs::

  (require 'epc)

  (defvar my-epc (epc:start-epc "reddel" nil))

  ;; make sure myprovidermod is in a directory within the PYTHONPATH
  (epc:call-sync my-epc 'add_provider '("myprovidermod.MyProvider"))

  (message (epc:call-sync my-epc 'add_arg '("def foo(arg1, arg3): pass" 1 "arg2")))
  >> def foo(arg1, arg2, arg3): pass 

Redbaron provides a lossless format, so even formatting and comments are preserved.

Installation
============

At the command line::

    pip install reddel-server

Usage
=====

You can start a reddel server from within Emacs like shown above or start it from the command line.
A executable ``reddel`` is provided by this project, which should suitable for most usecases.
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

If you need advanced features check the `reference guide <reference/index>`_.

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
