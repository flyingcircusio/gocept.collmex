Update the ``Product`` model (CMXPRD) to the current field layout: it now
maps all 67 documented fields instead of ending with an outdated
``Reserviert`` field at position 26. Notably, the fields ``Bemerkung``,
``Kosten``/``Kostenermittlung``, the supplier block (``EK-Lieferant``,
``EK-ProdNr d.Lieferanten``, ``EK-Preis``, ...) and ``Herkunftsland`` are
available now. The former shop (Webauftritt) fields 41-55 are reserved by
Collmex and kept as placeholders, as are the other reserved positions.

The field at position 16 has been renamed from ``EAN`` to ``GTIN``,
following Collmex; models using ``product["EAN"]`` have to be adapted.

(`#34 <https://github.com/flyingcircusio/gocept.collmex/issues/34>`_)
