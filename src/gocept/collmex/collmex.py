import csv
import io
import logging
import os
import re
import threading
import urllib.request

import gocept.cache.method
import gocept.cache.property
import transaction
import transaction.interfaces
import webtest
import zope.deprecation
import zope.interface
from zope.interface import implementer

import gocept.collmex.interfaces
import gocept.collmex.model
import gocept.collmex.utils

log = logging.getLogger(__name__)


class CollmexDialect(csv.Dialect):
    quoting = csv.QUOTE_ALL
    delimiter = ";"
    quotechar = '"'
    lineterminator = "\r\n"
    doublequote = True
    skipinitialspace = True


class APIError(Exception):
    pass


def get_api_url():
    """Returns the base URL of the Collmex server.

    This is ``https://www.collmex.de`` unless overridden by the
    ``COLLMEX_API_URL`` environment variable, e.g. to run tests against
    the faux Collmex server shipped with this package
    (see :mod:`gocept.collmex.faux`).
    """
    return os.environ.get("COLLMEX_API_URL", "https://www.collmex.de").rstrip(
        "/"
    )


@implementer(transaction.interfaces.IDataManager)
class CollmexDataManager:
    def __init__(self, utility):
        self.utility = utility
        self._reset()

    def _reset(self):
        self.data = io.StringIO()
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
                "Single phase data manager: cannot abort after vote"
            )
        self._reset()

    def tpc_finish(self, transaction):
        assert transaction is self._transaction
        self._reset()

    def sortKey(self):
        # XXX make very small or add single-phase datamanager integration to
        # the transaction module.
        return ""  # None


@implementer(gocept.collmex.interfaces.ICollmex)
class Collmex:
    # XXX should go on CollmexDialect but the csv module's magic prevents it
    NULL = gocept.collmex.interfaces.NULL

    encoding = "Windows-1252"  # Encoding used by Collmex
    # System name (C20) sent with queries. Collmex stores the date and
    # time of the last query of a record type server-side under this
    # name -- the basis of the "Nur geänderte" (only changed) mechanism.
    system_identifier = "gocept.collmex"

    def __init__(
        self,
        customer_id=None,
        company_id=None,
        username=None,
        password=None,
        system_identifier=None,
    ):
        # credentials are invalid if any argument is None or empty
        invalid_credentials = not all(
            [customer_id, company_id, username, password]
        )

        try:
            # try to use credentials from ini file 'collmex.ini'
            cred = gocept.collmex.utils.get_collmex_credentials()
        except OSError as error:
            if invalid_credentials:
                raise ValueError(
                    "Not enough credentials given for initialization and no "
                    "valid ini file found. Searching and parsing the ini file "
                    "gave the following error message: {error_message}".format(
                        error_message=str(error)
                    )
                )

        # any given argument will overwrite credentials from ini file
        self.customer_id = customer_id or cred.get("customer_id", None)
        self.company_id = company_id or cred.get("company_id", None)
        self.username = username or cred.get("username", None)
        self.password = password or cred.get("password", None)

        # A dedicated system name matters for tools relying on the
        # "Nur geänderte" (only changed) mechanism: Collmex stores the
        # date and time of the last query server-side per system name
        # and record type. All queries sending the same name advance
        # each other's watermark -- the class default is therefore
        # shared by all gocept.collmex users of an account.
        self.system_identifier = (
            system_identifier or type(self).system_identifier
        )
        if len(self.system_identifier) > 20:
            # Collmex restricts the system name to 20 characters (C20).
            raise ValueError(
                f"system_identifier is restricted to 20 characters by"
                f" Collmex (C20), got {self.system_identifier!r}"
                f" ({len(self.system_identifier)} characters)."
            )

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
        self._ensure_local_attribute("connection")
        if self._local.connection is None:
            self._local.connection = CollmexDataManager(self)
        return self._local.connection

    def create(self, item):
        data = io.StringIO()
        writer = csv.writer(data, dialect=CollmexDialect)
        item.company = self.company_id
        writer.writerow([elem for elem in list(item)])
        self.connection.register_data(data.getvalue())

    def create_invoice(self, items):
        # Trigger reset of invoice ids if this is a new transaction
        self.connection

        id = self.generate_invoice_id()
        for item in items:
            item["Rechnungsnummer"] = id
            self.create(item)

    def create_product(self, product):
        # This is an deprecated API. Use ``create`` instead.
        self.create(product)

    def create_customer(self, customer):
        # This is an deprecated API. Use ``create`` instead.
        self.create(customer)

    def get_invoices(
        self,
        invoice_id=NULL,
        customer_id=NULL,
        start_date=NULL,
        end_date=NULL,
        only_changed=NULL,
    ):
        """Returns a list of IInvoiceItems matching given criteria.

        With ``only_changed=1`` only invoices changed or newly created
        since the last INVOICE_GET of this ``system_identifier`` are
        returned. Collmex advances this watermark when the query
        executes -- regardless of whether the caller manages to
        process the result -- so callers should be able to fall back
        to a full query. Deletions are never reported.
        """
        return self._query_objects(
            "INVOICE_GET",
            invoice_id,
            self.company_id,
            customer_id,
            date_to_collmex(start_date),
            date_to_collmex(end_date),
            0,
            0,
            only_changed,
            self.system_identifier,
        )

    def get_customers(self, customer_id=NULL, text=NULL):
        return self._query_objects(
            "CUSTOMER_GET",
            customer_id,
            self.company_id,
            text,
            0,
            self.NULL,
            self.NULL,
            self.NULL,
            self.NULL,
            self.NULL,
            0,
            self.system_identifier,
        )

    def get_members(self, member_id=NULL, text=NULL, include_inactive=True):
        return self._query_objects(
            "MEMBER_GET",
            member_id,
            self.company_id,
            text,
            self.NULL,  # plz/country
            0,  # address group
            int(include_inactive),  # 1 -- auch ausgetretene
            0,  # 1 -- only changed since last call
            self.system_identifier,
        )

    def get_products(
        self, product_id=NULL, product_group=NULL, price_group=NULL
    ):
        return self._query_objects(
            "PRODUCT_GET",
            self.company_id,
            product_id,
            product_group,
            price_group,
            0,
            self.system_identifier,
        )

    def get_customer_agreements(
        self,
        customer_id=NULL,
        product_id=NULL,
        valid_on_date=NULL,
        inactive=NULL,
        only_changed=NULL,
    ):
        return self._query_objects(
            "CUSTOMER_AGREEMENT_GET",
            self.company_id,
            customer_id,
            product_id,
            date_to_collmex(valid_on_date),
            inactive,
            only_changed,
            self.system_identifier,
        )

    def get_projects(self, project_id=NULL, customer_id=NULL):
        return self._query_objects(
            "PROJECT_GET", project_id, self.company_id, customer_id
        )

    def get_activities(
        self,
        project_id=NULL,
        employee_id=NULL,
        start_date=NULL,
        end_date=NULL,
        only_non_billed=NULL,
        billable=NULL,
        only_non_internal=NULL,
        only_changed=NULL,
    ):
        """Returns a list of IActivities matching given criteria.

        With ``only_changed=1`` only activities changed or newly
        created since the last ACTIVITIES_GET of this
        ``system_identifier`` are returned. Collmex advances this
        watermark when the query executes -- regardless of whether the
        caller manages to process the result -- so callers should be
        able to fall back to a full query. Deletions are never
        reported.
        """
        return self._query_objects(
            "ACTIVITIES_GET",
            project_id,
            self.company_id,
            employee_id,
            date_to_collmex(start_date),
            date_to_collmex(end_date),
            only_non_billed,
            billable,
            only_non_internal,
            only_changed,
            self.system_identifier,
        )

    def browser_login(self):
        """Log into Collmex using a browser.

        Raises a ValueError when Collmex responds with an error, containing the
        error message from Collmex. Common errors are:

        * invalid credentials
        * disabled login, due to too many failed logins

        """
        b = webtest.TestApp(get_api_url()).get("/")
        b.charset = self.encoding

        f = b.form
        f["Kunde"] = self.customer_id
        b = f.submit().maybe_follow()
        b.charset = self.encoding

        f = b.form
        f["group_benutzerId"] = self.username
        f["group_kennwort"] = self.password
        b = f.submit().maybe_follow()
        b.charset = self.encoding

        body = b.body.decode(self.encoding)
        error = re.search('<p class="error">(.*?)</p>', body)
        if error is not None:
            raise ValueError(error.group(1))

        return b

    def _get_cache(self):
        self._ensure_local_attribute("cache")
        if self._local.cache is None:
            self._local.cache = {}
            dm = gocept.cache.property.CacheDataManager(
                self, None, transaction.get()
            )
            transaction.get().join(dm)
        return self._local.cache

    def _set_cache(self, cache):
        self._local.cache = cache

    _cache = property(_get_cache, _set_cache)

    # hook for gocept.cache.property.CacheDataManager
    def invalidate(self, dummy):
        self._cache = None

    @gocept.cache.method.memoize_on_attribute("_cache", timeout=5 * 60)
    def _query_objects(self, function, *args):
        data = io.StringIO()
        writer = csv.writer(data, dialect=CollmexDialect)
        writer.writerow([elem for elem in (function,) + args])
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
        data = data.decode("UTF-8") if isinstance(data, bytes) else data
        data = "LOGIN;{};{}\n".format(self.username, self.password) + data
        log.debug(data.replace(self.password, "<PASSWORD>"))
        content_type, body = gocept.collmex.utils.encode_multipart_formdata(
            [], [("fileName", "api.csv", data)]
        )

        url = "%s/cgi-bin/cgi.exe?%s,0,data_exchange" % (
            get_api_url(),
            self.customer_id,
        )
        content_type_label = "Content-type"

        body = body.encode(self.encoding)

        request = urllib.request.Request(url, body)
        request.add_header(content_type_label, content_type)
        response = urllib.request.urlopen(request)

        response = io.StringIO(response.read().decode(self.encoding))

        lines = list(csv.reader(response, dialect=CollmexDialect))

        response.close()
        result = lines.pop()
        assert len(result) >= 4

        record_type, message_type, message_id, message_text = result[:4]
        if record_type != "MESSAGE":
            raise TypeError("API returned invalid response record: %r" % result)
        if message_type != "S":
            raise APIError(message_id, message_text)
        return lines


def date_to_collmex(date):
    """Converts a date into Collmex' D8 format (YYYYMMDD).

    ``datetime.date`` and ``datetime.datetime`` objects are formatted
    accordingly; strings pass through unchanged so pre-formatted dates
    keep working.
    """
    if date == Collmex.NULL or isinstance(date, str):
        return date
    return date.strftime("%Y%m%d")


# Backward compatibility
InvoiceItem = gocept.collmex.model.InvoiceItem
zope.deprecation.deprecated(
    "InvoiceItem",
    "InvoiceItem has been moved to gocept.collmex.model.InvoiceItem",
)
