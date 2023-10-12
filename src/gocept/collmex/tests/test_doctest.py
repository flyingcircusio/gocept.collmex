import doctest
from zope.testing import renormalizing
import re

checker = renormalizing.RENormalizing([
    # Ignore output returned by GHA for PyPy3
    (re.compile('/etc/ssl/certs/ca-certificates.crt /etc/ssl/certs'), ''),
])


def test_suite():
    return doctest.DocFileSuite('../doctest.rst', checker=checker)
