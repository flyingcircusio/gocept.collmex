# coding: utf-8
# Copyright (c) 2008-2012 gocept gmbh & co. kg
# See also LICENSE.txt

import datetime
import gocept.collmex.collmex
import gocept.collmex.model
import os
import transaction
import zope.testbrowser.browser


def get_collmex(password=None):
    return gocept.collmex.collmex.Collmex(
        os.environ['collmex_customer'],
        os.environ['collmex_company'],
        os.environ['collmex_username'],
        os.environ['collmex_password'] if password is None else password)

def cleanup_collmex():
    # Prepare a clean environment in our Collmex testing.
    b = get_collmex().browser_login()

    # Firma loeschen
    b.getLink('Verwaltung').click()
    b.getLink(u'Löschen').click()
    b.getControl(u'Umfang der Löschung').displayValue = [
        'Alle Belege und Stammdaten']
    b.getControl(u'Ja, wirklich löschen').selected = True
    b.getControl(u'Daten löschen').click()

    assert 'Daten erfolgreich gel' in b.contents

    # Explicitly close response to not leave open http objects.
    b.mech_browser._response.close()

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
        product['Produktart'] = 1 # Dienstleistung
        product['Basismengeneinheit'] = 'HR'
        product['Verkaufs-Preis'] = 5
        collmex.create(product)
        transaction.commit()

    assert 'TEST' in [prod['Produktnummer'] for prod in collmex.get_products()]


def create_projects():
    # There is no API to create projects, so use the browser
    create_product()

    b = get_collmex().browser_login()
    # Projekt anlegen
    b.getLink('Verkauf').click()
    b.getLink(url=',pjcr').click()
    assert b.title.startswith('Projekt anlegen')

    b.getControl('Projekt anlegen').click()
    b.getControl('Bezeichnung').value = 'Testprojekt'
    b.getControl('Kunde').value = '10000'

    b.getControl(name='table_1_produktNr').value = 'TEST'
    b.getControl('Speichern').click()
    assert 'Produkt TEST existiert nicht' not in b.contents

    b.getControl(name='table_2_produktNr').value = 'TEST'
    b.getControl('Speichern').click()
    assert 'Produkt TEST existiert nicht' not in b.contents
    b.getControl(name='table_2_satz').value = '9,65'
    b.getControl('Speichern').click()


def create_employee():
    # There is no API to create employees, so use the browser
    b = get_collmex().browser_login()
    b.getLink('Buchhaltung').click()
    b.getLink('Mitarbeiter anlegen').click()
    b.getControl('Mitarbeiter anlegen').click()
    b.getControl('Vorname').value = 'Sebastian'
    b.getControl('Name').value = 'Wehrmann'
    b.getControl('Speichern').click()


def create_activity():
    create_projects()
    create_employee()
    collmex = get_collmex()
    act = gocept.collmex.model.Activity()
    act['Projekt Nr'] = '1' # Testprojekt
    act['Mitarbeiter Nr'] = '1' # Sebastian Wehrmann
    act['Satz Nr'] = '1' # TEST
    act['Beschreibung'] = u'allgemeine T\xe4tigkeit'
    act['Datum'] = datetime.date(2012, 1, 23)
    act['Von'] = datetime.time(8, 7)
    act['Bis'] = datetime.time(14, 28)
    act['Pausen'] = datetime.timedelta(hours=1, minutes=12)
    collmex.create(act)
    transaction.commit()
