import unittest
from unittest import mock

import transaction
import webtest

import gocept.collmex.collmex
import gocept.collmex.faux
import gocept.collmex.model

CREDENTIALS = {
    "customer_id": "10001",
    "company_id": "1",
    "username": "fauxuser",
    "password": "fauxpassword",
}


class FauxServerTest(unittest.TestCase):
    """Direct tests of the faux server.

    (The rest of this package's test suite runs against a faux server
    implicitly via the autouse fixture in conftest.py.)
    """

    def setUp(self):
        self.server = gocept.collmex.faux.start_server(
            credentials=dict(CREDENTIALS)
        )
        patcher = mock.patch.dict(
            "os.environ", {"COLLMEX_API_URL": self.server.url}
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        gocept.collmex.faux.stop_server(self.server)
        transaction.abort()

    def make_collmex(self, username=None, password=None):
        return gocept.collmex.collmex.Collmex(
            CREDENTIALS["customer_id"],
            CREDENTIALS["company_id"],
            username or CREDENTIALS["username"],
            password or CREDENTIALS["password"],
        )

    def test_invalid_login_raises_APIError(self):
        collmex = self.make_collmex(username="invalid")
        with self.assertRaises(gocept.collmex.collmex.APIError) as err:
            collmex.get_customers()
        self.assertEqual(
            ("101004", "Benutzer oder Kennwort nicht korrekt"),
            err.exception.args,
        )

    def test_unknown_satzart_raises_APIError(self):
        collmex = self.make_collmex()
        with self.assertRaises(gocept.collmex.collmex.APIError) as err:
            collmex._post("FROBNICATE;1\n")
        self.assertEqual(
            ("105001", "Satzart nicht definiert: FROBNICATE"),
            err.exception.args,
        )

    def test_records_can_be_created_and_queried(self):
        collmex = self.make_collmex()
        customer = gocept.collmex.model.Customer()
        customer["Kundennummer"] = 10000
        customer["Firma"] = "Testkunden"
        collmex.create(customer)
        transaction.commit()
        # The generic customer 9999 is always present, after it the
        # newly created one:
        self.assertEqual(
            ["Allgemeiner Geschäftspartner", "Testkunden"],
            [cust["Firma"] for cust in collmex.get_customers()],
        )

    def test_create_replaces_record_with_same_key(self):
        collmex = self.make_collmex()
        product = gocept.collmex.model.Product()
        product["Produktnummer"] = "TEST"
        product["Bezeichnung"] = "Alt"
        collmex.create(product)
        transaction.commit()
        product = gocept.collmex.model.Product()
        product["Produktnummer"] = "TEST"
        product["Bezeichnung"] = "Neu"
        collmex.create(product)
        transaction.commit()
        self.assertEqual(
            ["Neu"], [prod["Bezeichnung"] for prod in collmex.get_products()]
        )

    def test_only_changed_reports_new_records(self):
        collmex = self.make_collmex()
        self.assertEqual([], collmex.get_invoices(only_changed=1))
        item = gocept.collmex.model.InvoiceItem()
        item["Kunden-Nr"] = "10000"
        item["Menge"] = 1
        collmex.create_invoice([item])
        transaction.commit()
        self.assertEqual(1, len(collmex.get_invoices(only_changed=1)))

    def test_numbers_are_exported_with_decimal_comma(self):
        self.assertEqual("9,65", gocept.collmex.faux.format_number(9.65))
        self.assertEqual(9.65, gocept.collmex.faux.parse_number("9,65"))

    def test_dates_are_normalised_to_D8(self):
        self.assertEqual(
            "20120101", gocept.collmex.faux.format_date("2012-01-01")
        )
        self.assertEqual(
            "20120101", gocept.collmex.faux.format_date("20120101")
        )

    def test_browser_login_flow(self):
        browser = webtest.TestApp(self.server.url)
        b = browser.get("/")
        b.charset = "windows-1252"
        f = b.form
        f["Kunde"] = CREDENTIALS["customer_id"]
        b = f.submit().maybe_follow()
        b.charset = "windows-1252"
        f = b.form
        f["group_benutzerId"] = "wrong"
        f["group_kennwort"] = "wrong"
        b = f.submit().maybe_follow()
        b.charset = "windows-1252"
        self.assertIn("Benutzer oder Kennwort nicht korrekt", b.unicode_body)

        f = b.form
        f["group_benutzerId"] = CREDENTIALS["username"]
        f["group_kennwort"] = CREDENTIALS["password"]
        b = f.submit().maybe_follow()
        b.charset = "windows-1252"
        [link] = [s for s in b.html.find_all("a") if "Projekt-Verbrauch" in s]
        self.assertTrue(link.get("href").endswith(",vbrp"))
