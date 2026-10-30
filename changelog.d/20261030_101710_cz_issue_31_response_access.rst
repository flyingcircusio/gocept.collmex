- New: IDs assigned by Collmex ("interne Nummernvergabe") can be
  retrieved. For customers, members and invoices created without an ID,
  a temporary number is substituted automatically; after a successful
  ``transaction.commit()`` the ID assigned by Collmex is written back
  onto the objects passed to ``create()``, and all positions of an
  invoice created with ``create_invoice()`` carry their assigned
  invoice number. The complete raw response of the last write is
  available as ``collmex.last_response``, with
  ``gocept.collmex.collmex.new_object_ids()`` extracting the
  ``NEW_OBJECT_ID`` assignments.
  (`#31 <https://github.com/flyingcircusio/gocept.collmex/issues/31>`_)
- The faux Collmex server emulates the internal numbering: it assigns
  numbers for records with empty or negative keys and reports them as
  ``NEW_OBJECT_ID`` records, so the new features can be tested offline.
