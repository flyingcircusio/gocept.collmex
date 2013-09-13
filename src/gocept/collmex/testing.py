# coding: utf-8
# Copyright (c) 2008-2012 gocept gmbh & co. kg
# See also LICENSE.txt

from __future__ import unicode_literals
import datetime
import gocept.collmex.collmex
import gocept.collmex.model
import os
import transaction
import six


def get_collmex(password=None):
    customer = os.environ['collmex_customer']
    company = os.environ['collmex_company']
    username = os.environ['collmex_username']
    password = os.environ['collmex_password'] if password is None else password

    customer, company, username, password = [
        six.u(string) if isinstance(string, six.binary_type) else string
        for string in [customer, company, username, password]]

    return gocept.collmex.collmex.Collmex(
        customer,
        company,
        username,
        password)


def cleanup_collmex():
    # Prepare a clean environment in our Collmex testing.
    b = get_collmex().browser_login()

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


def create_project(title):
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
                    employee_id='1'):
    collmex = get_collmex()
    act = gocept.collmex.model.Activity()
    act['Projekt Nr'] = project_id
    act['Mitarbeiter Nr'] = employee_id
    act['Satz Nr'] = '1'  # TEST
    act['Beschreibung'] = title
    act['Datum'] = date
    act['Von'] = datetime.time(8, 7)
    act['Bis'] = datetime.time(14, 28)
    act['Pausen'] = datetime.timedelta(hours=1, minutes=12)
    collmex.create(act)
    transaction.commit()
