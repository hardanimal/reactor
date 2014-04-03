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
import logging
import time

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

CHARGE = 1
DISCHARGE = 0


class DUTStatus(object):
    IDLE = 1        # dut is waiting for burn in
    BLANK = 2       # dut is not inserted in the slot
    TESTING = 3     # dut is in burn in
    FAILED = 4      # dut has failed in burn in
    PASSED = 5      # dut has passed in burn in


class LIMITS(object):
    VCAP_LIMITS_HIGH = 130
    TEMP_LIMITS_HIGH = 40
    VCAP_THRESH_HIGH = 115
    VCAP_THRESH_LOW = 50            # need confirm
    MAX_DISCHANGE_TIME = 20         # seconds
    MAX_CHARGE_TIME = 100           # seconds
    POWER_CYCLE = 50                # for testing


def process_check(device, ch_id):
    set_relay(device, ch_id, status=CHARGE)
    time.sleep(5)       # wait for device to be ready
    for i in range(8):
        dut_id = re_position(ch_id, i)
        dut = {"_id": dut_id}    # TODO fetch from db by dut_id
        if(not hwrd(device, ch_id, i)):
            logging.debug(str(dut_id) + " is not ready.")
            dut["status"] = DUTStatus.BLANK
        else:
            switch(device, ch_id, i)
            dut.update(dut_info(device, ch_id, i))
            if(dut["PWRCYCS"] >= LIMITS.POWER_CYCLE):
                dut["STATUS"] = DUTStatus.PASSED
                dut["MESSAGE"] = "DUT PASSED."
                logging.warning(str(dut["_id"]) + " " + dut["SN"] + " passed.")
            logging.info("[+] " + "Found " + dut["MODEL"] + " " +
                        dut["SN"] + " on " + str(re_position(ch_id, i)))
            #logging.info(dut)
    set_relay(device, ch_id, status=DISCHARGE)


def process_charge(device, ch_id):
    set_relay(device, ch_id, status=CHARGE)
    start_s = time.time()
    finish = False
    while(not finish):
        finish = True
        for i in range(8):
            switch(device, ch_id, i)

            dut_id = re_position(ch_id, i)
            dut = {"_id": dut_id, "PWRCYCS": 1}  # TODO fetch from db by dut_id
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
        logging.info("=" * len(display))    # seperator for diaplay
        time.sleep(3)


def process_discharge(device, ch_id):
    set_relay(device, ch_id, status=DISCHARGE)
    start_s = time.time()
    finish = False
    while(not finish):
        finish = True
        for i in range(8):
            switch(device, ch_id, i)

            dut_id = re_position(ch_id, i)
            dut = {"_id": dut_id, "PWRCYCS": 1}  # TODO fetch from db by dut_id
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
        logging.info("=" * len(display))    # seperator for diaplay
        time.sleep(3)


def process_postcheck(ch_id):
    # check if duts on ch_id are all idle.
    return False


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
        self.db = DB(range(re_position(ch_id, 0), 8))
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
                process_charge(self.device, self.ch_id)
            except Exception as e:
                logging.error(e)
                self.queue.put(ChannelStates.ERROR)
            self.queue.put(ChannelStates.discharging)
        elif(state == ChannelStates.discharging):
            # DISCHARGING
            logging.debug("channel " + str(self.ch_id) + " in discharging")
            try:
                process_discharge(self.device, self.ch_id)
            except Exception as e:
                logging.error(e)
                self.queue.put(ChannelStates.ERROR)
            self.queue.put(ChannelStates.postcheck)
        elif(state == ChannelStates.postcheck):
            # Post Check
            logging.debug("channel " + str(self.ch_id) + " in post-check")
            try:
                finish = process_postcheck(self.ch_id)
                if(finish):
                    self.queue.put(ChannelStates.EXIT)
            except Exception as e:
                logging.error(e)
                self.queue.put(ChannelStates.ERROR)
            else:
                self.queue.put(ChannelStates.IDLE)
        elif(state == ChannelStates.precheck):
            # Pre Check
            logging.debug("channel " + str(self.ch_id) + " in pre-check")
            try:
                process_check(self.device, self.ch_id)
            except Exception as e:
                logging.error(e)
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
            set_relay(self.device, self.ch_id, status=DISCHARGE)
        except:
            pass
        self.queue.put(ChannelStates.EXIT)

    def exit(self):
        self.device.close()
        logging.debug("channel " + str(self.ch_id) + " in exit...")


if __name__ == "__main__":
    my_channel = channle_open(ch_id=0, device_id=DEVICE_LIST[0])
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
