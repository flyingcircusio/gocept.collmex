Collmex API
===========

Collmex provides a POST- and CSV-based API, which is encapsulated into a
utility that provides methods for the various CSV record types.  API
documentation is available at
http://www.collmex.de/cgi-bin/cgi.exe?1005,1,help,api.


The collmex object
------------------

The collmex object is a central place to access collmex. In the Zope 3 jargon
it is a global utility:

>>> import os
>>> import gocept.collmex.collmex
>>> collmex = gocept.collmex.collmex.Collmex(
...     os.environ['collmex_customer'], os.environ['collmex_company'],
...     os.environ['collmex_username'], os.environ['collmex_password'])


Transaction integration
-----------------------

gocept.collmex has support for transaction integration. All modifying calls are
buffered until the transaction is commited. XXX explain more.

[#pre-flight-cleanup]_ [#invalid-login]_

>>> import transaction


Customers: ``create_customer`` and ``get_customers``
----------------------------------------------------

>>> customer = gocept.collmex.model.Customer()
>>> customer['Kundennummer'] = 10000
>>> customer['Firma'] = 'Testkunden'
>>> collmex.create_customer(customer)
>>> transaction.commit()

Customers can be listed using the get_customers method:

>>> customers = collmex.get_customers()
>>> customers
[<gocept.collmex.model.Customer object at 0x...>,
 <gocept.collmex.model.Customer object at 0x...>]
>>> len(customers)
2

The first customer is the generic one:

>>> customer = customers[0]
>>> customer['Satzart']
u'CMXKND'
>>> customer['Kundennummer']
u'9999'
>>> customer['Firma']
u'Allgemeiner Gesch\xe4ftspartner'


The second customer is one created during test setup:

>>> customer = customers[1]
>>> customer['Satzart']
u'CMXKND'
>>> customer['Kundennummer']
u'10000'
>>> customer['Firma']
u'Testkunden'

Products: ``create_product`` and ``get_products``
-------------------------------------------------

Products are created using the ``create_product`` method:

>>> product = gocept.collmex.model.Product()
>>> product['Produktnummer'] = 'TEST'
>>> product['Bezeichnung'] = 'Testprodukt'
>>> product['Produktart'] = 1 # Dienstleistung
>>> product['Basismengeneinheit'] = 'HR'
>>> product['Verkaufs-Preis'] = 5
>>> collmex.create_product(product)
>>> transaction.commit()
>>> collmex.get_products()[0]['Bezeichnung']
u'Testprodukt'

Invoices: ``create_invoice`` and ``get_invoices``
-------------------------------------------------

Invoices are created using the ``create_invoice`` method:

>>> import datetime
>>> start_date = datetime.datetime.now()
>>> item = gocept.collmex.model.InvoiceItem()
>>> item['Kunden-Nr'] = '10000'
>>> item['Rechnungsnummer'] = 100000
>>> item['Menge'] = 3
>>> item['Produktnummer'] = 'TEST'
>>> item['Rechnungstext'] = u'item text \u2013 with non-ascii characters'
>>> item['Positionstyp'] = 0
>>> collmex.create_invoice([item])

Invoices can be looked up again, using the ``get_invoices`` method. However, as
discussed above the invoice was only registered for addition. Querying right
now does *not* return the invoice:

>>> collmex.get_invoices(customer_id='10000', start_date=start_date)
[]

After committing, the invoice is found:

>>> transaction.commit()
>>> collmex.get_invoices(customer_id='10000',
...                      start_date=start_date)[0]['Rechnungstext']
u'item text \u2013 with non-ascii characters'

Activities
----------

This section describes the API for activities (Taetigkeiten erfassen). A
project with one set and an employee are required to submit activities:

>>> import datetime
>>> today = datetime.date.today()
>>> import gocept.collmex.testing
>>> gocept.collmex.testing.create_projects()
>>> gocept.collmex.testing.create_employee()
>>> act = gocept.collmex.model.Activity()
>>> act['Projekt Nr'] = '1' # Testprojekt
>>> act['Mitarbeiter Nr'] = '1' # Sebastian Wehrmann
>>> act['Satz Nr'] = '1' # TEST
>>> act['Beschreibung'] = u'allgemeine T\xe4tigkeit'
>>> act['Datum'] = today
>>> act['Von'] = datetime.time(8, 7)
>>> act['Bis'] = datetime.time(14, 28)
>>> act['Pausen'] = datetime.timedelta(hours=1, minutes=12)
>>> collmex.create(act)
>>> transaction.commit()

[#check-activity-creation]_

Projects: ``get_projects``
--------------------------

Projects can be exported with the ``get_projects`` API. It returns an entry
for every project set (Projektsatz) of each project (Projekt):

>>> proj = collmex.get_projects()
>>> len(proj)
2
>>> proj[0]['Projektnummer'] == proj[1]['Projektnummer']
True

>>> proj[0]['Satz']
u'5,00'
>>> proj[1]['Satz']
u'9,65'

Caching
-------

Results queried from Collmex are cached for the duration of the transaction.

To demonstrate this, we instrument the _post() method that performs the actual
HTTP communication to show when it is called:

    >>> original_post = collmex._post
    >>> def tracing_post(self, *args, **kw):
    ...     print 'cache miss'
    ...     return original_post(*args, **kw)
    >>> collmex._post = tracing_post.__get__(collmex, type(collmex))

The first time in an transaction is retrieved from Collmex, of course:

    >>> transaction.abort()
    >>> collmex.get_products()[0]['Bezeichnung']
    cache miss
    u'Testprodukt'

But after that, values are cached:

    >>> collmex.get_products()[0]['Bezeichnung']
    u'Testprodukt'

When the transaction ends, the cache is invalidated:

    >>> transaction.commit()
    >>> collmex.get_products()[0]['Bezeichnung']
    cache miss
    u'Testprodukt'
    >>> collmex.get_products()[0]['Bezeichnung']
    u'Testprodukt'

Remove tracing instrumentation:

    >>> collmex._post = original_post


.. [#pre-flight-cleanup] First we need to clean up the Collmex environment:

    >>> import gocept.collmex.testing
    >>> gocept.collmex.testing.cleanup_collmex()

.. [#check-activity-creation] Check if an activity was imported:

    >>> import gocept.collmex.testing
    >>> b = gocept.collmex.testing.collmex_login()
    >>> b.getLink('Verkauf').click()
    >>> b.getLink('T\xe4tigkeiten erfassen').click()
    >>> b.getControl(name='table_1_datum').value == today.strftime('%d.%m.%Y')
    True
    >>> b.getControl(name='table_1_von').value
    '08:07'
    >>> b.getControl(name='table_1_bis').value
    '14:28'
    >>> b.getControl(name='table_1_pausen').value
    '1:12'
    >>> b.getControl(name='table_1_beschreibung').value
    'allgemeine T\xe4tigkeit'

.. [#invalid-login] Invalid login information raises an exception:

    >>> collmex_invalid = gocept.collmex.collmex.Collmex(
    ...     os.environ['collmex_customer'], os.environ['collmex_company'],
    ...     os.environ['collmex_username'], 'invalid')
    >>> collmex_invalid.get_invoices(customer_id='10000')
    Traceback (most recent call last):
        ...
    APIError: ('101004', 'Benutzer oder Kennwort nicht korrekt')
