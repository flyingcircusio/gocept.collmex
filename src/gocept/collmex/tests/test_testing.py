# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

import mock
import unittest


def get_env_value(key):
    mock_data = dict(collmex_customer='123',
                     collmex_company='456',
                     collmex_username='ben.utzer',
                     collmex_password='asdf')
    return mock_data[key]


class TestGetCollmex(unittest.TestCase):

    @mock.patch('os.environ.__getitem__', get_env_value)
    def test_reads_data_from_environment(self):
        import gocept.collmex.testing
        collmex = gocept.collmex.testing.get_collmex()
        self.assertEqual('123', collmex.customer_id)
        self.assertEqual('456', collmex.company_id)
        self.assertEqual('ben.utzer', collmex.username)
        self.assertEqual('asdf', collmex.password)

    @mock.patch('os.environ.__getitem__', get_env_value)
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
        gocept.collmex.testing.create_projects()
        collmex = gocept.collmex.testing.get_collmex()
        self.assertEqual(
            ['TEST'],
            [prod['Produktnummer'] for prod in collmex.get_products()])


class TestCreateActivity(unittest.TestCase):

    def setUp(self):
        import gocept.collmex.testing
        gocept.collmex.testing.cleanup_collmex()

    def test_create_activity(self):
        import gocept.collmex.testing
        gocept.collmex.testing.create_activity()
        collmex = gocept.collmex.testing.get_collmex()
        self.assertEqual(
            'Typkennung;Projekt;Mitarbeiter;Firma;Satz;Beschreibung;Datum;Von;'
            'Bis;Pausen\r\nCMXACT;1 Testprojekt;1 Sebastian Wehrmann;1 gocept '
            'apitest;1 Testprodukt;allgemeine T\xe4tigkeit;20120123;08:07;14:'
            '28;1:12\r\n', collmex.get_activities())
