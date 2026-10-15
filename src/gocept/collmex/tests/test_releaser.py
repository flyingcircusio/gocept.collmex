import sys
import unittest
from unittest import mock

import gocept.collmex.releaser


class DisableHistoryUpdateTest(unittest.TestCase):
    def test_sets_update_history_false_for_this_package(self):
        data = {"name": "gocept.collmex", "update_history": True}
        gocept.collmex.releaser.disable_history_update(data)
        self.assertFalse(data["update_history"])

    def test_ignores_other_packages(self):
        data = {"name": "other.package", "update_history": True}
        gocept.collmex.releaser.disable_history_update(data)
        self.assertTrue(data["update_history"])


class CollectChangelogTest(unittest.TestCase):
    def data(self):
        return {
            "name": "gocept.collmex",
            "new_version": "3.0",
            "workingdir": "/tmp/workdir",
        }

    def test_runs_scriv_collect_with_release_version(self):
        data = self.data()
        with (
            mock.patch("gocept.collmex.releaser.subprocess.run") as run,
            mock.patch.object(sys, "executable", "python"),
        ):
            run.return_value = mock.Mock(returncode=0)
            gocept.collmex.releaser.collect_changelog(data)
        run.assert_called_once_with(
            ["python", "-m", "scriv", "collect", "--version", "3.0"],
            cwd="/tmp/workdir",
            check=False,
        )

    def test_ignores_other_packages(self):
        data = self.data()
        data["name"] = "other.package"
        with mock.patch("gocept.collmex.releaser.subprocess.run") as run:
            gocept.collmex.releaser.collect_changelog(data)
        run.assert_not_called()

    def test_tolerates_missing_fragments(self):
        data = self.data()
        with mock.patch("gocept.collmex.releaser.subprocess.run") as run:
            run.return_value = mock.Mock(returncode=2)
            gocept.collmex.releaser.collect_changelog(data)

    def test_raises_on_scriv_error(self):
        data = self.data()
        with mock.patch("gocept.collmex.releaser.subprocess.run") as run:
            run.return_value = mock.Mock(returncode=1)
            with self.assertRaises(RuntimeError):
                gocept.collmex.releaser.collect_changelog(data)
