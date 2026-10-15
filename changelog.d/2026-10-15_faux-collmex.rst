- New: ship a faux Collmex server (``gocept.collmex.faux``) that mimics
  the data exchange API and the HTML pages used by the test helpers.
  It is provided as the session-scoped pytest fixture
  ``faux_collmex`` (to be imported in ``conftest.py``), so test suites
  of ``gocept.collmex`` and of dependent projects can run without
  access to the Collmex test system. Set ``COLLMEX_FAUX=0`` and
  ``COLLMEX_TEST_LIVE=1`` (or use the new ``py3xx-live`` tox
  environments) to run against the live Collmex test system instead.

- New: the Collmex base URL can be overridden with the
  ``COLLMEX_API_URL`` environment variable.

- CI: the test workflow declares a ``concurrency`` group so pushes,
  pull requests and scheduled runs cannot use the shared Collmex test
  system at the same time. The live test runs in a dedicated
  ``py312-live`` environment; the other environments use the faux
  server and no longer need the decrypted ``collmex.ini``.
