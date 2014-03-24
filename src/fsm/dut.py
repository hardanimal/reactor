#!/usr/bin/env python
# encoding: utf-8

"""dut burnin functions
"""
import base
import logging
from multiprocessing import Queue
import time


class DUTStates(base.States):
    charging = 0xA0
    discharging = 0xA1


class DUT(base.IFunc):
    def __init__(self, dutid):
        self.dutid = dutid
        self.queue = Queue()

    def en_queue(self, state):
        self.queue.put(state)

    def init(self):
        logging.debug("dut" + str(self.dutid) + " in init")

    def idle(self):
        logging.debug("dut" + str(self.dutid) + " in idle")

    def work(self, state):
        if(state == DUTStates.charging):
            logging.debug("dut" + str(self.dutid) + " in charging")
            time.sleep(3)
        elif(state == DUTStates.discharging):
            logging.debug("dut" + str(self.dutid) + " in discharging")
            time.sleep(3)
        else:
            logging.debug("unknow dut state, exit...")
            self.queue.put(DUTStates.EXIT)

    def exit(self):
        logging.debug("dut" + str(self.dutid) + " exit...")


if __name__ == "__main__":
    import sys

    logger = logging.getLogger()
    formatter = logging.Formatter('[ %(asctime)s ] %(levelname)s %(message)s')

    # add stdout handler
    stdhl = logging.StreamHandler(sys.stdout)
    stdhl.setFormatter(formatter)
    stdhl.setLevel(logging.DEBUG)   # print everything
    logger.addHandler(stdhl)
    logger.setLevel(logging.DEBUG)

    duts = []
    for i in range(128):
        dut = DUT(i)
        fsm = base.StateMachine(dut)
        fsm.run()
        duts.append(dut)
    for dut in duts:
        dut.en_queue(DUTStates.INIT)
        dut.en_queue(DUTStates.charging)
        dut.en_queue(DUTStates.discharging)
        dut.en_queue(DUTStates.EXIT)
