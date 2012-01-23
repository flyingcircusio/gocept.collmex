# Copyright (c) 2008-2012 gocept gmbh & co. kg
# See also LICENSE.txt

import zope.testing.doctest


optionflags = (zope.testing.doctest.INTERPRET_FOOTNOTES |
               zope.testing.doctest.NORMALIZE_WHITESPACE |
               zope.testing.doctest.ELLIPSIS)


def test_suite():
    return zope.testing.doctest.DocFileSuite(
        'README.txt',
        package='gocept.collmex',
        optionflags=optionflags)
