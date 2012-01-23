# Copyright (c) 2008-2012 gocept gmbh & co. kg
# See also LICENSE.txt

import gocept.collmex.interfaces
import gocept.collmex.model
import unittest
import zope.interface


class TestModel(gocept.collmex.model.Model):

    zope.interface.implements(gocept.collmex.interfaces.IInvoiceItem)

    satzart = 'CMXINV'
    fields = (
        'Satzart',
        'Rechnungsnummer',
    )


class ModelTest(unittest.TestCase):

    def test_model_robust_against_extension(self):
        tm = TestModel(['CMXINV', 'foo', 'bar', ''])
        self.assertEqual('foo', tm['Rechnungsnummer'])
        self.assertEqual(['bar', None], tm._unmapped)
