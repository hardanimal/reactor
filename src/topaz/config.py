#!/usr/bin/env python
# encoding: utf-8

DBOPTION = dict(connectstring='mongodb://localhost:27017/',
                db_name="topaz_bi",
                collection_running="dut_running",
                collection_archive="dut_archive")

DUTLIST = range(1, 2)       # define the list to be tested

CHARGE = 0
DISCHARGE = 1


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


class I2CADDR(object):
    DUT = 0x14


class DUTException(Exception):
    """define the DUT error
    """
    def __init__(self, **kvargs):
        self.code = kvargs.get("code", 0)
        self.message = kvargs.get("message", "undefined error")

    def __str__(self):
        return repr(self.message)


class DUTERROR(object):
    HR_TIMEOUT = DUTException(code=0x01, message="read HW_READY timeout")
    DI_TIMEOUT = DUTException(code=0x02, message="read DUT eeprom timeout")
    CH_TIMEOUT = DUTException(code=0x03, message="charge timeout")
    DC_TIMEOUT = DUTException(code=0x04, message="discharge timeout")
    VCAP_HIGH  = DUTException(code=0x05, message="VCAP over voltage")
    TEMP_HIGH  = DUTException(code=0x06, message="over temperature")
