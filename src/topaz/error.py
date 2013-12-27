#!/usr/bin/env python
# encoding: utf-8


class DUTException(Exception):
    """define the DUT error
    """
    def __init__(self, **kvargs):
        self.code = kvargs.get("code", 0)
        self.message = kvargs.get("message", "undefined error")

    def __str__(self):
        return repr(self.message)


class DUTERROR(object):
    DUT_PASSED = DUTException(code=0x00, message="PASSED")
    HR_TIMEOUT = DUTException(code=0x01, message="read HW_READY timeout")
    DI_TIMEOUT = DUTException(code=0x02, message="read DUT eeprom timeout")
    CH_TIMEOUT = DUTException(code=0x03, message="charge timeout")
    DC_TIMEOUT = DUTException(code=0x04, message="discharge timeout")
    VCAP_HIGH  = DUTException(code=0x05, message="VCAP over voltage")
    TEMP_HIGH  = DUTException(code=0x06, message="over temperature")
