- Modernise packaging: use ``pyproject.toml`` (PEP 621) instead of
  ``setup.py`` and ``setup.cfg``.

- Convert ``gocept`` to a native (PEP 420) namespace package, this removes
  the runtime dependency on ``pkg_resources``/``setuptools``.

- Use uv instead of pip for development, building and CI.

- Drop support for Python 3.7 - 3.10.

- Add support for Python 3.12, 3.13, 3.14 and 3.15.
