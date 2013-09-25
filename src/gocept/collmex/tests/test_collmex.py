# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

from __future__ import unicode_literals
import mock
import unittest


class TestCollmex(unittest.TestCase):

    def setUp(self):
        import gocept.collmex.testing
        gocept.collmex.testing.cleanup_collmex()

    @property
    def collmex(self):
        import gocept.collmex.testing
        return gocept.collmex.testing.get_collmex()

    @mock.patch.dict('os.environ',
        {'collmex_credential_section': 'non-existing-credentials'})
    def test_missing_login_information_raises_an_exception(self):
        import gocept.collmex.collmex
        with self.assertRaises(ValueError) as err:
            gocept.collmex.collmex.Collmex()
        self.assertEqual('Not enough credentials given for '
                         'initialization and no valid ini file found. '
                         'Searching and parsing the ini file gave the '
                         'following error message: Could not find an '
                         'ini file with the name \'collmex.ini\' in the '
                         'current or any parent directory, which '
                         'contained the section \'[non-existing-credentials]\''
                         ' with the following options: customer_id, '
                         'company_id, username, password.',
                         str(err.exception))

    def test_invalid_login_information_raises_an_exception(self):
        import gocept.collmex.collmex
        import gocept.collmex.testing

        collmex_invalid = gocept.collmex.testing.get_collmex(
            password='invalid')
        with self.assertRaises(gocept.collmex.collmex.APIError) as err:
            collmex_invalid.get_invoices(customer_id='10000')
        self.assertEqual(('101004', 'Benutzer oder Kennwort nicht korrekt'),
                         err.exception.args)

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
