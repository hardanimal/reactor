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
i2c_adapter2 = Adapter()
i2c_adapter2.open(serialnumber=DEVICE_LIST[1])


def main():
    channel_list = []
    for channel_id in range(0, 8):
        my_channel = channel_open(ch_id=channel_id, device=i2c_adapter)
        f = fsm.StateMachine(my_channel)
        f.run()
        channel_list.append(f)

    for channel_id in range(8, 16):
        my_channel = channel_open(ch_id=channel_id, device=i2c_adapter2)
        f = fsm.StateMachine(my_channel)
        f.run()
        channel_list.append(f)

    wait_for_discharge = 0

    burnin_finish = False
    logging.info("====================burnin start=========================")
    while(not burnin_finish):
        burnin_finish = True
        for f in channel_list:
            if(f.status.value == ChannelStates.EXIT):
                # check if already finished.
                burnin_finish &= True
                logging.info("----------channel finish.------------------")
                wait_for_discharge += 30
                continue
            else:
                burnin_finish &= False
                logging.info("----------channel not finish.------------------")
            logging.info("----------channel start------------------")
            # start one cycle
            f.en_queue(ChannelStates.run)
            time.sleep(1)

            # wait for this cycle to finish
            while((f.status.value != ChannelStates.IDLE) and
                  (f.status.value != ChannelStates.EXIT)):
                # check if the channle has finished burnin
                time.sleep(5)
            logging.info("--------------channel done.----------------------")
        if(not burnin_finish):
            # used to prevent only one channel left and
            # get not enough time to dischage
            time.sleep(wait_for_discharge)
    logging.info("====================burnin done.=========================")


if __name__ == "__main__":
    main()
