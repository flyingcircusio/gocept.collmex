.. contents::

.. image:: https://github.com/gocept/gocept.collmex/workflows/tests/badge.svg
           :target: https://github.com/gocept/gocept.collmex/actions?query=workflow%3Atests
.. image:: https://coveralls.io/repos/github/gocept/gocept.collmex/badge.svg?branch=master
           :target: https://coveralls.io/github/gocept/gocept.collmex?branch=master
.. image:: https://img.shields.io/pypi/v/gocept.collmex.svg
           :target: https://pypi.org/project/gocept.collmex/
           :alt: Current version on PyPI
.. image:: https://img.shields.io/pypi/pyversions/gocept.collmex.svg
           :target: https://pypi.org/project/gocept.collmex/
           :alt: Supported Python versions


Introduction
============

Collmex is an online ERP system for (small) companies with a focus on simple
accounting. <http://www.collmex.de> (Note: Collmex is Germany-based but seems
to support English. You're bound to stumble over German strings, though.)

This package aims to provide pythonic bindings to program against Collmex'
API. It includes transaction management for integration with the ZODB or other
databases that can integrate with the `transaction` package.


Credentials
===========

To initialize a connection to the collmex server, login-credentials are required. These can be given explicitely when the ``gocept.collmex.collmex.Collmex`` object is created or via an ini file named ``collmex.ini``.
The ini file must live in the project directory or any of it's parent directories, e.g. it is possible to place ``collmex.ini`` in your home directory to use those credentials for all of your projects.
The ini file must contain the section ``[credentials]`` for production and ``[test-credentials]`` for testing purposes.
Each section must have the following options: ``customer_id``, ``company_id``, ``username`` and ``password``.
The file ``collmex.ini-example`` can be used as a template.

Example::

    [credentials]
    customer_id = 42555
    company_id = 1
    username = realuser
    password = realpassword

    [test-credentials]
    customer_id = 41222
    company_id = 1
    username = testuser
    password = testpassword
