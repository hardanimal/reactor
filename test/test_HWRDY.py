#!/usr/bin/env python
# encoding: utf-8

"""test i2c hardware ready signal

TCA9554A to read the HW_READY signal.
    Address: 0x38 + channel number
    Command Byte:
        input = 0x00
"""

from topaz.pyaardvark import Adapter


def read_hwrd():
    global_da.slave_addr = 0x38

    # config PIO to input
    wdata = [0x00, 0x00]
    global_da.write(wdata)

    # read 1 byte
    val = global_da.read()
    val = (~ (val & 0xFF)) & 0xFF
    return val


if __name__ == "__main__":
    global_da = Adapter(bitrate=400)
    global_da.open(portnum=0)
    print read_hwrd()
