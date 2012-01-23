# coding: utf-8
# Copyright (c) 2008-2012 gocept gmbh & co. kg
# See also LICENSE.txt

import os
import transaction
import gocept.collmex.collmex
import gocept.collmex.model
import zope.testbrowser.browser
import datetime


def collmex_login():
    # Log into collmex
    b = zope.testbrowser.browser.Browser()
    b.open('http://www.collmex.de')

    b.getControl('Kunden Nr').value = os.environ['collmex_customer']
    b.getControl('anmelden...').click()

    b.getControl('Benutzer').value = os.environ['collmex_username']
    b.getControl('Kennwort').value = os.environ['collmex_password']
    b.getControl('Anmelden').click()
    return b


def get_collmex(password=None):
    return gocept.collmex.collmex.Collmex(
        os.environ['collmex_customer'],
        os.environ['collmex_company'],
        os.environ['collmex_username'],
        os.environ['collmex_password'] if password is None else password)


def cleanup_collmex():
    # Prepare a clean environment in our Collmex testing.
    b = collmex_login()

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


def create_projects():
    # There is no API to create projects, so use the browser
    b = collmex_login()

    # Projekt anlegen
    b.getLink('Verkauf').click()
    b.getLink(url=',pjcr').click()
    assert b.title.startswith('Projekt anlegen')

    b.getControl('Projekt anlegen').click()
    b.getControl('Bezeichnung').value = 'Testprojekt'
    b.getControl('Kunde').value = '10000'

    b.getControl(name='table_1_produktNr').value = 'TEST'
    b.getControl('Speichern').click()
    b.getControl(name='table_2_produktNr').value = 'TEST'
    b.getControl('Speichern').click()
    b.getControl(name='table_2_satz').value = '9,65'
    b.getControl('Speichern').click()


def create_employee():
    # There is no API to create employees, so use the browser
    b = collmex_login()
    b.getLink('Buchhaltung').click()
    b.getLink('Mitarbeiter anlegen').click()
    b.getControl('Mitarbeiter anlegen').click()
    b.getControl('Vorname').value = 'Sebastian'
    b.getControl('Name').value = 'Wehrmann'
    b.getControl('Speichern').click()


def create_activity(collmex):
    create_projects()
    create_employee()
    act = gocept.collmex.model.Activity()
    act['Projekt Nr'] = '1' # Testprojekt
    act['Mitarbeiter Nr'] = '1' # Sebastian Wehrmann
    act['Satz Nr'] = '1' # TEST
    act['Beschreibung'] = u'allgemeine T\xe4tigkeit'
    act['Datum'] = datetime.date.today()
    act['Von'] = datetime.time(8, 7)
    act['Bis'] = datetime.time(14, 28)
    act['Pausen'] = datetime.timedelta(hours=1, minutes=12)
    collmex.create(act)
    transaction.commit()
