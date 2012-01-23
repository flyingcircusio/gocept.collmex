# Copyright (c) 2008-2012 gocept gmbh & co. kg
# See also LICENSE.txt

import gocept.collmex.testing
import os
import Queue
import unittest
import threading


class Worker(threading.Thread):
    def __init__(self, collmex, queue):
        super(Worker, self).__init__()
        self.collmex = collmex
        self.queue = queue

    def run(self):
        self.queue.put_nowait(self.collmex.get_products())


class ThreadTest(unittest.TestCase):
    def test_two_threads_can_access_their_caches(self):
        collmex = gocept.collmex.testing.get_collmex()
        queue = Queue.Queue(-1)
        workers = []
        for i in range(2):
            w = Worker(collmex, queue)
            workers.append(w)
            w.start()
        for w in workers: w.join()
        self.assertEqual(2, queue.qsize())
