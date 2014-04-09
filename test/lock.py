#!/usr/bin/env python
# encoding: utf-8

"""test lock
"""
from multiprocessing import Lock


class TestLock(object):
    def __init__(self):
        self.lock = Lock()

#    def do(self, msg):
#        with self.lock:
#            f = open("./lock.txt", "a")
#            f.write(msg + "\n")
#            f.close()

    def do(self, msg):
        f = open("./lock.txt", "a")
        f.write(msg + "\n")
        import time
        time.sleep(5)
        f.close()
