# Copyright (c) 2008-2012 gocept gmbh & co. kg
# See also LICENSE.txt

from __future__ import unicode_literals
import datetime
import gocept.collmex.interfaces
import gocept.collmex.model
import unittest
import zope.interface

@zope.interface.implementer(gocept.collmex.interfaces.IInvoiceItem)
class TestModel(gocept.collmex.model.Model):

    satzart = 'CMXINV'
    fields = (
        'Satzart',
        'Rechnungsnummer',
    )


class ModelTest(unittest.TestCase):

    def test_model_robust_against_extension(self):
        tm = TestModel(['CMXINV', 'foo', 'bar', ''])
        self.assertEqual('foo', tm['Rechnungsnummer'])
        self.assertEqual(['bar', None], tm._unmapped)


class TestActivity(unittest.TestCase):

    def act(self, **kw):
        from ..model import Activity
        act = Activity()
        act.update(**kw)
        return act

    def test_day_should_return_matching_date_object(self):
        self.assertEqual(
            datetime.date(2013, 4, 12),
            self.act(Datum='20130412').day)

    def test_start_time_should_return_matching_time_object(self):
        self.assertEqual(
            datetime.time(8, 27),
            self.act(Von='08:27').start_time)

    def test_end_time_should_return_matching_time_object(self):
        self.assertEqual(
            datetime.time(17, 34),
            self.act(Bis='17:34').end_time)

    def test_breaks_should_return_matching_timedelta(self):
        self.assertEqual(
            datetime.timedelta(hours=1, minutes=34),
            self.act(Pausen='1:34').breaks)

    def test_duration_should_return_matching_timedelta(self):
        self.assertEqual(
            datetime.timedelta(hours=8, minutes=0),
            self.act(Von='08:00', Bis='17:00', Pausen='1:00').duration)

    def test_project_name_should_skip_project_id(self):
        self.assertEqual(
            'Foo bar project',
            self.act(**{'Projekt Nr': '43 Foo bar project'}).project_name)

    def test_employee_name_should_skip_employee_id(self):
        self.assertEqual(
            'Foo bar employee',
            self.act(**{'Mitarbeiter Nr': '43 Foo bar employee'}).employee_name)