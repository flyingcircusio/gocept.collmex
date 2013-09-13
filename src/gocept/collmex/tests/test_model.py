# Copyright (c) 2008-2012 gocept gmbh & co. kg
# See also LICENSE.txt

from __future__ import unicode_literals
import gocept.collmex.interfaces
import gocept.collmex.model
import unittest
from zope.interface import implementer


@implementer(gocept.collmex.interfaces.IInvoiceItem)
class TestModel(gocept.collmex.model.Model):

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
