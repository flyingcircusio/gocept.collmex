# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

import gocept.collmex.collmex
import os
import Queue
import unittest
import threading
import zope.testing.doctest


class Worker(threading.Thread):
    def __init__(self, collmex, queue):
        super(Worker, self).__init__()
        self.collmex = collmex
        self.queue = queue

    def run(self):
        self.queue.put_nowait(self.collmex.get_products())


class ThreadTest(unittest.TestCase):
    def test_two_threads_can_access_their_caches(self):
        collmex = gocept.collmex.collmex.Collmex(
            os.environ['collmex_customer'], os.environ['collmex_company'],
            os.environ['collmex_username'], os.environ['collmex_password'])
        queue = Queue.Queue(-1)
        workers = []
        for i in range(2):
            w = Worker(collmex, queue)
            workers.append(w)
            w.start()
        for w in workers: w.join()
        self.assertEqual(2, queue.qsize())


class ModelTest(unittest.TestCase):

    def test_model_robust_agains_extension(self):

        class TestModel(gocept.collmex.model.Model):

            zope.interface.implements(gocept.collmex.interfaces.IInvoiceItem)

            satzart = 'CMXINV'
            fields = (
                'Satzart',
                'Rechnungsnummer',
            )

        tm = TestModel(['CMXINV', 'foo', 'bar', ''])
        self.assertEqual('foo', tm['Rechnungsnummer'])
        self.assertEqual(['bar', None], tm._unmapped)


optionflags = (zope.testing.doctest.INTERPRET_FOOTNOTES |
               zope.testing.doctest.NORMALIZE_WHITESPACE |
               zope.testing.doctest.ELLIPSIS)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ThreadTest))
    suite.addTest(unittest.makeSuite(ModelTest))
    suite.addTest(zope.testing.doctest.DocFileSuite(
        'README.txt',
        optionflags=optionflags))
    return suite
