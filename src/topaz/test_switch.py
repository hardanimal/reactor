#!/usr/bin/env python
# encoding: utf-8

"""test i2c switch between DUT

PCA9548A to control the I2C switch:
    control register (1=enable, 0=disable):
        bit: B7 B6 B5 B4 B3 B2 B1 B0
        en:   0  0  0  0  0  0  0  1
"""

from topaz.i2c_adapter import DeviceAPI


def switch(chnum, slotnum):
    """switch I2C ports by PCA9548A, only 1 channel is enabled.
       chnum(channel number): 0~7
       slotnum(slot number): 0~7
    """
    global_da.slave_addr = 0x70 + chnum    # 0111 0000
    wdata = [0x01 << slotnum]
    global_da.write(wdata)


def test_dut():
    global_da.slave_addr = 0x14
    print global_da.read_reg(0x05)
    print global_da.read_reg(0x06)
    print global_da.read_reg(0x08)


if __name__ == "__main__":
    global_da = DeviceAPI(bitrate=400)
    global_da.open(portnum=0)
    switch(0, 7)
    test_dut()
