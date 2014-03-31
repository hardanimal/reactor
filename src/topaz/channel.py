#!/usr/bin/env python
# encoding: utf-8
"""open 1 channel, return Channel object,
and control the burin in process on this channel
"""
from topaz import fsm
from topaz.pyaardvark import Adapter
from topaz.i2c_basic import set_relay, switch, hwrd
from topaz.i2c_basic import dut_info, dut_reg
import logging

DEVICE_LIST = [2237839440,
               2237839440,
               2237839440,
               2237839440,
               2237839440,
               2237839440,
               2237839440,
               2237839440,
               2237849511,
               2237849511,
               2237849511,
               2237849511,
               2237849511,
               2237849511,
               2237849511,
               2237849511]


def open(ch_id, device_id):
    device = Adapter()
    device.open(serialnumber=device_id)
    return Channel(ch_id, device)


class ChannelStates(fsm.States):
    charging = 0xA0
    discharging = 0xA1


class Channel(fsm.IFunc):
    def __init__(self, ch_id, device):
        self.ch_id = ch_id
        self.device = device
        super(Channel, self).__init__()

    def init(self):
        logging.debug("channel" + str(self.ch_id) + " in init")

    def idle(self):
        logging.debug("channel" + str(self.ch_id) + " in idle")

    def work(self, state):
        if(state == ChannelStates.charging):
            logging.debug("channel" + str(self.ch_id) + " in charging")
            set_relay(self.device, self.ch_id, status=1)
        elif(state == ChannelStates.discharging):
            logging.debug("channel" + str(self.ch_id) + " in discharging")
        else:
            logging.debug("unknow dut state, exit...")
            self.queue.put(ChannelStates.EXIT)

    def exit(self):
        self.device.close()
        logging.debug("channel" + str(self.ch_id) + " in exit...")


if __name__ == "__main__":
    pass
