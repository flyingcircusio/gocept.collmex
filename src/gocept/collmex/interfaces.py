# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

import zope.interface

# NULL aka None for Collmex
NULL = "(NULL)"


class ICollmex(zope.interface.Interface):
    """Python binding for the Collmex API."""

    def create_invoice(items):
        """Creates an invoice consisting of the given IInvoiceItems."""

    def get_invoices(invoice_id=NULL, customer_id=NULL,
                     start_date=NULL, end_date=NULL):
        """Returns a list of IInvoiceItems maching given criteria."""


class IInvoiceItem(zope.interface.Interface):
    """An invoice item from Collmex.

    Must be able to convert itself into a list.
    """
