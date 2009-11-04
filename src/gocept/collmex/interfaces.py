# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

import zope.interface
import zope.interface.common.mapping

# NULL aka None for Collmex
NULL = "(NULL)"


class ICollmex(zope.interface.Interface):
    """Python binding for the Collmex API."""

    def create_invoice(items):
        """Creates an invoice consisting of the given IInvoiceItems."""

    def create_product(product):
        """Creates a product for the given IProduct."""

    def get_invoices(invoice_id=NULL, customer_id=NULL,
                     start_date=NULL, end_date=NULL):
        """Returns a list of IInvoiceItems maching given criteria."""

    def get_customers(customer_id=NULL, text=NULL):
        """Returns a list of ICustomers matching given criteria."""

    def get_products(product_id=NULL, product_group=NULL, price_group=NULL):
        """Returns a list of IProducts matching given criteria."""


class IModel(zope.interface.common.mapping.IFullMapping):
    """A collmex model.

    A collmex model mapps the field names specified by the API to their
    respective values.

    """

    satzart = zope.interface.Attribute("The collmex model indicator.")

    def __iter__(self):
        """Iterate over vields in order specified by collmex API."""


class IInvoiceItem(IModel):
    """An invoice item (CMXINV)"""


class ICustomer(IModel):
    """A customer (CMXKND)."""


class IProduct(IModel):
    """A product (CMXPRD)."""


class IActivity(IModel):
    """A product (CMXACT)."""


class IProject(IModel):
    """A project (CMXPRJ)."""
