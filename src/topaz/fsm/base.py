#!/usr/bin/env python
# encoding: utf-8
"""event-driven state machine
"""
from multiprocessing import Process, Queue
from exceptions import NotImplementedError


class States(object):
    INIT = 0
    IDLE = 1
    WORK = 2
    ERROR = 3
    EXIT = 4


class IFunc(object):
    def __init__(self):
        self.queue = Queue()

    def init(self):
        raise NotImplementedError

    def idle(self):
        raise NotImplementedError

    def work(self):
        raise NotImplementedError

    def error(self):
        raise NotImplementedError

    def exit(self):
        raise NotImplementedError


class StateMachine(object):
    def __init__(self, ifunc):
        self.mf = ifunc
        self.q = ifunc.queue
        self.exit = False

    def run(self):
        p = Process(target=self.loop)
        p.start()

    def exit(self):
        self.q.empty()
        self.q.put(States.EXIT)

    def loop(self):
        while(not self.exit):
            s = self.q.get()
            if(s == States.INIT):
                self.mf.init()
            elif(s == States.IDLE):
                self.mf.idle()
            elif(s == States.ERROR):
                self.mf.error()
            elif(s == States.EXIT):
                self.mf.exit()
                self.exit = True
            else:
                self.mf.work(s)
