# vim:fileencoding=utf-8 -*- coding: utf-8 -*-
# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

import zope.testbrowser.browser


def cleanup_collmex():
    # Prepare a clean environment in our Collmex testing.
    b = zope.testbrowser.browser.Browser()
    b.open('http://www.collmex.de')

    # Login
    b.getControl('Kunden Nr').value = '42779'
    b.getControl('anmelden...').click()

    b.getControl('Benutzer').value = '1141688'
    b.getControl('Kennwort').value = '1416678'
    b.getControl('Anmelden').click()

    # Firma loeschen
    b.getLink('Verwaltung').click()
    b.getLink(u'Löschen').click()
    b.getControl(u'Zu löschende Daten').displayValue = [
        'Alle Belege und Stammdaten']
    b.getControl(u'Ja, wirklich löschen').selected = True
    b.getControl(u'Daten löschen').click()

    assert 'Daten erfolgreich gel' in b.contents

    # Beispielkunden anlegen
    b.getLink('Warenwirtschaft').click()
    add_link = b.getLink(u'Anzeigen und ändern', index=2)
    assert add_link.url.endswith('cu')
    add_link.click() # XXX Magic number
    b.getLink('Anlegen').click()
    b.getControl('Kunde Nr', index=0).value = '10000'
    b.getControl('Kunde anlegen').click()
    b.getControl('Firma').value = 'Testkunden'
    b.getControl('Speichern').click()

    # Beispielprodukt anlegen
    b.getLink('Warenwirtschaft').click()
    add_link = b.getLink(u'Anlegen', index=4)
    assert add_link.url.endswith('prcr')
    add_link.click() # XXX Magic number
    b.getControl('Produkt', index=1).value = 'TRAFFIC'
    b.getControl('Produkt anlegen').click()
    b.getControl('Bezeichnung').value = 'Testprodukt'
    b.getControl('Speichern').click()
    b.getLink('Verkauf', index=1).click()
    b.getControl(name='preis_1_preis').value = '5,00'
    b.getControl('Speichern').click()
