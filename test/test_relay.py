#!/usr/bin/env python
# encoding: utf-8

"""test the 128 DUTs switch.

TCA9555 to control the relay:
    Address: 0x20 + channel number
    Command Byte:
        input = 0x00
        output = 0x02
        config = 0x06

    Relay matrix: (B for dischage, A for charge)
        bit: 4B 4A 3B 3A 2B 2A 1B 1A
        sta:  1  1  1  1  1  1  1  1
        bit: 8B 8A 7B 7A 6B 6A 5B 5A
        sta:  1  1  1  1  1  1  1  1

"""

from topaz.i2c_adapter import Adapter, I2CConfig

REG_INPUT = 0x00
REG_OUTPUT = 0x02
REG_CONFIG = 0x06


def set_relay(chnum, slotnum, status=0):
    """set relay for dut
    """
    global_da.slave_addr = 0x20 + chnum     # 0100000

    # config PIO to output
    wdata = [REG_CONFIG, 0x00, 0x00]
    global_da.write(wdata)

    # set charge relay
    wdata = [REG_OUTPUT, 0x00, 0x00]    # open all relay
    global_da.write(wdata)

    if(status==0):
        # open relay
        pass


    if(slotnum > 3):
        pass


    pass


def charge_relay(chnum, slotnum, open=True):
    global_da.slave_addr = 0x20  # 0100000

    # config PIO to output
    wdata = [REG_CONFIG, 0x00, 0x00]
    global_da.write(wdata)

    # set charge relay
    wdata = [REG_OUTPUT, 0x00, 0x00]    # open all relay
    global_da.write(wdata)

    #wdata = [REG_OUTPUT, 0x01, 0x40]
    #wdata = [REG_OUTPUT, 0x55, 0x55]   # all charge
    wdata = [REG_OUTPUT, 0xaa, 0xaa]    # all dischage
    global_da.write(wdata)


def discharge_relay(dutnum, open=True):
    global_da.slave_addr = 0x20  # 0100000

    # config PIO to output
    wdata = [REG_CONFIG, 0x00, 0x00]
    global_da.write(wdata)

    # set charge relay
    wdata = [REG_OUTPUT, 0x02, 0x80]
    global_da.write(wdata)


if __name__ == "__main__":
    # init
    global_da = Adapter(bitrate=400)
    global_da.open(serialnumber=2237839440)

    import time
    charge_relay(0, 1)
    #time.sleep(30)
    #discharge_relay(1)

    # close
    global_da.close()
