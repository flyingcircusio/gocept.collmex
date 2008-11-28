Collmex API
===========

Collmex provides a POST- and CSV-based API, which is encapsulated into a
utility that provides methods for the various CSV record types.  API
documentation is available at
http://www.collmex.de/cgi-bin/cgi.exe?1005,1,help,api.


Transaction integration
-----------------------

gocept.collmex has support for transaction integration. All modifying calls are
buffered until the transaction is commited. XXX explain more.

[#pre-flight-cleanup]_[#invalid-login]_


Invoices
--------

Invoices are created using the ``create_invoice`` method:

>>> import datetime
>>> collmex = gocept.collmex.collmex.Collmex(
...     os.environ['collmex_customer'], os.environ['collmex_company'],
...     os.environ['collmex_username'], os.environ['collmex_password'])
>>> start_date = datetime.datetime.now()
>>> item = gocept.collmex.collmex.InvoiceItem()
>>> item['Kunden-Nr'] = '10000'
>>> item['Rechnungsnummer'] = 100000
>>> item['Menge'] = 3
>>> item['Produktnummer'] = 'TRAFFIC'
>>> item['Rechnungstext'] = 'item text'
>>> item['Positionstyp'] = 0
>>> collmex.create_invoice([item])



Invoices can be looked up again, using the ``get_invoices`` method. However, as
discussed above the invoice was only registered for addition. Querying right
now does *not* return the invoice:

>>> collmex.get_invoices(customer_id='10000', start_date=start_date)
[]

After committing, the invoice is found:

>>> import transaction
>>> transaction.commit()
>>> collmex.get_invoices(customer_id='10000',
...                      start_date=start_date)[0]['Rechnungstext']
'item text'



.. [#pre-flight-cleanup] First we need to clean up the Collmex environment:

    >>> import gocept.collmex.testing
    >>> gocept.collmex.testing.cleanup_collmex()

.. [#invalid-login] Invalid login information raises an exception:

    >>> import os
    >>> import gocept.collmex.collmex
    >>> collmex = gocept.collmex.collmex.Collmex(
    ...     os.environ['collmex_customer'], os.environ['collmex_company'],
    ...     os.environ['collmex_username'], 'invalid')
    >>> collmex.get_invoices(customer_id='10000')
    Traceback (most recent call last):
        ...
    APIError: ('101004', 'Benutzer oder Kennwort nicht korrekt')
