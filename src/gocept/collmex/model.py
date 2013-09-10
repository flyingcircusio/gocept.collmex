# coding: utf8
# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

from __future__ import unicode_literals
import six
if six.PY3:
    from collections import UserDict
else:
    from UserDict import UserDict
import datetime
import gocept.collmex.interfaces
import zope.interface
from zope.interface import implementer

class Model(UserDict, object):
    """Base for collmex models."""

    satzart = None

    def __init__(self, row=()):
        UserDict.__init__(self)

        self['Satzart'] = self.satzart
        self._unmapped = []

        for i, value in enumerate(row):
            if value is None or isinstance(value, six.text_type) and value == '':
                value = None
            try:
                field_name = self.fields[i]
            except IndexError:
                self._unmapped.append(value)
            else:
                self[field_name] = value

    def __iter__(self):
        for field in self.fields:
            if field in self:
                yield self[field]
            else:
                yield gocept.collmex.interfaces.NULL

    @property
    def company(self):
        return self['Firma Nr']

    @company.setter
    def company(self, company_id):
        self['Firma Nr'] = company_id

    def __repr__(self):
        return '<%s.%s object at %s>' % (
            self.__class__.__module__,
            self.__class__.__name__,
            hex(id(self)))


def factory(record_type):
    """looks up Model class representing the given `record_type`."""

    for class_ in globals().values():
        if isinstance(class_, type) and issubclass(class_, Model):
            if class_.satzart == record_type:
                return class_
    return None


@implementer(gocept.collmex.interfaces.IInvoiceItem)
class InvoiceItem(Model):

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

    def __init__(self, row=()):
        super(InvoiceItem, self).__init__(row)
        if not self.get('Rechnungsart'):
            self['Rechnungsart'] = 0  # type invoice


@implementer(gocept.collmex.interfaces.ICustomer)
class Customer(Model):

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
        'Wiedervorlage am',
        'Liefersperre',
        'Baudienstleister',
        'Lief-Nr. bei Kunde',
        'Ausgabesprache',
        'CC',
    )


@implementer(gocept.collmex.interfaces.IProduct)
class Product(Model):

    satzart = 'CMXPRD'
    fields = (
        'Satzart',
        'Produktnummer',
        'Bezeichnung',
        'Bezeichnung Eng',
        'Basismengeneinheit',
        'Produktgruppe',
        'Firma',
        'Steuerklassifikation',
        'Gewicht',
        'Gewicht Mengeneinheit',
        'Preismenge',
        'Produktart',
        'Inaktiv',
        'Preisgruppe',
        'Verkaufs-Preis',
        'EAN',
        'Hersteller',
        'Versandgruppe',
        'Mindestbestand',
        'Bestellmenge',
        'Chargenpflicht',
        'Beschaffungsart',
        'Produktionsdauer',
        'Lohnkosten',
        'Lohnkosten-Bezugsmenge',
        'Reserviert',
    )

    @property
    def company(self):
        return self['Firma']

    @company.setter
    def company(self, company_id):
        self['Firma'] = company_id


@implementer(gocept.collmex.interfaces.IActivity)
class Activity(Model):

    satzart = 'CMXACT'
    fields = (
        'Satzart',
        'Projekt Nr',
        'Mitarbeiter Nr',
        'Firma Nr',
        'Satz Nr',
        'Beschreibung',
        'Datum',
        'Von',
        'Bis',
        'Pausen',
    )


@implementer(gocept.collmex.interfaces.IProject)
class Project(Model):

    satzart = 'CMXPRJ'
    fields = (
        'Satzart',
        'Projektnummer',
        'Firma Nr',
        'Bezeichnung',
        'Kunde Nr',
        'Name des Kunden',
        'Abgeschlossen',
        'Reserviert',
        'Reserviert',
        'Reserviert',
        'Reserviert',
        'Reserviert',
        'Satz Nr',
        'Satz Bezeichnung',
        'Produktnummer',
        'Satz',
        'Währung',
        'Mengeneinheit',
        'Inaktiv',
    )
