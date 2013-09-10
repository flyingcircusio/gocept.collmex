# -*- coding: utf-8 -*-
# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

from __future__ import unicode_literals
try:
    import io as StringIO
except ImportError:
    import StringIO
import csv
import gocept.cache.method
import gocept.cache.property
import gocept.collmex.interfaces
import gocept.collmex.model
import gocept.collmex.utils
import logging
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
import zope.testbrowser.browser
from wsgiproxy.proxies import HostProxy


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


@implementer(transaction.interfaces.IDataManager)
class CollmexDataManager(object):

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
            raise Exception(
                'Single phase data manager: cannot abort after vote')
        self._reset()

    def tpc_finish(self, transaction):
        assert transaction is self._transaction
        self._reset()

    def sortKey(self):
        # XXX make very small or add single-phase datamanager integration to
        # the transaction module.
        return '' # None


@implementer(gocept.collmex.interfaces.ICollmex)
class Collmex(object):

    # XXX should go on CollmexDialect but the csv module's magic prevents it
    NULL = gocept.collmex.interfaces.NULL

    system_identifier = 'gocept.collmex'

    def __init__(self, customer_id, company_id, username, password):
        self.customer_id = customer_id
        self.company_id = company_id
        self.username = username
        self.password = password

        # Store thread-local (actually: transaction-local) information
        self._local = threading.local()

    def _ensure_local_attribute(self, name):
        if not getattr(self._local, name, None):
            setattr(self._local, name, None)

    @property
    def connection(self):
        self._ensure_local_attribute('connection')
        if self._local.connection is None:
            self._local.connection = CollmexDataManager(self)
        return self._local.connection

    def create(self, item):
        data = StringIO.StringIO()
        writer = csv.writer(data, dialect=CollmexDialect)
        item.company = self.company_id
        writer.writerow(list(item))
        self.connection.register_data(data.getvalue())

    def create_invoice(self, items):
        # This is an deprecated API. Use ``create`` instead.
        for item in items:
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
        """Log into Collmex using a browser."""
        b = zope.testbrowser.browser.Browser(wsgi_app=HostProxy('https://www.collmex.de', client='requests'))
        # b = zope.testbrowser.browser.Browser(wsgi_app=HostProxy('http://www.collmex.de', client='requests'))
        b.testapp.restricted = False
        # b.handleErrors = False
        # b.raiseHttpErrors = False
        b._req_content_type = 'text/html'
        b._req_headers = {
            'Host': 'www.collmex.de',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'en-US,en;q=0.8',
            'Cookie': '__utma=230922765.2017575219.1378723311.1378723311.1378734339.2; __utmb=230922765.2.10.1378734339; __utmc=230922765; __utmz=230922765.1378723311.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)',
            'If-None-Match': "04fef4ba366ce1:0",
            'If-Modified-Since': 'Tue, 11 Jun 2013 12:57:58 GMT'
        }
        # b._req_headers = {
        #     'User-Agent': 'Python'
        # }
        #     'Accept-Charset': 'ISO-8859-1,UTF-8;q=0.7,*;q=0.7',
        #     'Accept-Encoding': 'gzip',
        #     'Cache-Control': 'no-cache',
        #     'Accept-Language': 'de,en;q=0.7,en-us;q=0.3'
        # }
        # GET / HTTP/1.1
        # Host: www.collmex.de
        # Connection: close[CRLF]
        # User-Agent: Web-sniffer/1.0.46 (+http://web-sniffer.net/)
        # Accept-Encoding: gzip
        # Accept-Charset: ISO-8859-1,UTF-8;q=0.7,*;q=0.7
        # Cache-Control: no-cache
        # Accept-Language: de,en;q=0.7,en-us;q=0.3
        # Referer: http://web-sniffer.net/
        # try:
        import pdb; pdb.set_trace()
        b.open('https://www.collmex.de')
        # except zope.testbrowser._compat.urllib_request.HTTPError as e:
        #     import pdb; pdb.set_trace()

        b.getControl(name='Kunde').value = self.customer_id
        b.getControl('Anmelden').click()

        b.getControl('Benutzer').value = self.username
        b.getControl('Kennwort').value = self.password
        b.getControl('Anmelden').click()
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

    @gocept.cache.method.memoize_on_attribute('_cache', timeout=5*60)
    def _query_objects(self, function, *args):
        data = StringIO.StringIO()
        writer = csv.writer(data, dialect=CollmexDialect)
        writer.writerow((function,) + args)
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
        data = 'LOGIN;%s;%s\n' % (self.username, self.password) + data
        log.debug(data)
        content_type, body = gocept.collmex.utils.encode_multipart_formdata(
            [], [('fileName', 'api.csv', data)])
        request = urllib2.Request(
            'https://www.collmex.de/cgi-bin/cgi.exe?%s,0,data_exchange'
            % self.customer_id, body)
        request.add_header('Content-type', content_type)
        response = urllib2.urlopen(request)
        response_content = response.read().decode('Windows-1252')

        lines = list(csv.reader(StringIO.StringIO(response_content), dialect=CollmexDialect))
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
