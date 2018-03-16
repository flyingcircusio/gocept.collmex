# coding: utf-8
# Copyright (c) 2008-2012 gocept gmbh & co. kg
# See also LICENSE.txt

from __future__ import unicode_literals
from zope.interface import implementer
import csv
import datetime
import gocept.collmex.collmex
import gocept.collmex.interfaces
import gocept.collmex.model
import logging
import os
import six
import transaction


log = logging.getLogger(__name__)


def get_collmex(password=None):
    os.environ['collmex_credential_section'] = 'test-credentials'
    return gocept.collmex.collmex.Collmex(password=password)


def cleanup_collmex():
    # Prepare a clean environment in our Collmex testing.
    b = get_collmex().browser_login()

    # make sure that deletion only occurs iff test user is logged in
    assert os.environ['collmex_credential_section'] == 'test-credentials'

    # Firma loeschen
    b = b.click(description='Verwaltung')
    b.charset = 'Windows-1252'
    b = b.click(description='Löschen')
    b.charset = 'Windows-1252'

    f = b.form
    f['group_loeschArt'] = '2'
    f['group_bestaetigung'] = True
    b = f.submit(name='loeschen').maybe_follow()
    b.charset = 'Windows-1252'

    assert 'Daten erfolgreich gel' in b.unicode_body


def create_customer():
    collmex = get_collmex()
    if 'Testkunden' not in [cust['Firma'] for cust in collmex.get_customers()]:
        customer = gocept.collmex.model.Customer()
        customer['Kundennummer'] = 10000
        customer['Firma'] = 'Testkunden'
        collmex.create(customer)
        transaction.commit()

    assert 'Testkunden' in [cust['Firma'] for cust in collmex.get_customers()]


def create_member():
    collmex = get_collmex()
    if 'Testmitglied' not in [mem['Name'] for mem in collmex.get_members()]:
         member = gocept.collmex.model.Member()
         member['Mitgliedsnummer'] = 10001
         member['Name'] = 'Testmitglied'
         collmex.create(member)
         transaction.commit()

    assert 'Testmitglied' in [mem['Name'] for mem in collmex.get_members()]


def create_product():
    create_customer()
    collmex = get_collmex()
    if 'TEST' not in [prod['Produktnummer']
                      for prod in collmex.get_products()]:
        product = gocept.collmex.model.Product()
        product['Produktnummer'] = 'TEST'
        product['Bezeichnung'] = 'Testprodukt'
        product['Produktart'] = 1  # Dienstleistung
        product['Basismengeneinheit'] = 'HR'
        product['Verkaufs-Preis'] = 5
        collmex.create(product)
        transaction.commit()

    assert 'TEST' in [prod['Produktnummer'] for prod in collmex.get_products()]


def create_member_product():
    create_member()
    collmex = get_collmex()
    if 'TEST2' not in [prod['Produktnummer']
                      for prod in collmex.get_products()]:
        product = gocept.collmex.model.Product()
        product['Produktnummer'] = 'TEST2'
        product['Bezeichnung'] = 'Testbeitrag'
        product['Produktart'] = 2  # Mitgliedsbeitrag
        product['Verkaufs-Preis'] = 5
        collmex.create(product)
        transaction.commit()

    assert 'TEST2' in [prod['Produktnummer'] for prod in collmex.get_products()]


def create_project(title, budget=0):
    # There is no API to create projects, so use the browser
    create_product()
    b = get_collmex().browser_login()

    # Projekt anlegen
    b = b.click(description='Verkauf', href='crm')
    b.charset = 'Windows-1252'

    # pjcr = Project Create
    b = b.click(description='Anlegen', href='pjcr')
    b.charset = 'Windows-1252'

    b = b.form.submit(name='anlegen')
    b.charset = 'Windows-1252'

    f = b.form
    f['group_bezeichnung'] = title
    f['group_kundeNr'] = '10000'
    f['table_1_produktNr'] = 'TEST'
    f['group_budget'] = budget
    b = f.submit(name='speichern')
    b.charset = 'Windows-1252'

    assert 'Produkt TEST existiert nicht' not in b.unicode_body

    f = b.form
    f['table_2_produktNr'] = 'TEST'
    b = f.submit(name='speichern')
    b.charset = 'Windows-1252'

    assert 'Produkt TEST existiert nicht' not in b.unicode_body

    f = b.form
    f['table_2_satz'] = '9,65'
    b = f.submit(name='speichern')
    b.charset = 'Windows-1252'


def create_employee():
    # There is no API to create employees, so use the browser
    b = get_collmex().browser_login()

    for _ in range(2):
        b = b.click(description='Buchhaltung', href='cgi')
        b.charset = 'Windows-1252'

        b = b.click(description='Mitarbeiter anlegen')
        b.charset = 'Windows-1252'

        b = b.form.submit(name='anlegen')
        b.charset = 'Windows-1252'

    f = b.form
    f['group_adrVorname'] = 'Sebastian'
    f['group_adrName'] = 'Wehrmann'
    b = f.submit(name='speichern').maybe_follow()
    b.charset = 'Windows-1252'


def create_activity(title,
                    date=datetime.date(2012, 1, 23),
                    project_id='1',
                    employee_id='1',
                    start_time=datetime.time(8, 7),
                    end_time=datetime.time(14, 28),
                    break_time=datetime.timedelta(hours=1, minutes=12)):
    collmex = get_collmex()
    act = gocept.collmex.model.Activity()
    act['Projekt Nr'] = project_id
    act['Mitarbeiter Nr'] = employee_id
    act['Satz Nr'] = '1'  # TEST
    act['Beschreibung'] = title
    act['Datum'] = date
    act['Von'] = start_time
    act['Bis'] = end_time
    act['Pausen'] = break_time
    collmex.create(act)
    transaction.commit()


NULL = gocept.collmex.interfaces.NULL


@implementer(gocept.collmex.interfaces.ICollmex)
class ConsoleDump(object):

    def __init__(self):
        log.info('Initialized console collmex connection.')

    def create(self, item):
        log.info('Would create item %r' % self._serialize(item))

    def _serialize(self, item):
        data = six.StringIO()
        writer = csv.writer(
            data, dialect=gocept.collmex.collmex.CollmexDialect)
        item.company = 'NONE'
        writer.writerow([elem.encode('UTF-8')
                         if isinstance(elem, six.text_type) and six.PY2
                         else elem for elem in list(item)])
        return data.getvalue()

    def create_invoice(self, items):
        for item in items:
            self.create(item)

    def create_product(self, product):
        self.create(product)

    def create_customer(self, customer):
        self.create(customer)

    def get_invoices(self, invoice_id=NULL, customer_id=NULL,
                     start_date=NULL, end_date=NULL):
        log.info('get_invoices()')
        return []

    def get_customers(self, customer_id=NULL, text=NULL):
        log.info('get_customers()')
        return []

    def get_members(self, member_id=NULL, text=NULL):
        log.info('get_members()')
        return []

    def get_products(self, product_id=NULL,
                     product_group=NULL, price_group=NULL):
        log.info('get_products()')
        return []

    def get_projects(self, project_id=NULL, customer_id=NULL):
        log.info('get_projects()')
        return []

    def get_activities(self, project_id=NULL,
                       employee_id=NULL,
                       start_date=NULL, end_date=NULL,
                       only_non_billed=NULL, billable=NULL,
                       only_non_internal=NULL,
                       only_changed=NULL):
        log.info('get_activities()')
        return []
