#!/usr/bin/env python
# encoding: utf-8
""" I2C basic functions for topaz VPD and registers
"""

REG_MAP = [{"name": "READINESS", "addr": 0x04},
           {"name": "PGEMSTAT",  "addr": 0x05},
           {"name": "TEMP",      "addr": 0x06},
           {"name": "VIN",       "addr": 0x07},
           {"name": "VCAP",      "addr": 0x08},
           {"name": "VC1",       "addr": 0x09},
           {"name": "VC2",       "addr": 0x0A},
           {"name": "VC3",       "addr": 0x0B},
           {"name": "VC4",       "addr": 0x0C},
           {"name": "VC5",       "addr": 0x0D},
           {"name": "VC6",       "addr": 0x0E},
           {"name": "RESERVED",  "addr": 0x0F}]

EEP_MAP = [{"name": "PWRCYCS", "addr": 0x0268, "length": 2, "type": "word"},
           {"name": "LASTCAP", "addr": 0x026A, "length": 1, "type": "int"},
           {"name": "MODEL",   "addr": 0x026B, "length": 8, "type": "str"},
           {"name": "FWVER",   "addr": 0x0273, "length": 8, "type": "str"},
           {"name": "HWVER",   "addr": 0x027B, "length": 8, "type": "str"},
           {"name": "CAPPN",   "addr": 0x0283, "length": 8, "type": "str"},
           {"name": "SN",      "addr": 0x028B, "length": 8, "type": "str"},
           {"name": "PCBVER",  "addr": 0x0293, "length": 8, "type": "str"},
           {"name": "MFDATE",  "addr": 0x029B, "length": 8, "type": "str"},
           {"name": "ENDUSR",  "addr": 0x02A3, "length": 8, "type": "str"},
           {"name": "PCA",     "addr": 0x02AB, "length": 8, "type": "str"},
           {"name": "CINT",    "addr": 0x02B3, "length": 1, "type": "int"}]

EEPROM_REG_ADDRL = 0        # EEPROM register of ADDRESS LOW
EEPROM_REG_ADDRH = 1        # EEPROM register of ADDRESS HIGH
EEPROM_REG_RWDATA = 2       # EEPROM register of Data to read and write


def query_map(mymap, **kvargs):
    """method to search the map (the list of dict, [{}, {}])
    params: mymap:  the map to search
            kvargs: query conditon key=value, key should be in the dict.
    return: the dict match the query contdtion or None.
    """
    r = mymap
    for k, v in kvargs.items():
        r = filter(lambda row: row[k] == v,  r)
    return r


def position(dutnum):
    chnum, slot = dutnum / 8, dutnum % 8
    return chnum, slot


def re_position(chnum, slot):
    dutnum = chnum * 8 + slot
    return dutnum


def read_ee(device, addr):
    """method to read eeprom data,
    first write low address byte to register EEPROM_REG_ADDRL,
    then write high address byte to register EEPROM_REG_ADDRH,
    then read the data from register EEPROM_REG_RWDATA.
    params: device: I2C adapter device handle
            addr:   eeprom address to read
    return: value of addr in byte
    """
    device.slave_addr = 0x14
    device.write_reg(EEPROM_REG_ADDRL, addr & 0xFF)
    device.write_reg(EEPROM_REG_ADDRH, (addr >> 8) & 0xFF)
    val = device.read_reg(EEPROM_REG_RWDATA)
    return val


def readvpd_byname(device, eep_name):
    """method to read eep_data according to eep_name
    eep is one dict in eep_map, for example:
    {"name": "CINT", "addr": 0x02B3, "length": 1, "type": "int"}
    """
    eep = query_map(EEP_MAP, name=eep_name)[0]     # eep is one dict in eep_map
    start = eep["addr"]                 # start_address
    length = eep["length"]              # length
    typ = eep["type"]                   # type
    datas = [read_ee(device, addr) for addr in range(start, (start + length))]
    if(typ == "word"):
        val = datas[0] + (datas[1] << 8)
        return val
    if(typ == "str"):
        return ''.join(chr(i) for i in datas)
    if(typ == "int"):
        return datas[0]


def readreg_byname(device, reg_name):
    """method to read register data according to register name
    reg is one dict in reg_map, for example:
    {"name": "VCAP",      "addr": 0x08},
    """
    device.slave_addr = 0x14
    reg = query_map(REG_MAP, name=reg_name)[0]     # reg is one dict in reg_map
    addr = reg["addr"]
    return device.read_reg(addr)


def dut_info(device, chnum, slot):
    """method to read out EEPROM info from dut
    return a dict.
    """
    dut = {}
    for eep in EEP_MAP:
        eep_name = eep["name"]
        dut.update({eep_name: readvpd_byname(device, eep_name)})
    return dut


def dut_reg(device, chnum, slot):
    """method to read out registers info from dut
    return a dict.
    """
    dut = {}
    for reg in REG_MAP:
        reg_name = reg["name"]
        dut.update({reg_name: readreg_byname(device, reg_name)})

    return dut


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


#def hwrd(device, chnum, slot):
#    device.slave_addr = 0x38 + chnum
#
#    # config PIO to input
#    wdata = [0x00, 0x00]
#    device.write(wdata)
#
#    # read 1 byte
#    val = device.read()
#    # check 1 bit
#    val &= 0x01 << slot
#    if(val == 0):
#        return True
#    else:
#        return False

def hwrd(device, chnum):
    device.slave_addr = 0x38 + chnum

    # config PIO to input
    wdata = [0x00, 0x00]
    device.write(wdata)

    # read 1 byte
    val = device.read()
    val = (~ (val & 0xFF)) & 0xFF
    return val


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


def switch(device, chnum, slot):
    """switch I2C ports by PCA9548A, only 1 channel is enabled.
       chnum(channel number): 0~7
       slotnum(slot number): 0~7
    """
    device.slave_addr = 0x70 + chnum    # 0111 0000
    wdata = [0x01 << slot]
    device.write(wdata)


def deswitch(device, chnum):
    """switch I2C ports by PCA9548A, only 1 channel is enabled.
       chnum(channel number): 0~7
       slotnum(slot number): 0~7
    """
    device.slave_addr = 0x70 + chnum    # 0111 0000
    wdata = 0x00
    device.write(wdata)


if __name__ == "__main__":
    import time
    from topaz.pyaardvark import Adapter

    device = Adapter()
    device.open(portnum=0)
    channel = 0

    # charge all
    set_relay(device, channel, 0xFF, status=1)
    time.sleep(5)
    # read hardware ready signal
    matrix = hwrd(device, channel)
    set_relay(device, channel, matrix, status=1)
    for i in range(8):
        if(matrix & (0x01 << i)):
            try:
                print str(i) + " is ready."
                switch(device, channel, i)
                print dut_info(device, channel, i)
                print dut_reg(device, channel, i)
            except Exception as e:
                print(e)
        else:
            print str(i) + " is not ready"
    deswitch(device, channel)
    time.sleep(10)
    set_relay(device, channel, matrix, status=0)
