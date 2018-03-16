# coding: utf8

from __future__ import unicode_literals
import mock
import unittest


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

    @mock.patch.dict('os.environ',
                     {'collmex_credential_section': 'non-existing-credentials'}
                     )
    def test_missing_login_information_raises_an_exception(self):
        import gocept.collmex.collmex
        with self.assertRaises(ValueError):
            gocept.collmex.collmex.Collmex()

    def test_invalid_login_information_raises_an_exception_via_API(self):
        import gocept.collmex.collmex
        import gocept.collmex.testing

        collmex_invalid = gocept.collmex.testing.get_collmex(
            password='invalid')
        with self.assertRaises(gocept.collmex.collmex.APIError) as err:
            collmex_invalid.get_invoices(customer_id='10000')
        self.assertEqual(('101004', 'Benutzer oder Kennwort nicht korrekt'),
                         err.exception.args)

    def test_invalid_login_information_raises_an_exception_via_browser(self):
        import gocept.collmex.testing

        collmex_invalid = gocept.collmex.testing.get_collmex(
            password='invalid')
        with self.assertRaises(ValueError) as err:
            collmex_invalid.browser_login()
        self.assertIn(
            'Benutzer oder Kennwort nicht korrekt', err.exception.args[0])

    def test_browser_login_authenticates_user_using_browser(self):
        browser = self.collmex.browser_login()
        links = browser.html.find_all('a')
        [link] = [s for s in links if 'Projekt-Verbrauch' in s]
        self.assertTrue(link.get('href').endswith(',vbrp'))

    def test_get_activities_should_support_passing_project_id(self):
        import datetime
        import gocept.collmex.testing
        import transaction
        gocept.collmex.testing.create_employee()
        gocept.collmex.testing.create_project(title='Testprojekt')
        gocept.collmex.testing.create_project(title='Projektil')
        gocept.collmex.testing.create_activity(
            'Activity in test project',
            project_id='1', employee_id='1',
            date=datetime.date(2012, 1, 1))
        gocept.collmex.testing.create_activity(
            'Activity in projektil',
            project_id='2', employee_id='1',
            date=datetime.date(2012, 1, 2))
        transaction.commit()
        activities = self.collmex.get_activities(project_id='2')
        self.assertEqual(1, len(activities))

    def test_get_activities_should_pass_all_parameters(self):
        collmex = self.collmex
        query = collmex._query_objects = mock.Mock()
        collmex.get_activities(
            project_id=mock.sentinel.project_id,
            employee_id=mock.sentinel.employee_id,
            start_date=mock.sentinel.start_date,
            end_date=mock.sentinel.end_date,
            only_non_billed=mock.sentinel.only_non_billed,
            billable=mock.sentinel.billable,
            only_non_internal=mock.sentinel.only_non_internal,
            only_changed=mock.sentinel.only_changed)
        query.assert_called_with(
            'ACTIVITIES_GET',
            mock.sentinel.project_id,
            '1',  # Company id
            mock.sentinel.employee_id,
            mock.sentinel.start_date,
            mock.sentinel.end_date,
            mock.sentinel.only_non_billed,
            mock.sentinel.billable,
            mock.sentinel.only_non_internal,
            mock.sentinel.only_changed,
            'gocept.collmex')  # system identifier

    def test_collmex__Collmex__get_projects__1(self):
        """It returns same project twice for both configured rates."""
        import gocept.collmex.testing
        import transaction
        gocept.collmex.testing.create_project(title='Testprojekt')
        transaction.commit()
        projects = self.collmex.get_projects()
        self.assertEqual(2, len(projects))
        self.assertEqual('1', projects[0]['Satz Nr'])
        self.assertEqual('5,00', projects[0]['Satz'])
        self.assertEqual('2', projects[1]['Satz Nr'])
        self.assertEqual('9,65', projects[1]['Satz'])

    def test_collmex__Collmex__get_projects__2(self):
        """It returns project with budget set on creation."""
        import gocept.collmex.testing
        import transaction
        gocept.collmex.testing.create_project(title='Testprojekt', budget=50)
        transaction.commit()
        projects = self.collmex.get_projects()
        self.assertEqual('50,00', projects[0]['Budget'])

    def test_collmex__Collmex__get_projects__3(self):
        """It returns project with summed up cost for all activities."""
        import datetime
        import gocept.collmex.testing
        import transaction
        gocept.collmex.testing.create_project(title='Testprojekt', budget=50)
        gocept.collmex.testing.create_employee()
        # Default activity has a duration of 5.15h for 5€/h, i.e. costs 25.75€
        gocept.collmex.testing.create_activity(
            'Activity in test project',
            project_id='1', employee_id='1',
            date=datetime.date(2012, 1, 1))
        transaction.commit()

        projects = self.collmex.get_projects()
        self.assertEqual('50,00', projects[0]['Budget'])
        self.assertEqual('25,75', projects[0]['Wert'])

    def test_collmex__Collmex__get_members__1(self):
        #unfortunately this can only be tested
        #with a "collmex verein" testaccount
        return
        """It returns all members."""

        # Unfortunately we cannot yet create members with the same
        # test credentials, as this is a special "collmex verein"
        # feature.

        import gocept.collmex.testing
        gocept.collmex.testing.create_member()
        members = self.collmex.get_members()
        self.assertEqual('Testmitglied', members[0]['Name'])
        self.assertEqual(1, len(members))

    def test_collmex__Collmex__create_member__1(self):
        #unfortunately this can only be tested
        #with a "collmex verein" testaccount
        return
        import gocept.collmex.testing
        import gocept.collmex.model
        import transaction
        collmex = gocept.collmex.testing.get_collmex()
        member = gocept.collmex.model.Member()
        member['Mitgliedsnummer'] = 10001
        member['Name'] = 'Testmitglied'
        member['Firma'] = 1
        collmex.create(member)
        transaction.commit()
        assert 'Testmitglied' in [mem['Name'] for mem in collmex.get_members()]

    def test_collmex__Collmex__create_abo__1(self):
        #unfortunately this can only be tested
        #with a "collmex verein" testaccount
        return
        import gocept.collmex.testing
        import gocept.collmex.model
        import transaction
        gocept.collmex.testing.create_member_product()
        transaction.commit()
        collmex = gocept.collmex.testing.get_collmex()
        prod = gocept.collmex.model.MemberProduct()
        prod['Mitglieds-Nr'] = 10001
        prod['Produkt Nr'] = 'TEST2'
        prod['Firma'] = 1
        collmex.create(prod)
        transaction.commit()
        assert 'Testmitglied' in [mem['Name'] for mem in collmex.get_members()]
