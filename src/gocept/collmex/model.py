# coding: utf8

from __future__ import unicode_literals
from six.moves import UserDict
import datetime
import gocept.collmex.interfaces
import six
import zope.interface


class Model(UserDict, object):
    """Base for collmex models."""

    satzart = None

    def __init__(self, row=()):
        UserDict.__init__(self)

        self['Satzart'] = self.satzart
        self._unmapped = []

        for i, value in enumerate(row):
            if (value is None or isinstance(value, six.text_type) and
                    value == ''):
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


@zope.interface.implementer(gocept.collmex.interfaces.IInvoiceItem)
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

    # Possible values for 'Positionstyp'
    TYPE_DEFAULT = 0
    TYPE_SUM = 1
    TYPE_TEXT = 2
    TYPE_FREE = 3

    def __init__(self, row=()):
        super(InvoiceItem, self).__init__(row)
        if not self.get('Rechnungsart'):
            self['Rechnungsart'] = 0  # type invoice


@zope.interface.implementer(gocept.collmex.interfaces.IMember)
class Member(Model):
    satzart = 'CMXMGD'
    fields = (
        'Satzart',
        'Mitgliedsnummer',
        'Anrede',
        'Titel',
        'Vorname',
        'Name',
        'Firma',
        'Abteilung',
        'Straße',
        'PLZ',
        'Ort',
        'Löschen',
        'URL',
        'Land',
        'Telefon',
        'Telefax',
        'E-Mail',
        'Kontonummer',
        'Blz',
        'Iban',
        'Bic',
        'Bankname',
        'Lastschrift-Mandatsreferenz',
        'Datum Unterschrift',
        'Geburtsdatum',
        'Eintrittsdatum',
        'Austrittsdatum',
        'Bemerkung',
        'Telefon2',
        'Skype/VoIP',
        'Kontoinhaber',
        'Ausgabemedium',
        'Adressgruppe',
        'Zahlungsbedingung',
        'Abrechnung über',
        'Ausgabesprache',
        'Kostenstelle',
    )


@zope.interface.implementer(gocept.collmex.interfaces.IMemberProduct)
class MemberProduct(Model):
    satzart = 'CMXABO'
    fields = (
        'Satzart',
        'Mitglieds-Nr',
        'Firma',
        'Gültig von',
        'Gültig bis',
        'Produkt Nr',
        'Produktbeschreibung',
        'Individueller Preis',
        'Intervall',
        'Nächste Rechnung',
        'Reserviert',
        'Pos',
    )


@zope.interface.implementer(gocept.collmex.interfaces.ICustomer)
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


@zope.interface.implementer(gocept.collmex.interfaces.IProduct)
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


@zope.interface.implementer(gocept.collmex.interfaces.IActivity)
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

    @property
    def day(self):
        return datetime.datetime.strptime(self['Datum'], '%Y%m%d').date()

    @property
    def start_time(self):
        return self._start_datetime.time()

    @property
    def end_time(self):
        return self._end_datetime.time()

    @property
    def breaks(self):
        time = datetime.datetime.strptime(self['Pausen'], '%H:%M').time()
        return datetime.timedelta(hours=time.hour, minutes=time.minute)

    @property
    def duration(self):
        return self._end_datetime - self._start_datetime - self.breaks

    @property
    def project_name(self):
        # skip id in front of name
        _, name = self['Projekt Nr'].split(' ', 1)
        return name

    @property
    def employee_name(self):
        _, name = self['Mitarbeiter Nr'].split(' ', 1)
        return name

    @property
    def _start_datetime(self):
        return datetime.datetime.strptime(self['Von'], '%H:%M')

    @property
    def _end_datetime(self):
        return datetime.datetime.strptime(self['Bis'], '%H:%M')


@zope.interface.implementer(gocept.collmex.interfaces.IProject)
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
        'Budget',
        'Wert',
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
