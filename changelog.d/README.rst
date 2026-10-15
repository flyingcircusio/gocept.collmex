Changelog fragments
===================

This directory contains unreleased changelog fragments, managed by
`scriv <https://scriv.readthedocs.io>`_. Each fragment describes one
change (usually one per pull request) and gets merged into
``CHANGES.rst`` at release time.

Workflow
--------

* When you make a user-visible change, run::

      uv run scriv create

  and edit the created file in this directory. Commit it together with
  your change.

* When releasing, ``uv run fullrelease`` (zest.releaser) collects all
  fragments into ``CHANGES.rst`` automatically. To only collect them
  manually, run::

      uv run scriv collect
