========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis|
        | |coveralls|
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

Python EPC server for reddel.

* Free software: BSD license

Installation
============

::

    pip install reddel-server

Documentation
=============

https://reddel-server.readthedocs.io/

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
