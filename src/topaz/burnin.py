#!/usr/bin/env python
# encoding: utf-8
import time
from topaz.pyaardvark import Adapter
from topaz.channel import channel_open, ChannelStates
from topaz import fsm
from topaz.config import DEVICE_LIST
import logging

i2c_adapter = Adapter()
i2c_adapter.open(serialnumber=DEVICE_LIST[0])


def main():
    channel_list = []
    for channel_id in range(0, 8):
        my_channel = channel_open(ch_id=channel_id, device=i2c_adapter)
        f = fsm.StateMachine(my_channel)
        f.run()
        channel_list.append(f)

    burnin_finish = False
    logging.info("====================burnin start=========================")
    while(not burnin_finish):
        burnin_finish = True
        for f in channel_list:
            if(f.status.value == ChannelStates.EXIT):
                # check if already finished.
                burnin_finish &= True
                continue
            else:
                burnin_finish &= False
            logging.info("--------------channel start----------------------")
            # start one cycle
            f.en_queue(ChannelStates.run)
            time.sleep(1)

            # wait for this cycle to finish
            while((f.status.value != ChannelStates.IDLE) and
                  (f.status.value != ChannelStates.EXIT)):
                # check if the channle has finished burnin
                time.sleep(5)
            logging.info("--------------channel done.----------------------")
    logging.info("====================burnin done.=========================")


if __name__ == "__main__":
    main()
