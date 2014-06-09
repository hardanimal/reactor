#!/usr/bin/env python
# encoding: utf-8
'''chamber class, control the upper and lower chamber.
one chamber contains 8 channels.
'''
from topaz.pyaardvark import Adapter
from topaz.channel import channel_open, ChannelStates
from topaz import fsm
import logging
import sys
import traceback
import time


class ChamberStates(fsm.States):
    pass


class Chamber(fsm.IFunc):
    '''chamber class
    '''

    def __init__(self, adapter_sn, powersupply, ps_node, ps_set, chamber_id):
        self.i2c_adapter = Adapter()
        self.i2c_sn = adapter_sn
        self.ps = powersupply
        self.ps_node = ps_node
        self.chamber_id = chamber_id
        self.setting = ps_set
        self.channel_list = []
        for i in range(chamber_id*8, chamber_id*8+8):
            my_channel = channel_open(ch_id=i, device=self.i2c_adapter)
            f = fsm.StateMachine(my_channel)
            f.run()
            self.channel_list.append(f)
        self.finish = False
        super(Chamber, self).__init__()

    def init(self):
        logging.debug("chamber " + str(self.chamber_id) + " in init")
        try:
            self.i2c_adapter.open(serialnumber=self.i2c_sn)
            self.ps.selectChannel(node=self.ps_node, ch=1)
            self.ps.set(self.setting)
            self.ps.activateOutput()
            time.sleep(2)
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            logging.error(repr(traceback.format_exception(exc_type,
                                                          exc_value,
                                                          exc_tb)))
            self.empty()
            self.queue.put(ChamberStates.ERROR)

    def idle(self):
        logging.debug("chamber " + str(self.chamber_id) + " in idle")

    def work(self, state):
        logging.debug("chamber " + str(self.chamber_id) + " start")
        wait_for_discharge = 0      # time to delay for empty channel
        while(not self.finish):
            self.finish = True
            for f in self.channel_list:
                if(f.status.value == ChannelStates.EXIT):
                    # check if already finished.
                    self.finish &= True
                    logging.info("-----channel finish.-----")
                    wait_for_discharge += 30
                    continue
                else:
                    self.finish &= False
                    logging.info("-----channel not finish.-----")
                logging.info("-----channel start-----")
                # start one cycle
                f.en_queue(ChannelStates.run)
                time.sleep(1)

                # wait for this cycle to finish
                while((f.status.value != ChannelStates.IDLE) and
                      (f.status.value != ChannelStates.EXIT)):
                    # check if the channle has finished burnin
                    time.sleep(5)
                logging.info("-----channel done.-----")
            if(not self.finish):
                # used to prevent only one channel left and
                # get not enough time to dischage
                time.sleep(wait_for_discharge)
            wait_for_discharge = 0
        logging.debug("chamber " + str(self.chamber_id) + " finish")

    def error(self):
        logging.debug("chamber " + str(self.chamber_id) + " in error")
        try:
            self.ps.selectChannel(node=self.ps_node, ch=1)
            self.ps.deactivateOutput()
            self.i2c_adapter.close()
        except Exception:
            pass
        self.queue.put(ChannelStates.EXIT)

    def exit(self):
        self.ps.deactivateOutput()
        logging.debug("chamber " + str(self.chamber_id) + " in exit...")


if __name__ == "__main__":
    from pwr import PowerSupply
    ps = PowerSupply()
    setting = {"volt": 12.0, "curr": 15.0, "ovp": 13.0, "ocp": 20.0}

    chamber = Chamber(2237839440, ps, ps_node=5, ps_set=setting,  Chamber_id=0)
    f = fsm.StateMachine(chamber)
    f.run()

    f.en_queue(ChamberStates.INIT)
    f.en_queue(ChamberStates.WORK)
