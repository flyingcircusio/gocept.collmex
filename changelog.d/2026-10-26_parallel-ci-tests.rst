- Parallelise the GitHub test workflow: only ``py312-live`` (which uses
  the shared Collmex test system) runs exclusively, all other test
  environments now run in parallel.
