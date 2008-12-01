# -*- coding: utf-8 -*-
# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

import StringIO
import csv
import gocept.collmex.interfaces
import gocept.collmex.model
import gocept.collmex.utils
import logging
import threading
import transaction
import transaction.interfaces
import urllib2
import zope.deprecation
import zope.interface


log = logging.getLogger(__name__)

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
        self.voted = False

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
        # We need to do our work in tpc_vote as we're a single-phase-only data 
        # manager.
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
    NULL = gocept.collmex.interfaces.NULL

    system_identifier = 'gocept.collmex'

    model_factory = {
        'CMXINV': gocept.collmex.model.InvoiceItem,
        'CMXKND': gocept.collmex.model.Customer,
    }

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
        return self._query_objects(
            'INVOICE_GET',
            invoice_id,
            self.company_id,
            customer_id,
            date_to_collmex(start_date),
            date_to_collmex(end_date),
            0, 0,
            0, self.system_identifier)

    def get_customers(self, customer_id=NULL, text=NULL):
        return self._query_objects(
            'CUSTOMER_GET',
            customer_id,
            self.company_id,
            text,
            0, self.NULL, self.NULL, self.NULL, self.NULL, self.NULL,
            0, self.system_identifier)

    def _query_objects(self, function, *args):
        data = StringIO.StringIO()
        writer = csv.writer(data, dialect=CollmexDialect)
        writer.writerow((function,) + args)
        lines = self._post(data.getvalue())
        result = []
        for line in lines:
            record_type = line[0]
            factory = self.model_factory.get(record_type)
            if factory is None:
                continue
            result.append(factory(line))
        return result



    def _post(self, data):
        data = 'LOGIN;%s;%s\n' % (self.username, self.password) + data
        log.debug(data)
        content_type, body = gocept.collmex.utils.encode_multipart_formdata(
            [], [('fileName', 'api.csv', data)])
        request = urllib2.Request(
            'https://www.collmex.de/cgi-bin/cgi.exe?%s,0,data_exchange'
            % self.customer_id, body)
        request.add_header('Content-type', content_type)
        response = urllib2.urlopen(request)

        lines = list(csv.reader(response, dialect=CollmexDialect))
        response.close()
        result = lines.pop()
        assert len(result) >= 4

        record_type, message_type, message_id, message_text = (
            result[:4])
        if record_type != 'MESSAGE':
            raise TypeError('API returned invalid response record: %r' %
                            result)
        if message_type != 'S':
            raise APIError(message_id, message_text)
        return lines


def date_to_collmex(date):
    if date == Collmex.NULL:
        return date
    else:
        return date.strftime('%Y%m%d')


# Backward compatibility
InvoiceItem = gocept.collmex.model.InvoiceItem
zope.deprecation.deprecated(
    'InvoiceItem',
    'InvoiceItem has been moved to gocept.collmex.model.InvoiceItem')
