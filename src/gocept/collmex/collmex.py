# -*- coding: utf-8 -*-
# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

from __future__ import unicode_literals
import six
import csv
import gocept.cache.method
import gocept.cache.property
import gocept.collmex.interfaces
import gocept.collmex.model
import gocept.collmex.utils
import logging
import re
import threading
import transaction
import transaction.interfaces
try:
    import urllib.request as urllib2
except ImportError:
    import urllib2
import zope.deprecation
import zope.interface
from zope.interface import implementer
import webtest


log = logging.getLogger(__name__)


class CollmexDialect(csv.Dialect):
    quoting = csv.QUOTE_ALL
    if six.PY3:
        delimiter = ';'
        quotechar = '"'
        lineterminator = '\r\n'
    else:
        delimiter = b';'
        quotechar = b'"'
        lineterminator = b'\r\n'
    doublequote = True
    skipinitialspace = True


class APIError(Exception):
    pass


@implementer(transaction.interfaces.IDataManager)
class CollmexDataManager(object):

    def __init__(self, utility):
        self.utility = utility
        self._reset()

    def _reset(self):
        self.data = six.StringIO()
        self._joined = False
        self._transaction = None
        self.voted = False
        self.utility.reset_invoice_id()

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
            raise Exception(
                'Single phase data manager: cannot abort after vote')
        self._reset()

    def tpc_finish(self, transaction):
        assert transaction is self._transaction
        self._reset()

    def sortKey(self):
        # XXX make very small or add single-phase datamanager integration to
        # the transaction module.
        return ''  # None


@implementer(gocept.collmex.interfaces.ICollmex)
class Collmex(object):

    # XXX should go on CollmexDialect but the csv module's magic prevents it
    NULL = gocept.collmex.interfaces.NULL

    encoding = 'Windows-1252'  # Encoding used by Collmex
    system_identifier = 'gocept.collmex'

    def __init__(self, customer_id=None, company_id=None,
                 username=None, password=None):
        # credentials are invalid if any argument is None or empty
        invalid_credentials = not all(
            [customer_id, company_id, username, password])

        try:
            # try to use credentials from ini file 'collmex.ini'
            cred = gocept.collmex.utils.get_collmex_credentials()
        except IOError as error:
            if invalid_credentials:
                raise ValueError(
                    'Not enough credentials given for initialization and no '
                    'valid ini file found. Searching and parsing the ini file '
                    'gave the following error message: {error_message}'
                    .format(error_message=str(error)))

        # any given argument will overwrite credentials from ini file
        self.customer_id = customer_id or cred.get('customer_id', None)
        self.company_id = company_id or cred.get('company_id', None)
        self.username = username or cred.get('username', None)
        self.password = password or cred.get('password', None)

        # Store thread-local (actually: transaction-local) information
        self._local = threading.local()

    def _ensure_local_attribute(self, name):
        if not getattr(self._local, name, None):
            setattr(self._local, name, None)

    def reset_invoice_id(self):
        # Collmex generates an invoice number if the one passed in is missing
        # or negative; the same negative number in one import call will assign
        # the same generated number.
        # NOTE: we need to start with -10000. -1 does not work.
        self._local.invoice_id = -10000

    def generate_invoice_id(self):
        self._local.invoice_id -= 1
        return self._local.invoice_id

    @property
    def connection(self):
        self._ensure_local_attribute('connection')
        if self._local.connection is None:
            self._local.connection = CollmexDataManager(self)
        return self._local.connection

    def create(self, item):
        data = six.StringIO()
        writer = csv.writer(data, dialect=CollmexDialect)
        item.company = self.company_id
        writer.writerow([elem.encode('UTF-8')
                        if isinstance(elem, six.text_type) and six.PY2
                        else elem for elem in list(item)])
        self.connection.register_data(data.getvalue())

    def create_invoice(self, items):
        # Trigger reset of invoice ids if this is a new transaction
        self.connection

        id = self.generate_invoice_id()
        for item in items:
            item['Rechnungsnummer'] = id
            self.create(item)

    def create_product(self, product):
        # This is an deprecated API. Use ``create`` instead.
        self.create(product)

    def create_customer(self, customer):
        # This is an deprecated API. Use ``create`` instead.
        self.create(customer)

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

    def get_products(self, product_id=NULL,
                     product_group=NULL, price_group=NULL):
        return self._query_objects(
            'PRODUCT_GET',
            self.company_id,
            product_id,
            product_group,
            price_group,
            0, self.system_identifier)

    def get_projects(self, project_id=NULL, customer_id=NULL):
        return self._query_objects(
            'PROJECT_GET',
            project_id,
            self.company_id,
            customer_id)

    def get_activities(self, project_id=NULL,
                       employee_id=NULL,
                       start_date=NULL, end_date=NULL,
                       only_non_billed=NULL, billable=NULL,
                       only_non_internal=NULL,
                       only_changed=NULL):
        return self._query_objects(
            'ACTIVITIES_GET',
            project_id,
            self.company_id,
            employee_id,
            start_date, end_date,
            only_non_billed, billable,
            only_non_internal,
            only_changed, self.system_identifier)

    def browser_login(self):
        """Log into Collmex using a browser.

        Raises a ValueError when Collmex responds with an error, containing the
        error message from Collmex. Common errors are:

        * invalid credentials
        * disabled login, due to too many failed logins

        """
        b = webtest.TestApp('https://www.collmex.de').get('/')
        b.charset = self.encoding

        f = b.form
        f['Kunde'] = self.customer_id
        b = f.submit().maybe_follow()
        b.charset = self.encoding

        f = b.form
        f['group_benutzerId'] = self.username
        f['group_kennwort'] = self.password
        b = f.submit().maybe_follow()
        b.charset = self.encoding

        body = b.body.decode(self.encoding)
        error = re.search('<p class="error">(.*?)</p>', body)
        if error is not None:
            raise ValueError(error.group(1))

        return b

    def _get_cache(self):
        self._ensure_local_attribute('cache')
        if self._local.cache is None:
            self._local.cache = {}
            dm = gocept.cache.property.CacheDataManager(
                self, None, transaction.get())
            transaction.get().join(dm)
        return self._local.cache

    def _set_cache(self, cache):
        self._local.cache = cache

    _cache = property(_get_cache, _set_cache)

    # hook for gocept.cache.property.CacheDataManager
    def invalidate(self, dummy):
        self._cache = None

    @gocept.cache.method.memoize_on_attribute('_cache', timeout=5 * 60)
    def _query_objects(self, function, *args):
        data = six.StringIO()
        writer = csv.writer(data, dialect=CollmexDialect)
        writer.writerow([elem.encode('UTF-8')
                        if isinstance(elem, six.text_type) and six.PY2
                        else elem
                        for elem in (function,) + args])
        lines = self._post(data.getvalue())
        result = []
        for line in lines:
            record_type = line[0]
            factory = gocept.collmex.model.factory(record_type)
            if factory is None:
                continue
            result.append(factory(line))
        return result

    def _post(self, data):
        data = (data.decode('UTF-8')
                if isinstance(data, six.binary_type)
                else data)
        data = 'LOGIN;%s;%s\n' % (self.username, self.password) + data
        log.debug(data.replace(self.password, '<PASSWORD>'))
        content_type, body = gocept.collmex.utils.encode_multipart_formdata(
            [], [('fileName', 'api.csv', data)])

        url = ('https://www.collmex.de/cgi-bin/cgi.exe?%s,0,data_exchange'
               % self.customer_id)
        content_type_label = 'Content-type'

        if six.PY2:
            url, body, content_type_label, content_type = [
                text.encode(self.encoding) for text in
                [url, body, content_type_label, content_type]]
        else:
            body = body.encode(self.encoding)

        request = urllib2.Request(url, body)
        request.add_header(content_type_label, content_type)
        response = urllib2.urlopen(request)

        if six.PY3:
            response = six.StringIO(response.read().decode(self.encoding))

        lines = list(csv.reader(response, dialect=CollmexDialect))

        if six.PY2:
            lines = [[line.decode(self.encoding) for line in ls]
                     for ls in lines]
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
