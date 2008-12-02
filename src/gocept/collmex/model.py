# coding: utf8
# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

import UserDict
import gocept.collmex.interfaces
import zope.interface

class Model(object, UserDict.UserDict):
    """Base for collmex models."""

    satzart = None

    def __init__(self, row=[]):
        UserDict.UserDict.__init__(self)

        self['Satzart'] = self.satzart
        self['Rechnungsart'] = 0 # type invoice

        for i in range(len(row)):
            if row[i] == '':
                row[i] = None
            self[self.fields[i]] = row[i]

    def __iter__(self):
        result = []
        for field in self.fields:
            if field in self:
                value = self[field]
                if isinstance(value, unicode):
                    value = value.encode('Windows-1252')
                yield value
            else:
                yield gocept.collmex.interfaces.NULL


class InvoiceItem(Model):

    zope.interface.implements(gocept.collmex.interfaces.IInvoiceItem)

    satzart = 'CMXINV'
    fields = (
        'Satzart',
        'Rechnungsnummer',
        'Position',
        'Rechnungsart',
        'Firma Nr',
        'Auftrag Nr',
        'Kunden-Nr',
        'Anrede',
        'Titel',
        'Vorname',
        'Name',
        'Firma',
        'Abteilung',
        'Strasse',
        'PLZ',
        'Ort',
        'Land',
        'Telefon',
        'Telefon2',
        'Telefax',
        'E-Mail',
        'Kontonr',
        'Blz',
        'Abweichender Kontoinhaber',
        'IBAN',
        'BIC',
        'Bank',
        'USt.IdNr',
        'Privatperson',
        'Rechnungsdatum',
        'Preisdatum',
        'Zahlungsbedingung',
        'Währung',
        'Preisgruppe',
        'Rabattgruppe',
        'Schluss-Rabatt',
        'Rabattgrund',
        'Rechnungstext',
        'Schlusstext',
        'Internes Memo',
        'Gelöscht',
        'Sprache',
        'Bearbeiter',
        'Reserviert',
        'Reserviert',
        'Reserviert',
        'Reserviert',
        'Reserviert',
        'Versandart',
        'Versandkosten',
        'Nachnahmegebühr',
        'Lieferdatum',
        'Lieferbedingung',
        'Lieferbedingung Zusatz',
        'Anrede Lieferung',
        'Titel Lieferung',
        'Vorname Lieferung',
        'Name Lieferung',
        'Firma Lieferung',
        'Abteilung Lieferung',
        'Strasse Lieferung',
        'PLZ Lieferung',
        'Ort Lieferung',
        'Land Lieferung',
        'Telefon Lieferung',
        'Telefon2 Lieferung',
        'Telefax Lieferung',
        'E-Mail Lieferung',
        'Positionstyp',
        'Produktnummer',
        'Produktbeschreibung',
        'Mengeneinheit',
        'Menge',
        'Einzelpreis',
        'Preismenge',
        'Positionsrabatt',
        'Positionswert',
        'Produktart',
        'Steuerklassifikation',
        'Steuer auch im Ausland',
        'Kundenauftragsposition',
        'Erlösart',
        )


class Customer(Model):

    zope.interface.implements(gocept.collmex.interfaces.ICustomer)

    satzart = 'CMXKND'
    fields = (
        'Satzart',
        'Kundennummer',
        'Firma Nr',
        'Anrede',
        'Titel',
        'Vorname',
        'Name',
        'Firma',
        'Abteilung',
        'Strasse',
        'PLZ',
        'Ort',
        'Reserviert',
        'Reserviert',
        'Land',
        'Telefon',
        'Telefax',
        'E-Mail',
        'Kontonr',
        'Blz',
        'Iban',
        'Bic',
        'Bankname',
        'Steuernummer',
        'USt.IdNr',
        'Zahlungsbedingung',
        'Rabattgruppe',
        'Lieferbedingung',
        'Lieferbedingung Zusatz',
        'Ausgabemedium',
        'Kontoinhaber',
        'Adressgruppe',
        'Privatperson',
        'Preisgruppe',
        'Währung (ISO-Codes)',
        'Vermittler',
        'Kostenstelle',
    )
