#!/usr/bin/env python
# encoding: utf-8
"""open 1 channel, return Channel object,
and control the burin in process on this channel
"""
from topaz import fsm
from topaz.pyaardvark import Adapter
from topaz.i2c_basic import set_relay, switch, hwrd, re_position
from topaz.i2c_basic import dut_info, dut_reg
from topaz.db import DB
from topaz.config import CHARGE, DISCHARGE, SLOTNUM
from topaz.config import DUTStatus, LIMITS, DEVICE_LIST, DELAY
import logging
import time
import sys
import traceback


def process_check(device, db, ch_id):
    """pre check"""
    set_relay(device, ch_id, 0xFF, status=CHARGE)
    time.sleep(DELAY.POWERON)       # wait for device to be ready
    matrix = hwrd(device, ch_id)
    set_relay(device, ch_id, matrix, status=CHARGE)
    for i in range(SLOTNUM):
        dut_id = re_position(ch_id, i)
        dut = db.fetch(dut_id)
        if(matrix & (0x01 << i)):
            # dut present
            switch(device, ch_id, i)
            dut.update(dut_info(device, ch_id, i))
            if(dut["PWRCYCS"] >= LIMITS.POWER_CYCLE):
                dut["STATUS"] = DUTStatus.PASSED
                dut["MESSAGE"] = "DUT PASSED."
                logging.warning(str(dut["_id"]) + " " + dut["SN"] + " passed.")
            logging.info("[+] " + "Found " + dut["MODEL"] + " " +
                         dut["SN"] + " " + str(dut["PWRCYCS"]) + " on "
                         + str(re_position(ch_id, i)))
        else:
            logging.debug(str(dut_id) + " is not ready.")
            dut["status"] = DUTStatus.BLANK
        db.update(dut)
    set_relay(device, ch_id, matrix, status=DISCHARGE)
    return matrix


def process_charge(device, db, ch_id, matrix):
    set_relay(device, ch_id, matrix, status=CHARGE)
    start_s = time.time()
    finish = False
    while(not finish):
        finish = True
        for i in range(SLOTNUM):
            if(not matrix & (0x01 << i)):
                continue
            switch(device, ch_id, i)

            dut_id = re_position(ch_id, i)
            dut = db.fetch(dut_id)
            result = dut_reg(device, ch_id, i)
            result.update({"TIME": time.time()-start_s})
            finish &= (result["VCAP"] >= LIMITS.VCAP_THRESH_HIGH)
            vcap = result["VCAP"]
            temp = result["TEMP"]
            if(vcap > LIMITS.VCAP_LIMITS_HIGH):
                # over charge voltage, fail
                logging.error("[-]" + " over charge voltage: " + str(vcap))
                dut["STATUS"] = DUTStatus.FAILED
                dut["MESSAGE"] = "DUT VCAP HIGH."
            if(temp > LIMITS.TEMP_LIMITS_HIGH):
                # over temperature, fail
                logging.error("[-]" + " over temperature: " + str(temp))
                dut["STATUS"] = DUTStatus.FAILED
                dut["MESSAGE"] = "DUT TEMP HIGH."

            # record result
            curr_cycle = "CYCLES" + str(int(dut["PWRCYCS"]) + 1)
            if curr_cycle not in dut:
                dut.update({curr_cycle: []})
            dut[curr_cycle].append(result)
            display = "[+] " + str(re_position(ch_id, i)) + \
                      " VCAP: " + str(vcap) + " TEMP: " + str(temp)

            logging.info(display)
            db.update(dut)
        logging.info("=" * len(display))    # seperator for diaplay
        time.sleep(DELAY.READCYCLE)


def process_discharge(device, db, ch_id, matrix):
    set_relay(device, ch_id, matrix, status=DISCHARGE)
    start_s = time.time()
    finish = False
    while(not finish):
        finish = True
        for i in range(SLOTNUM):
            if(not matrix & (0x01 << i)):
                continue

            switch(device, ch_id, i)

            dut_id = re_position(ch_id, i)
            dut = db.fetch(dut_id)
            result = dut_reg(device, ch_id, i)
            result.update({"TIME": time.time()-start_s})
            finish &= (result["VCAP"] <= LIMITS.VCAP_THRESH_LOW)
            vcap = result["VCAP"]
            temp = result["TEMP"]
            if(vcap > LIMITS.VCAP_LIMITS_HIGH):
                # over charge voltage, fail
                logging.error("[-]" + " over charge voltage: " + str(vcap))
                dut["STATUS"] = DUTStatus.FAILED
                dut["MESSAGE"] = "DUT VCAP HIGH."
            if(temp > LIMITS.TEMP_LIMITS_HIGH):
                # over temperature, fail
                logging.error("[-]" + " over temperature: " + str(temp))
                dut["STATUS"] = DUTStatus.FAILED
                dut["MESSAGE"] = "DUT TEMP HIGH."

            # record result
            curr_cycle = "CYCLES" + str(int(dut["PWRCYCS"]) + 1)
            if curr_cycle not in dut:
                dut.update({curr_cycle: []})
            dut[curr_cycle].append(result)

            display = "[+] " + str(re_position(ch_id, i)) + \
                      " VCAP: " + str(vcap) + " TEMP: " + str(temp)

            logging.info(display)
            db.update(dut)
        logging.info("=" * len(display))    # seperator for diaplay
        time.sleep(DELAY.READCYCLE)


def process_postcheck(db, ch_id):
    for i in range(SLOTNUM):
        dut_id = re_position(ch_id, i)
        dut = db.fetch(dut_id)
        if(dut["STATUS"] == DUTStatus.IDLE):
            return False
    return True


def channle_open(ch_id, device_id):
    device = Adapter()
    device.open(serialnumber=device_id)
    return Channel(ch_id, device)


class ChannelStates(fsm.States):
    run = 0xFF
    charging = 0xA0
    discharging = 0xA1
    precheck = 0xA2
    postcheck = 0xA3


class Channel(fsm.IFunc):
    def __init__(self, ch_id, device):
        self.ch_id = ch_id
        self.device = device
        index = re_position(ch_id, 0)
        self.db = DB(range(index, index + SLOTNUM))
        self.matrix = 0x00
        super(Channel, self).__init__()

    def init(self):
        logging.debug("channel " + str(self.ch_id) + " in init")

    def idle(self):
        logging.debug("channel " + str(self.ch_id) + " in idle")

    def work(self, state):
        if(state == ChannelStates.charging):
            # CHARGING
            logging.debug("channel " + str(self.ch_id) + " in charging")
            try:
                process_charge(self.device, self.db,
                               self.ch_id, self.matrix)
            except Exception as e:
                #logging.error(e)
                exc_type, exc_value, exc_tb = sys.exc_info()
                logging.error(repr(traceback.format_exception(exc_type,
                                                              exc_value,
                                                              exc_tb)))
                self.queue.put(ChannelStates.ERROR)
            self.queue.put(ChannelStates.discharging)
        elif(state == ChannelStates.discharging):
            # DISCHARGING
            logging.debug("channel " + str(self.ch_id) + " in discharging")
            try:
                process_discharge(self.device, self.db,
                                  self.ch_id, self.matrix)
            except Exception as e:
                #logging.error(e)
                exc_type, exc_value, exc_tb = sys.exc_info()
                logging.error(repr(traceback.format_exception(exc_type,
                                                              exc_value,
                                                              exc_tb)))
                self.queue.put(ChannelStates.ERROR)
            self.queue.put(ChannelStates.postcheck)
        elif(state == ChannelStates.postcheck):
            # Post Check
            logging.debug("channel " + str(self.ch_id) + " in post-check")
            try:
                finish = process_postcheck(self.db, self.ch_id)
                if(finish):
                    self.queue.put(ChannelStates.EXIT)
            except Exception as e:
                #logging.error(e)
                exc_type, exc_value, exc_tb = sys.exc_info()
                logging.error(repr(traceback.format_exception(exc_type,
                                                              exc_value,
                                                              exc_tb)))
                self.queue.put(ChannelStates.ERROR)
            else:
                self.queue.put(ChannelStates.IDLE)
        elif(state == ChannelStates.precheck):
            # Pre Check
            logging.debug("channel " + str(self.ch_id) + " in pre-check")
            try:
                self.matrix = process_check(self.device, self.db, self.ch_id)
            except Exception as e:
                #logging.error(e)
                exc_type, exc_value, exc_tb = sys.exc_info()
                logging.error(repr(traceback.format_exception(exc_type,
                                                              exc_value,
                                                              exc_tb)))
                self.queue.put(ChannelStates.ERROR)
            else:
                self.queue.put(ChannelStates.charging)
        elif(state == ChannelStates.run):
            # Start Running
            self.queue.put(ChannelStates.precheck)
        else:
            logging.debug("unknow dut state, exit...")
            self.queue.put(ChannelStates.EXIT)

    def error(self):
        logging.debug("channel " + str(self.ch_id) + " in error")
        try:
            set_relay(self.device, self.ch_id, 0x00,  status=DISCHARGE)
        except:
            pass
        self.queue.put(ChannelStates.EXIT)

    def exit(self):
        self.device.close()
        self.db.close()
        logging.debug("channel " + str(self.ch_id) + " in exit...")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="channel.py")
    parser.add_argument('channel', action='store', help='channel to burnin')
    args = parser.parse_args()
    print args.channel

    my_channel = channle_open(ch_id=int(args.channel)-1, device_id=DEVICE_LIST[0])
    f = fsm.StateMachine(my_channel)
    f.run()

    finish = False
    while(not finish):
        # start one cycle
        f.en_queue(ChannelStates.run)
        time.sleep(1)   # wait for the process to run, refresh the status.
        # wait for this cycle to finish
        while((f.status.value != ChannelStates.IDLE) and
              (f.status.value != ChannelStates.EXIT)):
            # check if the channle has finished burnin
            time.sleep(5)
        if(f.status.value == ChannelStates.EXIT):
            finish = True
        else:
            # wait the PGEM PowerCycle number change, stupid.
            time.sleep(360)
