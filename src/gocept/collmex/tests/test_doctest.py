# Copyright (c) 2008-2012 gocept gmbh & co. kg
# See also LICENSE.txt

import doctest
import six


def test_suite():
    file = 'py27_doctest.txt'
    if six.PY3:
        file = 'py32_doctest.txt'
    return doctest.DocFileSuite(
        file,
        package='gocept.collmex',
        optionflags=(doctest.NORMALIZE_WHITESPACE |
                     doctest.ELLIPSIS))
