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
