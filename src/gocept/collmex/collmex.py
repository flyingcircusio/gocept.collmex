# -*- coding: utf-8 -*-
# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

import StringIO
import UserDict
import csv
import gocept.collmex.interfaces
import gocept.collmex.utils
import threading
import transaction
import transaction.interfaces
import urllib2
import zope.interface


class CollmexDialect(csv.Dialect):
    quoting = csv.QUOTE_ALL
    delimiter = ';'
    quotechar = '"'
    lineterminator = '\r\n'
    doublequote = True
    skipinitialspace = True


class APIError(Exception):
    pass


class CollmexDataManager(object):
    zope.interface.implements(transaction.interfaces.IDataManager)

    def __init__(self, utility):
        self.utility = utility
        self._reset()

    def _reset(self):
        self.data = StringIO.StringIO()
        self._joined = False
        self._transaction = None

    def register_data(self, data):
        """Registers one or more CSV lines for writing."""
        self.data.write(data)
        if not self._joined:
            transaction.get().join(self)
            self._joined = True

    def abort(self, transaction):
        if self._transaction is not None:
            # No abort during TPC.
            return
        self._reset()

    def tpc_begin(self, transaction):
        self._transaction = transaction

    def commit(self, transaction):
        assert transaction is self._transaction
        # We need to do our work in tpc_vote as we're a single-phase-only data manager.
        pass

    def tpc_vote(self, transaction):
        assert transaction is self._transaction
        self.utility._post(self.data.getvalue())
        self.voted = True

    def tpc_abort(self, transaction):
        assert transaction is self._transaction
        if self.voted:
            raise Exception('Single phase data manager: cannot abort after vote')
        self._reset()

    def tpc_finish(self, transaction):
        assert transaction is self._transaction
        self._reset()

    def sortKey(self):
        # XXX make very small or add single-phase datamanager integration to the transaction module.
        return None


class Collmex(object):
    zope.interface.implements(gocept.collmex.interfaces.ICollmex)

    # XXX should go on CollmexDialect but the csv module's magic prevents it
    NULL = '(NULL)'

    def __init__(self, customer_id, company_id, username, password):
        self.customer_id = customer_id
        self.company_id = company_id
        self.username = username
        self.password = password

        # Store thread-local (actually: transaction-local) information
        self._local = threading.local()

    @property
    def connection(self):
        connection = getattr(self._local, 'connection', None)
        if connection is None:
            connection = self._local.connection = CollmexDataManager(self)
        return connection

    def create_invoice(self, items):
        data = StringIO.StringIO()
        writer = csv.writer(data, dialect=CollmexDialect)
        for item in items:
            item['Firma Nr'] = self.company_id
            writer.writerow(list(item))
        self.connection.register_data(data.getvalue())

    def get_invoices(self, invoice_id=NULL, customer_id=NULL,
                     start_date=NULL, end_date=NULL):
        data = StringIO.StringIO()
        writer = csv.writer(data, dialect=CollmexDialect)
        writer.writerow(['INVOICE_GET', invoice_id, self.company_id, customer_id,
                         date_to_collmex(start_date), date_to_collmex(end_date),
                         0, 0, 0, 'gocept.collmex'])
        lines = self._post(data.getvalue())
        return [InvoiceItem(line) for line in lines]

    def _post(self, data):
        data = 'LOGIN;%s;%s\n' % (self.username, self.password) + data

        content_type, body = gocept.collmex.utils.encode_multipart_formdata(
            [], [('fileName', 'api.csv', data)])

        request = urllib2.Request('https://www.collmex.de/cgi-bin/cgi.exe?%s,0,data_exchange'
                                  % self.customer_id, body)
        request.add_header('Content-type', content_type)
        result = urllib2.urlopen(request)
        lines = list(csv.reader(result, dialect=CollmexDialect))
        response = lines.pop()
        record_type, message_type, message_id, message_text = response
        if record_type != 'MESSAGE':
            raise TypeError('API returned invalid response record: %r' % response)
        if message_type != 'S':
            raise APIError(message_id, message_text)
        return lines


def date_to_collmex(date):
    if date == Collmex.NULL:
        return date
    else:
        return date.strftime('%Y%m%d')


class InvoiceItem(UserDict.UserDict):
    zope.interface.implements(gocept.collmex.interfaces.IInvoiceItem)

    def __init__(self, row=[]):
        UserDict.UserDict.__init__(self)

        self['Satzart'] = 'CMXINV'
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
                    value = value.encode('iso-8859-1')
                yield value
            else:
                yield Collmex.NULL

    fields = [
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
        ]
