#!/usr/bin/env python
# encoding: utf-8

from i2c_adapter.i2c_adapter import DeviceAPI

EEPROM_REG_ADDRL = 0
EEPROM_REG_ADDRH = 1
EEPROM_REG_RWDATA = 2


def read_ee(device, addr):
    device.write_reg(EEPROM_REG_ADDRL, addr & 0xFF)
    device.write_reg(EEPROM_REG_ADDRH, (addr >> 8) & 0xFF)
    val = device.read_reg(EEPROM_REG_RWDATA)
    return val


def get_PWRCYCS(device):
    data1 = read_ee(device, 0x268)
    data2 = read_ee(device, 0x269)
    val = data1 + (data2 << 8)
    return val


if __name__ == "__main__":
    da = DeviceAPI(bitrate=100)
    da.open(portnum=0)
    da.slave_addr = 20
    while 1:
        print "PGEM: " + str(da.read_reg(0x05))
        print "TEMP: " + str(da.read_reg(0x06))
        print "VCAP: " + str(da.read_reg(0x08))
        print "Power Cycle: " + str(get_PWRCYCS(da))
        da.sleep(1000)
