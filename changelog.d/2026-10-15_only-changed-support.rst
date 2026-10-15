- New: ``get_invoices()`` supports ``only_changed`` (INVOICE_GET field 9,
  "Nur geänderte") for incremental queries.

- New: ``Collmex(..., system_identifier=...)`` overrides the system name
  sent with queries; the default remains ``'gocept.collmex'``. Collmex
  stores the date and time of the last query per system name and record
  type -- the basis of the ``only_changed`` mechanism -- so tools relying
  on it should use a dedicated name (restricted to 20 characters by
  Collmex, longer names raise ``ValueError``).

- Fix: ``get_activities()`` converts ``start_date``/``end_date`` to
  Collmex' D8 format; ``date_to_collmex()`` now passes strings through
  unchanged.

- New: ``Activity`` maps the export-only fields ``Produkt Nr`` and
  ``In Rechnung Nr``; ``InvoiceItem`` maps the trailing fields
  ``Kunden-Referenz``, ``Schreibgeschützt``, ``Anzahlung`` and
  ``Anzahlungsbetrag``, so that live API responses are mapped completely.
