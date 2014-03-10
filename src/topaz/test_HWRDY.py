#!/usr/bin/env python
# encoding: utf-8

"""test i2c hardware ready signal
"""

from topaz.i2c_adapter import DeviceAPI


def read_hwrd():
    global_da.slave_addr = 0x38

    # config PIO to input
    wdata = [0x00, 0x00]
    global_da.write(wdata)

    # read 1 byte
    val = global_da.read()
    print val


if __name__ == "__main__":
    global_da = DeviceAPI(bitrate=400)
    global_da.open(portnum=0)
    read_hwrd()
