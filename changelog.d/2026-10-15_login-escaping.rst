- Fix: usernames or passwords containing ``;`` or ``"`` produced an
  invalid LOGIN row (and, with user-supplied credentials, allowed CSV
  injection). The login is now written through the regular CSV writer,
  so credentials are quoted and escaped correctly.
  (Contributed by Florian Best in
  `#35 <https://github.com/flyingcircusio/gocept.collmex/pull/35>`_)
