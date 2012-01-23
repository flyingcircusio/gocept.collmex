# Copyright (c) 2008-2012 gocept gmbh & co. kg
# See also LICENSE.txt

import doctest


def test_suite():
    return doctest.DocFileSuite(
        'README.txt',
        package='gocept.collmex',
        optionflags=(doctest.NORMALIZE_WHITESPACE |
                     doctest.ELLIPSIS))
