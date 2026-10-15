import unittest

import zope.interface.verify

import gocept.collmex.interfaces
import gocept.collmex.testing


class TestCreateProjects(unittest.TestCase):
    def setUp(self):
        import gocept.collmex.testing

        gocept.collmex.testing.cleanup_collmex()

    def test_creates_product_if_missing(self):
        import gocept.collmex.testing

        gocept.collmex.testing.create_project("project title")
        collmex = gocept.collmex.testing.get_collmex()
        self.assertEqual(
            ["TEST"], [prod["Produktnummer"] for prod in collmex.get_products()]
        )


class ConsoleDumpTest(unittest.TestCase):
    def test_implements_interface(self):
        zope.interface.verify.verifyObject(
            gocept.collmex.interfaces.ICollmex,
            gocept.collmex.testing.ConsoleDump(),
        )
