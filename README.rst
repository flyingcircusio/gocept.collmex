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


Faux Collmex server
===================

``gocept.collmex.faux`` provides an in-memory server that mimics the parts of
the Collmex HTTP interface this package uses, including the CSV API and some
basic HTML/Forms to emulate resetting the environment.

The faux server is available as the session-scoped pytest fixture
``faux_collmex``. To use it in a project, import it in your
``conftest.py`` so pytest picks it up::

    from gocept.collmex.faux import faux_collmex  # noqa: F401

and request it in your tests::

    def test_create_product(faux_collmex):
        ...

The fixture becomes a no-op when the environment variable ``COLLMEX_FAUX=0``
or ``COLLMEX_TEST_LIVE=1`` is set (tests shall run against the live
Collmex test system), or when ``COLLMEX_API_URL`` is already set (it is
left alone, e.g. to run against an externally started faux server).


Development
===========

We use `uv <https://docs.astral.sh/uv/>`_ and tox for development. To run the
tests::

    uvx --from tox --with tox-uv tox

or, to run a specific environment::

    uvx --from tox --with tox-uv tox -e py313

To build the distribution, use ``uv build``.

The changelog is managed with `scriv <https://scriv.readthedocs.io>`_:
for each user-visible change, run ``uv run scriv create``, edit the
fragment created in ``changelog.d/``, and commit it together with your
change (this avoids merge conflicts in ``CHANGES.rst``).

Releases are made with `zest.releaser
<https://zestreleaser.readthedocs.io>`_ via ``uv run fullrelease``. It
collects the fragments into ``CHANGES.rst`` with the release version
automatically.


Testing
=======

By default, the test suite runs against the faux Collmex server shipped
with this package, see `Faux Collmex server`_. It is wired autouse in
``conftest.py`` and needs no configuration.

To run the tests against the **live Collmex test system** instead (see
``collmex.ini-example``), set both ``COLLMEX_FAUX=0`` and
``COLLMEX_TEST_LIVE=1``. The easiest way is the dedicated tox environment
(Python 3.12)::

    uvx --from tox --with tox-uv tox -e py312-live

The live test system is a shared resource: concurrent test runs delete each
other's data and can lock the test account (some tests deliberately use
invalid credentials). Therefore, serialise all test runs that use it.
