# coding: utf-8
# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

import os
import zope.testbrowser.browser


def cleanup_collmex():
    # Prepare a clean environment in our Collmex testing.
    b = zope.testbrowser.browser.Browser()
    b.open('http://www.collmex.de')

    # Login
    b.getControl('Kunden Nr').value = os.environ['collmex_customer']
    b.getControl('anmelden...').click()

    b.getControl('Benutzer').value = os.environ['collmex_username']
    b.getControl('Kennwort').value = os.environ['collmex_password']
    b.getControl('Anmelden').click()

    # Firma loeschen
    b.getLink('Verwaltung').click()
    b.getLink(u'Löschen').click()
    b.getControl(u'Zu löschende Daten').displayValue = [
        'Alle Belege und Stammdaten']
    b.getControl(u'Ja, wirklich löschen').selected = True
    b.getControl(u'Daten löschen').click()

    assert 'Daten erfolgreich gel' in b.contents

    # Explicitly close response to not leave open http objects.
    b.mech_browser._response.close()
