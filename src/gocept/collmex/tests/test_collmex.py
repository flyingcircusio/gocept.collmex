# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

import unittest


class TestCollmex(unittest.TestCase):

    def test_invalid_login_information_raises_an_exception(self):
        import gocept.collmex.collmex
        import gocept.collmex.testing

        collmex_invalid = gocept.collmex.testing.get_collmex(
            password='invalid')
        with self.assertRaises(gocept.collmex.collmex.APIError) as err:
            collmex_invalid.get_invoices(customer_id='10000')
        self.assertEqual("('101004', 'Benutzer oder Kennwort nicht korrekt')",
                         str(err.exception))

    def test_browser_login_authenticates_user_using_browser(self):
        import gocept.collmex.testing
        collmex = gocept.collmex.testing.get_collmex()
        browser = collmex.browser_login()
        self.assertTrue(
            browser.getLink('Projekt-Verbrauch').url.endswith(',vbrp'))
