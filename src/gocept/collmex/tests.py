# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

import unittest
import zope.testing.doctest


def test_suite():
    suite = zope.testing.doctest.DocFileSuite(
        'README.txt',
        )
    return suite
