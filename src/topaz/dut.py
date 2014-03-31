#!/usr/bin/env python
# encoding: utf-8

"""dut burnin functions
"""
from topaz import fsm
import logging


class DUTStates(fsm.States):
    charging = 0xA0
    discharging = 0xA1


class DUT(fsm.IFunc):
    def __init__(self, dutid):
        self.dutid = dutid
        super(DUT, self).__init__()

    def init(self):
        logging.debug("dut" + str(self.dutid) + " in init")

    def idle(self):
        logging.debug("dut" + str(self.dutid) + " in idle")

    def work(self, state):
        if(state == DUTStates.charging):
            logging.debug("dut" + str(self.dutid) + " in charging")
        elif(state == DUTStates.discharging):
            logging.debug("dut" + str(self.dutid) + " in discharging")
        else:
            logging.debug("unknow dut state, exit...")
            self.queue.put(DUTStates.EXIT)

    def exit(self):
        logging.debug("dut" + str(self.dutid) + " exit...")


if __name__ == "__main__":
    duts = []
    for i in range(128):
        dut = DUT(i)
        f = fsm.StateMachine(dut)
        f.run()
        duts.append(dut)
    for dut in duts:
        dut.en_queue(DUTStates.INIT)
        dut.en_queue(DUTStates.charging)
        dut.en_queue(DUTStates.discharging)
        dut.en_queue(DUTStates.EXIT)
