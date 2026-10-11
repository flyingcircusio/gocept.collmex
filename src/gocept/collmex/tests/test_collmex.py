import unittest
from unittest import mock

import pytest


class TestCollmex(unittest.TestCase):
    def setUp(self):
        import gocept.collmex.testing

        gocept.collmex.testing.cleanup_collmex()

    def tearDown(self):
        self.collmex.browser_login()  # reset invalid login counter

    @property
    def collmex(self):
        import gocept.collmex.testing

        return gocept.collmex.testing.get_collmex()

    @mock.patch.dict(
        "os.environ", {"collmex_credential_section": "non-existing-credentials"}
    )
    def test_missing_login_information_raises_an_exception(self):
        import gocept.collmex.collmex

        with self.assertRaises(ValueError):
            gocept.collmex.collmex.Collmex()

    def test_invalid_login_information_raises_an_exception_via_API(self):
        import gocept.collmex.collmex
        import gocept.collmex.testing

        # We need an invalid username too, as we get a different error on too
        # many wrong password attempts.
        collmex_invalid = gocept.collmex.testing.get_collmex(
            username="invalid", password="invalid"
        )
        with self.assertRaises(gocept.collmex.collmex.APIError) as err:
            collmex_invalid.get_invoices(customer_id="10000")
        self.assertEqual(
            ("101004", "Benutzer oder Kennwort nicht korrekt"),
            err.exception.args,
        )

    def test_invalid_login_information_raises_an_exception_via_browser(self):
        import gocept.collmex.testing

        # We need an invalid username too, as we get a different error on too
        # many wrong password attempts.
        collmex_invalid = gocept.collmex.testing.get_collmex(
            username="invalid", password="invalid"
        )
        with self.assertRaises(ValueError) as err:
            collmex_invalid.browser_login()
        self.assertIn(
            "Benutzer oder Kennwort nicht korrekt", err.exception.args[0]
        )

    def test_browser_login_authenticates_user_using_browser(self):
        browser = self.collmex.browser_login()
        links = browser.html.find_all("a")
        [link] = [s for s in links if "Projekt-Verbrauch" in s]
        self.assertTrue(link.get("href").endswith(",vbrp"))

    def test_get_activities_should_support_passing_project_id(self):
        import datetime

        import transaction

        import gocept.collmex.testing

        gocept.collmex.testing.create_employee()
        gocept.collmex.testing.create_project(title="Testprojekt")
        gocept.collmex.testing.create_project(title="Projektil")
        gocept.collmex.testing.create_activity(
            "Activity in test project",
            project_id="1",
            employee_id="1",
            date=datetime.date(2012, 1, 1),
        )
        gocept.collmex.testing.create_activity(
            "Activity in projektil",
            project_id="2",
            employee_id="1",
            date=datetime.date(2012, 1, 2),
        )
        transaction.commit()
        activities = self.collmex.get_activities(project_id="2")
        self.assertEqual(1, len(activities))

    def test_get_activities_should_convert_dates(self):
        import datetime

        import transaction

        import gocept.collmex.testing

        gocept.collmex.testing.create_employee()
        gocept.collmex.testing.create_project(title="Testprojekt")
        gocept.collmex.testing.create_activity(
            "Activity in test project",
            project_id="1",
            employee_id="1",
            date=datetime.date(2012, 1, 1),
        )
        transaction.commit()
        activities = self.collmex.get_activities(
            start_date=datetime.date(2012, 1, 1),
            end_date=datetime.date(2012, 1, 31),
        )
        self.assertEqual(1, len(activities))
        self.assertEqual(
            "Activity in test project", activities[0]["Beschreibung"]
        )

    def test_get_activities_should_support_only_changed(self):
        import datetime

        import transaction

        import gocept.collmex.testing

        gocept.collmex.testing.create_employee()
        gocept.collmex.testing.create_project(title="Testprojekt")
        gocept.collmex.testing.create_activity(
            "Activity in test project",
            project_id="1",
            employee_id="1",
            date=datetime.date(2012, 1, 1),
        )
        transaction.commit()
        # Use a dedicated system identifier so only this test advances
        # the corresponding watermark:
        collmex = gocept.collmex.testing.get_collmex(
            system_identifier="test-only-changed"
        )
        changed = collmex.get_activities(only_changed=1)
        self.assertIn(
            "Activity in test project",
            [activity["Beschreibung"] for activity in changed],
        )

    def test_get_activities_maps_all_columns_of_live_response(self):
        import datetime

        import transaction

        import gocept.collmex.testing

        gocept.collmex.testing.create_employee()
        gocept.collmex.testing.create_project(title="Testprojekt")
        gocept.collmex.testing.create_activity(
            "Activity in test project",
            project_id="1",
            employee_id="1",
            date=datetime.date(2012, 1, 1),
        )
        transaction.commit()
        activities = self.collmex.get_activities(project_id="1")
        self.assertEqual(1, len(activities))
        # The export-only fields are mapped instead of landing in
        # _unmapped:
        self.assertEqual([], activities[0]._unmapped)
        self.assertEqual("TEST", activities[0]["Produkt Nr"])
        self.assertIsNone(activities[0]["In Rechnung Nr"])

    def _create_invoice(self, collmex, text):
        import gocept.collmex.model
        import gocept.collmex.testing

        gocept.collmex.testing.create_customer()
        gocept.collmex.testing.create_product()
        item = gocept.collmex.model.InvoiceItem()
        item["Kunden-Nr"] = "10000"
        item["Menge"] = 3
        item["Produktnummer"] = "TEST"
        item["Rechnungstext"] = text
        item["Positionstyp"] = 0
        collmex.create_invoice([item])
        import transaction

        transaction.commit()

    def test_get_invoices_should_support_only_changed(self):
        import transaction

        import gocept.collmex.testing

        self._create_invoice(self.collmex, "only changed 1")

        collmex = gocept.collmex.testing.get_collmex(
            system_identifier="test-only-changed"
        )
        # The system identifier was not used for a while (or never),
        # so the new invoice counts as changed:
        changed = collmex.get_invoices(only_changed=1)
        self.assertEqual(
            ["only changed 1"], [item["Rechnungstext"] for item in changed]
        )
        transaction.abort()  # discard query cache

        # An invoice created after the last query is reported as
        # changed. (Collmex stores the watermark with minute
        # granularity and asynchronously, so records changed in the
        # same minute as the query may be reported again -- we only
        # assert the reliable part.)
        self._create_invoice(collmex, "only changed 2")
        changed = collmex.get_invoices(only_changed=1)
        self.assertIn(
            "only changed 2", [item["Rechnungstext"] for item in changed]
        )

    def test_get_invoices_maps_all_columns_of_live_response(self):
        self._create_invoice(self.collmex, "invoice mapping")
        invoices = self.collmex.get_invoices()
        self.assertEqual(1, len(invoices))
        self.assertEqual([], invoices[0]._unmapped)
        self.assertEqual("invoice mapping", invoices[0]["Rechnungstext"])

    def test_get_activities_should_pass_all_parameters(self):
        import datetime

        collmex = self.collmex
        query = collmex._query_objects = mock.Mock()
        collmex.get_activities(
            project_id=mock.sentinel.project_id,
            employee_id=mock.sentinel.employee_id,
            start_date=datetime.date(2026, 1, 23),
            end_date=datetime.date(2026, 2, 28),
            only_non_billed=mock.sentinel.only_non_billed,
            billable=mock.sentinel.billable,
            only_non_internal=mock.sentinel.only_non_internal,
            only_changed=mock.sentinel.only_changed,
        )
        query.assert_called_with(
            "ACTIVITIES_GET",
            mock.sentinel.project_id,
            "1",  # Company id
            mock.sentinel.employee_id,
            "20260123",  # start date, converted to Collmex' D8 format
            "20260228",  # end date, converted to Collmex' D8 format
            mock.sentinel.only_non_billed,
            mock.sentinel.billable,
            mock.sentinel.only_non_internal,
            mock.sentinel.only_changed,
            "gocept.collmex",
        )  # system identifier

    def test_get_invoices_should_pass_all_parameters(self):
        import datetime

        collmex = self.collmex
        query = collmex._query_objects = mock.Mock()
        collmex.get_invoices(
            invoice_id=mock.sentinel.invoice_id,
            customer_id=mock.sentinel.customer_id,
            start_date=datetime.date(2026, 1, 23),
            end_date=datetime.date(2026, 2, 28),
            only_changed=mock.sentinel.only_changed,
        )
        query.assert_called_with(
            "INVOICE_GET",
            mock.sentinel.invoice_id,
            "1",  # Company id
            mock.sentinel.customer_id,
            "20260123",  # start date, converted to Collmex' D8 format
            "20260228",  # end date, converted to Collmex' D8 format
            0,  # Nur ausgegebene
            0,  # Rueckgabe-Format
            mock.sentinel.only_changed,
            "gocept.collmex",
        )  # system identifier

    def test_collmex__Collmex__get_projects__1(self):
        """It returns same project twice for both configured rates."""
        import transaction

        import gocept.collmex.testing

        gocept.collmex.testing.create_project(title="Testprojekt")
        transaction.commit()
        projects = self.collmex.get_projects()
        self.assertEqual(2, len(projects))
        self.assertEqual("1", projects[0]["Satz Nr"])
        self.assertEqual("5,00", projects[0]["Satz"])
        self.assertEqual("2", projects[1]["Satz Nr"])
        self.assertEqual("9,65", projects[1]["Satz"])

    def test_collmex__Collmex__get_projects__2(self):
        """It returns project with budget set on creation."""
        import transaction

        import gocept.collmex.testing

        gocept.collmex.testing.create_project(title="Testprojekt", budget=50)
        transaction.commit()
        projects = self.collmex.get_projects()
        self.assertEqual("50,00", projects[0]["Budget"])

    def test_collmex__Collmex__get_projects__3(self):
        """It returns project with summed up cost for all activities."""
        import datetime

        import transaction

        import gocept.collmex.testing

        gocept.collmex.testing.create_project(title="Testprojekt", budget=50)
        gocept.collmex.testing.create_employee()
        # Default activity has a duration of 5.15h for 5€/h, i.e. costs 25.75€
        gocept.collmex.testing.create_activity(
            "Activity in test project",
            project_id="1",
            employee_id="1",
            date=datetime.date(2012, 1, 1),
        )
        transaction.commit()

        projects = self.collmex.get_projects()
        self.assertEqual("50,00", projects[0]["Budget"])
        self.assertEqual("25,75", projects[0]["Wert"])

    @pytest.mark.skip('Can only be tested with "collmex verein" testaccount.')
    def test_collmex__Collmex__get_members__1(self):
        """It returns all members."""

        # Unfortunately we cannot yet create members with the same
        # test credentials, as this is a special "collmex verein"
        # feature.

        import gocept.collmex.testing

        gocept.collmex.testing.create_member()
        members = self.collmex.get_members()
        self.assertEqual("Testmitglied", members[0]["Name"])
        self.assertEqual(1, len(members))

    @pytest.mark.skip('Can only be tested with "collmex verein" testaccount.')
    def test_collmex__Collmex__create_member__1(self):
        import transaction

        import gocept.collmex.model
        import gocept.collmex.testing

        collmex = gocept.collmex.testing.get_collmex()
        member = gocept.collmex.model.Member()
        member["Mitgliedsnummer"] = 10001
        member["Name"] = "Testmitglied"
        member["Firma"] = 1
        collmex.create(member)
        transaction.commit()
        assert "Testmitglied" in [mem["Name"] for mem in collmex.get_members()]

    @pytest.mark.skip('Can only be tested with "collmex verein" testaccount.')
    def test_collmex__Collmex__create_abo__1(self):
        import transaction

        import gocept.collmex.model
        import gocept.collmex.testing

        gocept.collmex.testing.create_member_product()
        transaction.commit()
        collmex = gocept.collmex.testing.get_collmex()
        prod = gocept.collmex.model.MemberProduct()
        prod["Mitglieds-Nr"] = 10001
        prod["Produkt Nr"] = "TEST2"
        prod["Firma"] = 1
        collmex.create(prod)
        transaction.commit()
        assert "Testmitglied" in [mem["Name"] for mem in collmex.get_members()]


class TestSystemIdentifier(unittest.TestCase):
    """Tests for the configurable system identifier (offline)."""

    def tearDown(self):
        import transaction

        transaction.abort()

    def make_collmex(self, system_identifier=None):
        import gocept.collmex.collmex

        if system_identifier is None:
            return gocept.collmex.collmex.Collmex("any", "any", "any", "any")
        return gocept.collmex.collmex.Collmex(
            "any", "any", "any", "any", system_identifier=system_identifier
        )

    def test_defaults_to_class_attribute(self):
        self.assertEqual(
            "gocept.collmex", self.make_collmex().system_identifier
        )

    def test_overrides_class_attribute(self):
        collmex = self.make_collmex(system_identifier="test-sync")
        self.assertEqual("test-sync", collmex.system_identifier)

    def test_too_long_identifier_raises_value_error(self):
        import gocept.collmex.collmex

        with self.assertRaises(ValueError):
            gocept.collmex.collmex.Collmex(
                "any",
                "any",
                "any",
                "any",
                system_identifier="x" * 21,
            )

    def test_maximum_length_is_accepted(self):
        collmex = self.make_collmex(system_identifier="x" * 20)
        self.assertEqual("x" * 20, collmex.system_identifier)

    def test_identifier_is_sent_with_queries(self):
        import csv
        import io

        import gocept.collmex.collmex

        collmex = self.make_collmex(system_identifier="test-sync")
        collmex._post = mock.Mock(return_value=[["MESSAGE", "S", "0", ""]])
        collmex.get_invoices()
        (data,) = collmex._post.call_args[0]
        [row] = csv.reader(
            io.StringIO(data), dialect=gocept.collmex.collmex.CollmexDialect
        )
        self.assertEqual(
            [
                "INVOICE_GET",
                "(NULL)",  # Rechnungsnummer
                "any",  # Firma Nr
                "(NULL)",  # Kunde Nr
                "(NULL)",  # Rechnungsdatum Von
                "(NULL)",  # Rechnungsdatum Bis
                "0",  # Nur ausgegebene
                "0",  # Rueckgabe-Format
                "(NULL)",  # Nur geaenderte
                "test-sync",  # Systemname
            ],
            row,
        )


class TestDateToCollmex(unittest.TestCase):
    """Tests for the D8 conversion in date_to_collmex() (offline)."""

    def test_null_passes_through(self):
        import gocept.collmex.collmex

        self.assertEqual(
            gocept.collmex.collmex.Collmex.NULL,
            gocept.collmex.collmex.date_to_collmex(
                gocept.collmex.collmex.Collmex.NULL
            ),
        )

    def test_date_is_converted(self):
        import datetime

        import gocept.collmex.collmex

        self.assertEqual(
            "20260123",
            gocept.collmex.collmex.date_to_collmex(datetime.date(2026, 1, 23)),
        )

    def test_datetime_is_converted(self):
        import datetime

        import gocept.collmex.collmex

        self.assertEqual(
            "20260123",
            gocept.collmex.collmex.date_to_collmex(
                datetime.datetime(2026, 1, 23, 12, 30)
            ),
        )

    def test_string_passes_through_unchanged(self):
        import gocept.collmex.collmex

        self.assertEqual(
            "20260123",
            gocept.collmex.collmex.date_to_collmex("20260123"),
        )
