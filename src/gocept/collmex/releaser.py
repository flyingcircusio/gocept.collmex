"""zest.releaser integration for the scriv-managed changelog.

Registered via entry points in ``pyproject.toml``:

- ``prereleaser.before`` and ``postreleaser.before`` disable zest.releaser's
  own history file handling: the changelog belongs to scriv. zest.releaser
  would otherwise rewrite the last heading (adding the release date) or
  re-insert an ``(unreleased)`` section, neither of which exists in the
  fragment-based workflow.

- ``prereleaser.middle`` collects the fragments from ``changelog.d`` into
  ``CHANGES.rst``, using the release version zest.releaser just asked for.
  The version is passed explicitly, as ``pyproject.toml`` is only updated
  with the release version later on.

The entry points require gocept.collmex (this package) and scriv to be
installed in the same environment as zest.releaser, e.g. by running
releases via ``uv run fullrelease``.
"""

import subprocess
import sys


def disable_history_update(data):
    """Let scriv own CHANGES.rst, zest.releaser should not touch it."""
    if data["name"] != "gocept.collmex":
        return
    data["update_history"] = False


def collect_changelog(data):
    """Collect the changelog fragments with the version to be released."""
    if data["name"] != "gocept.collmex":
        return
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scriv",
            "collect",
            "--version",
            data["new_version"],
        ],
        cwd=data["workingdir"],
        check=False,
    )
    if result.returncode == 2:
        # No fragments pending, e.g. a release without user-visible
        # changes.
        return
    if result.returncode:
        raise RuntimeError(
            "scriv collect failed with exit code "
            f"{result.returncode}, is scriv installed?"
        )
