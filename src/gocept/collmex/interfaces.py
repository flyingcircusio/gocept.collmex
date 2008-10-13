# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

import zope.interface


class ICollmex(zope.interface.Interface):
    """Python binding for the Collmex API."""

    def create_invoice(items):
        """Creates an invoice consisting of the given IInvoiceItems."""


class IInvoiceItem(zope.interface.Interface):
    """An invoice item from Collmex.

    Must be able to convert itself into a list.
    """
