# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

from __future__ import unicode_literals
import unittest


class TestCreateProjects(unittest.TestCase):

    def setUp(self):
        import gocept.collmex.testing
        gocept.collmex.testing.cleanup_collmex()

    def test_creates_product_if_missing(self):
        import gocept.collmex.testing
        gocept.collmex.testing.create_project('project title')
        collmex = gocept.collmex.testing.get_collmex()
        self.assertEqual(
            ['TEST'],
            [prod['Produktnummer'] for prod in collmex.get_products()])
