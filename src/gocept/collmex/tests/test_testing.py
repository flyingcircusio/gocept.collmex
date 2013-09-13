# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

from __future__ import unicode_literals
import mock
import unittest


mock_data = dict(collmex_customer='123',
                 collmex_company='456',
                 collmex_username='ben.utzer',
                 collmex_password='asdf')


class TestGetCollmex(unittest.TestCase):

    @mock.patch.dict('os.environ', mock_data)
    def test_reads_data_from_environment(self):
        import gocept.collmex.testing
        collmex = gocept.collmex.testing.get_collmex()
        self.assertEqual('123', collmex.customer_id)
        self.assertEqual('456', collmex.company_id)
        self.assertEqual('ben.utzer', collmex.username)
        self.assertEqual('asdf', collmex.password)

    @mock.patch.dict('os.environ', mock_data)
    def test_keyword_args_override_data_from_environment(self):
        import gocept.collmex.testing
        collmex = gocept.collmex.testing.get_collmex(password='qwertz')
        self.assertEqual('123', collmex.customer_id)
        self.assertEqual('456', collmex.company_id)
        self.assertEqual('ben.utzer', collmex.username)
        self.assertEqual('qwertz', collmex.password)


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
