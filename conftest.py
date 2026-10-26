import pytest

from gocept.collmex.faux import faux_collmex

__all__ = ("faux_collmex",)


@pytest.fixture(autouse=True)
def faux_collmex_auto(faux_collmex):
    """Run all tests of this package against the faux Collmex server.

    The fixture is a no-op when ``COLLMEX_TEST_LIVE`` is set (or
    ``COLLMEX_FAUX=0``), in which case the tests run against the live
    Collmex test system instead.
    """
