# Copyright (c) 2008-2012 gocept gmbh & co. kg
# See also LICENSE.txt

import gocept.collmex.testing
import queue
import threading
import unittest


class Worker(threading.Thread):
    def __init__(self, collmex, queue):
        super().__init__()
        self.collmex = collmex
        self.queue = queue

    def run(self):
        self.queue.put_nowait(self.collmex.get_products())


class ThreadTest(unittest.TestCase):
    def test_two_threads_can_access_their_caches(self):
        collmex = gocept.collmex.testing.get_collmex()
        my_queue = queue.Queue(-1)
        workers = []
        for i in range(2):
            w = Worker(collmex, my_queue)
            workers.append(w)
            w.start()
        for w in workers:
            w.join()
        self.assertEqual(2, my_queue.qsize())
