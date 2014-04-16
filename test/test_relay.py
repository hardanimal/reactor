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


def position(dutnum):
    chnum, slot = dutnum / 8, dutnum % 8
    return chnum, slot


def set_relay(device, chnum, matrix, status=0):
    """set relay for dut
    """
    REG_OUTPUT = 0x02
    REG_CONFIG = 0x06
    dutnum = chnum * 8
    chnum, slot = position(dutnum)
    device.slave_addr = 0x20 + chnum     # 0100000

    # config PIO to output
    wdata = [REG_CONFIG, 0x00, 0x00]
    device.write(wdata)

    # set charge relay
    wdata = [REG_OUTPUT, 0x00, 0x00]    # open all relay
    device.write(wdata)

    if(status == 0):
        # discharge
        high, low = bitop_discharge(matrix)
        wdata = [REG_OUTPUT, low, high]    # all discharge
        device.write(wdata)
    else:
        # charge
        high, low = bitop_charge(matrix)
        wdata = [REG_OUTPUT, low, high]    # all charge
        device.write(wdata)


def bitop_discharge(data):
    # discharge
    high = (data & 0xF0) >> 4
    low = data & 0x0F
    RELAY03 = 0x0
    #RELAY47 = 0xAA
    RELAY47 = 0x0
    for i in range(4):
        b = high & 0x01
        b = b << (i*2 + 1)

        a = low & 0x01
        a = a << (i*2 + 1)

        RELAY47 += b
        RELAY03 += a
        high = high >> 1
        low = low >> 1

    return RELAY47, RELAY03


def bitop_charge(data):
    # charge
    high = (data & 0xF0) >> 4
    low = data & 0x0F
    RELAY03 = 0x0
    #RELAY47 = 0xAA
    RELAY47 = 0x0
    for i in range(4):
        b = high & 0x01
        b = b << (i*2)

        a = low & 0x01
        a = a << (i*2)

        RELAY47 += b
        RELAY03 += a
        high = high >> 1
        low = low >> 1

    return RELAY47, RELAY03


if __name__ == "__main__":
    from topaz.pyaardvark import Adapter
    # init
    global_da = Adapter(bitrate=400)
    global_da.open(serialnumber=2237839440)

    set_relay(global_da, 0, 0x00, status=1)

    # close
    global_da.close()
