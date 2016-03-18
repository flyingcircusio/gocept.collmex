Collmex API
===========

Collmex provides a POST- and CSV-based API, which is encapsulated into a
utility that provides methods for the various CSV record types.  API
documentation is available at
http://www.collmex.de/cgi-bin/cgi.exe?1005,1,help,api.


Compatibility for Python 2 and 3
--------------------------------

We need to define this function to make the doctests compatible.

>>> def assert_equal(expected, returned):
...     if expected != returned:
...         raise AssertionError("{!r} != {!r}".format(expected, returned))

The collmex object
------------------

The collmex object is a central place to access collmex. In the Zope 3 jargon
it is a global utility:

>>> import os
>>> import gocept.collmex.collmex
>>> os.environ['collmex_credential_section'] = 'test-credentials'
>>> collmex = gocept.collmex.collmex.Collmex()


Pre flight cleanup
------------------

First we need to clean up the Collmex environment:

>>> import gocept.collmex.testing
>>> gocept.collmex.testing.cleanup_collmex()


Transaction integration
-----------------------

gocept.collmex has support for transaction integration. All modifying calls are
buffered until the transaction is commited. XXX explain more.

>>> import transaction


Customers: ``create_customer`` and ``get_customers``
----------------------------------------------------

>>> customer = gocept.collmex.model.Customer()
>>> customer[u'Kundennummer'] = 10000
>>> customer[u'Firma'] = u'Testkunden'
>>> collmex.create(customer)
>>> transaction.commit()

Customers can be listed using the get_customers method:

>>> customers = collmex.get_customers()
>>> customers
[<gocept.collmex.model.Customer object at 0x...>, <gocept.collmex.model.Customer object at 0x...>]
>>> len(customers)
2

The first customer is the generic one:

>>> customer = customers[0]
>>> assert_equal(u'CMXKND', customer[u'Satzart'])
>>> assert_equal(u'9999', customer[u'Kundennummer'])
>>> assert_equal(u'Allgemeiner Gesch\xe4ftspartner', customer[u'Firma'])

The second customer is one created during test setup:

>>> customer = customers[1]
>>> assert_equal(u'CMXKND', customer[u'Satzart'])
>>> assert_equal(u'10000', customer[u'Kundennummer'])
>>> assert_equal(u'Testkunden', customer[u'Firma'])

Products: ``create_product`` and ``get_products``
-------------------------------------------------

Products are created using the ``create_product`` method:

>>> product = gocept.collmex.model.Product()
>>> product[u'Produktnummer'] = u'TEST'
>>> product[u'Bezeichnung'] = u'Testprodukt'
>>> product[u'Produktart'] = 1 # Dienstleistung
>>> product[u'Basismengeneinheit'] = u'HR'
>>> product[u'Verkaufs-Preis'] = 5
>>> collmex.create(product)
>>> transaction.commit()
>>> assert_equal(u'Testprodukt', collmex.get_products()[0][u'Bezeichnung'])

Invoices: ``create_invoice`` and ``get_invoices``
-------------------------------------------------

Invoices are created using the ``create_invoice`` method:

>>> import datetime
>>> start_date = datetime.datetime.now()
>>> item = gocept.collmex.model.InvoiceItem()
>>> item[u'Kunden-Nr'] = u'10000'
>>> item[u'Rechnungsnummer'] = 100000
>>> item[u'Menge'] = 3
>>> item[u'Produktnummer'] = u'TEST'
>>> item[u'Rechnungstext'] = u'item text \u2013 with non-ascii characters'
>>> item[u'Positionstyp'] = 0
>>> collmex.create_invoice([item])

Invoices can be looked up again, using the ``get_invoices`` method. However, as
discussed above the invoice was only registered for addition. Querying right
now does *not* return the invoice:

>>> collmex.get_invoices(customer_id=u'10000', start_date=start_date)
[]

After committing, the invoice is found:

>>> transaction.commit()
>>> assert_equal(u'item text \u2013 with non-ascii characters',
...       collmex.get_invoices(customer_id=u'10000',
...                            start_date=start_date)[0][u'Rechnungstext'])

Activities
----------

This section describes the API for activities (Taetigkeiten erfassen)

Create an activity
~~~~~~~~~~~~~~~~~~

A project with one set and an employee are required to submit activities:

>>> import datetime
>>> import gocept.collmex.testing
>>> gocept.collmex.testing.create_project(u'Testprojekt')
>>> gocept.collmex.testing.create_employee()
>>> act = gocept.collmex.model.Activity()
>>> act[u'Projekt Nr'] = u'1' # Testprojekt
>>> act[u'Mitarbeiter Nr'] = u'1' # Sebastian Wehrmann
>>> act[u'Satz Nr'] = u'1' # TEST
>>> act[u'Beschreibung'] = u'allgemeine T\xe4tigkeit'
>>> act[u'Datum'] = datetime.date(2012, 1, 23)
>>> act[u'Von'] = datetime.time(8, 7)
>>> act[u'Bis'] = datetime.time(14, 28)
>>> act[u'Pausen'] = datetime.timedelta(hours=1, minutes=12)
>>> collmex.create(act)
>>> transaction.commit()

Export using ``get_activities``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``get_activities`` returns Activity objects.

.. ATTENTION:: In previous versions this method returnd a raw CSV string. This
      was due to Collmex not having an actual API.


>>> activities = collmex.get_activities()
>>> assert_equal(u'allgemeine T\xe4tigkeit', activities[0][u'Beschreibung'])


Projects: ``get_projects``
--------------------------

Projects can be exported with the ``get_projects`` API. It returns an entry
for every project set (Projektsatz) of each project (Projekt):

>>> proj = collmex.get_projects()
>>> len(proj)
2
>>> proj[0][u'Projektnummer'] == proj[1][u'Projektnummer']
True

>>> assert_equal(u'5,00', proj[0][u'Satz'])
>>> assert_equal(u'9,65', proj[1][u'Satz'])
>>> assert_equal(u'0', proj[0][u'Inaktiv'])

Caching
-------

Results queried from Collmex are cached for the duration of the transaction.

To demonstrate this, we instrument the _post() method that performs the actual
HTTP communication to show when it is called:

    >>> original_post = collmex._post
    >>> def tracing_post(self, *args, **kw):
    ...     print(u'cache miss')
    ...     return original_post(*args, **kw)
    >>> collmex._post = tracing_post.__get__(collmex, type(collmex))

The first time in an transaction is retrieved from Collmex, of course:

    >>> transaction.abort()
    >>> assert_equal(u'Testprodukt', collmex.get_products()[0][u'Bezeichnung'])
    cache miss

But after that, values are cached:

    >>> assert_equal(u'Testprodukt', collmex.get_products()[0][u'Bezeichnung'])

When the transaction ends, the cache is invalidated:

    >>> transaction.commit()
    >>> assert_equal(u'Testprodukt', collmex.get_products()[0][u'Bezeichnung'])
    cache miss

    >>> assert_equal(u'Testprodukt', collmex.get_products()[0][u'Bezeichnung'])

Remove tracing instrumentation:

    >>> collmex._post = original_post

