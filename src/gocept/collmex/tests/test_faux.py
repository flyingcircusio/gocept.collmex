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

    def test_product_groups_can_be_created_and_queried(self):
        collmex = self.make_collmex()
        main = gocept.collmex.model.ProductGroup()
        main["Produktgruppe Nr"] = "1"
        main["Bezeichnung"] = "Hauptproduktgruppe"
        collmex.create(main)
        group = gocept.collmex.model.ProductGroup()
        group["Produktgruppe Nr"] = "2"
        group["Bezeichnung"] = "Testproduktgruppe"
        group["Untergruppe von"] = "1"
        collmex.create(group)
        transaction.commit()
        groups = collmex.get_product_groups()
        self.assertEqual(
            ["Hauptproduktgruppe", "Testproduktgruppe"],
            [group["Bezeichnung"] for group in groups],
        )
        self.assertEqual(
            ["1"],
            [
                group["Untergruppe von"]
                for group in groups
                if group["Bezeichnung"] == "Testproduktgruppe"
            ],
        )

    def test_product_group_replaces_record_with_same_key(self):
        collmex = self.make_collmex()
        group = gocept.collmex.model.ProductGroup()
        group["Produktgruppe Nr"] = "1"
        group["Bezeichnung"] = "Alt"
        collmex.create(group)
        group = gocept.collmex.model.ProductGroup()
        group["Produktgruppe Nr"] = "1"
        group["Bezeichnung"] = "Neu"
        collmex.create(group)
        transaction.commit()
        self.assertEqual(
            ["Neu"],
            [prod["Bezeichnung"] for prod in collmex.get_product_groups()],
        )

    def test_product_group_drops_non_numeric_parent(self):
        collmex = self.make_collmex()
        group = gocept.collmex.model.ProductGroup()
        group["Produktgruppe Nr"] = "1"
        group["Bezeichnung"] = "Testproduktgruppe"
        group["Untergruppe von"] = "Hauptproduktgruppe"
        collmex.create(group)
        transaction.commit()
        [group] = collmex.get_product_groups()
        self.assertIsNone(group["Untergruppe von"])

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

    def test_quantities_are_rendered_with_their_units_decimals(self):
        format_quantity = gocept.collmex.faux.format_quantity
        # Predefined units render with their default decimal places:
        self.assertEqual("2", format_quantity("2,00", "PCE"))  # Stück
        self.assertEqual("2,0", format_quantity("2", "MON"))  # Monat
        self.assertEqual("2,00", format_quantity("2", "HR"))  # Stunden
        self.assertEqual("2,000", format_quantity("2", "KGM"))  # Kilo.
        # Unknown (custom) units fall back to two decimals:
        self.assertEqual("2,00", format_quantity("2", "XYZ"))

    def test_invoice_export_fills_unit_from_product(self):
        collmex = self.make_collmex()
        self.create_product(collmex, unit="PCE")
        self.create_customer(collmex)
        item = gocept.collmex.model.InvoiceItem()
        item["Kunden-Nr"] = "10000"
        item["Produktnummer"] = "TEST"
        item["Menge"] = "2,00"
        collmex.create_invoice([item])
        transaction.commit()
        [invoice] = collmex.get_invoices()
        # The unit is filled in from the product's base unit, and the
        # quantity is rendered with the unit's decimal places, like
        # Collmex does (CMXINV fields 72 and 73):
        self.assertEqual("PCE", invoice["Mengeneinheit"])
        self.assertEqual("2", invoice["Menge"])

    def test_invoice_export_renders_quantity_of_sent_unit(self):
        collmex = self.make_collmex()
        self.create_customer(collmex)
        item = gocept.collmex.model.InvoiceItem()
        item["Kunden-Nr"] = "10000"
        item["Produktnummer"] = "TEST"
        item["Mengeneinheit"] = "PCE"
        item["Menge"] = "3,00"
        collmex.create_invoice([item])
        transaction.commit()
        [invoice] = collmex.get_invoices()
        self.assertEqual("PCE", invoice["Mengeneinheit"])
        self.assertEqual("3", invoice["Menge"])

    def test_invoice_export_renders_hours_with_two_decimals(self):
        collmex = self.make_collmex()
        self.create_product(collmex, unit="HR")
        self.create_customer(collmex)
        item = gocept.collmex.model.InvoiceItem()
        item["Kunden-Nr"] = "10000"
        item["Produktnummer"] = "TEST"
        item["Menge"] = 3
        collmex.create_invoice([item])
        transaction.commit()
        [invoice] = collmex.get_invoices()
        self.assertEqual("HR", invoice["Mengeneinheit"])
        self.assertEqual("3,00", invoice["Menge"])

    def test_product_export_defaults_preismenge_to_one(self):
        collmex = self.make_collmex()
        product = gocept.collmex.model.Product()
        product["Produktnummer"] = "TEST"
        product["Verkaufs-Preis"] = 5
        collmex.create(product)
        transaction.commit()
        [exported] = collmex.get_products()
        # Collmex defaults the price quantity to 1 (CMXPRD field 11):
        self.assertEqual("1", exported["Preismenge"])

    def test_product_export_keeps_explicit_preismenge(self):
        collmex = self.make_collmex()
        product = gocept.collmex.model.Product()
        product["Produktnummer"] = "TEST"
        product["Preismenge"] = 2
        collmex.create(product)
        transaction.commit()
        [exported] = collmex.get_products()
        self.assertEqual("2", exported["Preismenge"])

    # -- Helpers -------------------------------------------------------

    def create_product(self, collmex, unit="HR"):
        product = gocept.collmex.model.Product()
        product["Produktnummer"] = "TEST"
        product["Bezeichnung"] = "Testprodukt"
        product["Basismengeneinheit"] = unit
        collmex.create(product)

    def create_customer(self, collmex):
        customer = gocept.collmex.model.Customer()
        customer["Kundennummer"] = 10000
        customer["Firma"] = "Testkunden"
        collmex.create(customer)

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
