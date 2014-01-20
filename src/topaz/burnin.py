#!/usr/bin/env python
# encoding: utf-8
import atexit
import time

# GLOBAL_CONSTANT
LOG_FILE = 'error.log'
DBOPTION = dict(connectstring='mongodb://localhost:27017/',
                db_name="topaz_bi",
                collection_running="dut_running",
                collection_archive="dut_archive")
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
DUTLIST = range(1, 2)       # define the list to be tested

CHARGE = 0
DISCHARGE = 1

# IMPORT SELF-DEFINED MODULES AND GLOBAL_VIRIABLE
try:
    from topaz import log_io
    logger = log_io.init_log(LOG_FILE)
except ImportError, e:
    print("[-] Module log_io is not found.")
    exit(0)
try:
    from i2c_adapter.i2c_adapter import DeviceAPI
    global_da = DeviceAPI(bitrate=400)
except ImportError, e:
    logger.critical("[-] Module i2c_adapter is not found.")
    logger.warning("[!] program terminated...")
    exit(0)
try:
    from topaz import data_io
    global_db = data_io.DB(DBOPTION, DUTLIST)
    DUTSTATUS = data_io.DUTStatus
except ImportError, e:
    logger.critical("[-] MongoDB is not found. Need install it first.")
    logger.warning("[!] program terminated...")
    exit(0)
try:
    from topaz.timeout import timethis
    from topaz.error import DUTERROR, DUTException
except ImportError, e:
    logger.critical("[-] self defined  modules are not found.")
    logger.warning("[!] program terminated...")
    exit(0)


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


def query_map(mymap, **kvargs):
    """method to search the map (the list of dict, [{}, {}])
    params: mymap:  the map to search
            kvargs: query conditon key=value, key should be in the dict.
    return: the dict match the query contdtion or None.
    """
    for k, v in kvargs.items():
        r = filter(lambda row: row[k] == v,  mymap)
    return r


def read_ee(device, addr):
    """method to read eeprom data,
    first write low address byte to register EEPROM_REG_ADDRL,
    then write high address byte to register EEPROM_REG_ADDRH,
    then read the data from register EEPROM_REG_RWDATA.
    params: device: I2C adapter device handle
            addr:   eeprom address to read
    return: value of addr in byte
    """
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
    reg = query_map(REG_MAP, name=reg_name)[0]     # reg is one dict in reg_map
    addr = reg["addr"]
    return device.read_reg(addr)


@timethis
def dut_info(dut):
    global_da.slave_addr = I2CADDR.DUT

    for eep in EEP_MAP:
        eep_name = eep["name"]
        dut.update({eep_name: readvpd_byname(global_da, eep_name)})

    logger.info("[+] " + "Found " + dut["MODEL"] + " " +
                dut["SN"] + " on " + str(dut["_id"]))

    # read cycles, see if passed already
    if(dut["PWRCYCS"]) > LIMITS.POWER_CYCLE:
        raise DUTERROR.DUT_PASSED


@timethis
def dut_charge(cycle_data, start_s):
    global_da.slave_addr = I2CADDR.DUT

    tmp = {}
    vcap = readreg_byname(global_da, "VCAP")
    while(vcap < LIMITS.VCAP_THRESH_HIGH):    # charging
        for reg in REG_MAP:
            data = readreg_byname(global_da, reg["name"])
            cycle_data[reg["name"]].append(data)
            tmp.update({reg["name"]: data})
        curr_s = time.time() - start_s
        cycle_data["TIME"].append(curr_s)
        vcap = tmp["VCAP"]
        temp = tmp["TEMP"]
        if(vcap > LIMITS.VCAP_LIMITS_HIGH):
            # over charge voltage, fail
            logger.error("[-]" + " over charge voltage: " + str(vcap))
            raise DUTERROR.VCAP_HIGH
        if(temp > LIMITS.TEMP_LIMITS_HIGH):
            # over temperature, fail
            logger.error("[-]" + " over temperature: " + str(temp))
            raise DUTERROR.TEMP_HIGH
        logger.info("[+] " + " VCAP: " + str(vcap) + " TIME: " + str(curr_s))
        time.sleep(2)


@timethis
def dut_discharge(cycle_data, start_s):
    global_da.slave_addr = I2CADDR.DUT

    tmp = {}
    vcap = readreg_byname(global_da, "VCAP")
    while(vcap > LIMITS.VCAP_THRESH_LOW):    # charging
        for reg in REG_MAP:
            data = readreg_byname(global_da, reg["name"])
            cycle_data[reg["name"]].append(data)
            tmp.update({reg["name"]: data})
        curr_s = time.time() - start_s
        cycle_data["TIME"].append(curr_s)
        vcap = tmp["VCAP"]
        temp = tmp["TEMP"]
        if(vcap > LIMITS.VCAP_LIMITS_HIGH):
            # over charge voltage, fail
            logger.error("[-]" + " over charge voltage: " + str(vcap))
            raise DUTERROR.VCAP_HIGH
        if(temp > LIMITS.TEMP_LIMITS_HIGH):
            # over temperature, fail
            logger.error("[-]" + " over temperature: " + str(temp))
            raise DUTERROR.TEMP_HIGH
        logger.info("[+] " + " VCAP: " + str(vcap) + " TIME: " + str(curr_s))
        time.sleep(2)


def switch_slot(dutnum):
    """1~64   are in slot 1
       65~128 are in slot 2
    """
    global_da.close()
    if(dutnum <= 64):
        global_da.open(portnum=0)  # slot 1
    else:
        global_da.open(portnum=1)  # slot 2


def switch_brd(dutnum):
    """dutnmum from 1 to 128.
    current num = dutnum - 64
    first switch from 1 to 8 channel
    then, switch from 1 to 8 on 1 load board
    """
    pass


def charge_relay(dutnum, open=True):
    pass


def discharge_relay(dutnum, open=True):
    pass


@timethis
def HWReady(dutnum):
    status = True
    while(status is not True):
        status = True
    return status


def power_12V_on():
    pass


def power_12V_off():
    pass


def shutdown():
    """function when exit, exception."""
    global_da.close()
    global_db.close()
    logger.warning("[!] program shutdown...")


def loop(dutnum):
    dut = global_db.fetch(dutnum)
    switch_slot(dutnum)
    switch_brd(dutnum)

    # close charge relay
    charge_relay(dutnum, open=False)
    start_s = time.time()

    # read hwready signal
    r = HWReady(dutnum, timeout=5)
    if(r["timeout"]): raise DUTERROR.HR_TIMEOUT
    logger.debug(str(r))

    # set testing
    dut["STATUS"] = DUTSTATUS.TESTING
    global_db.update(dut)

    # read dut info
    r = dut_info(dut, timeout=2)
    if(r["timeout"]): raise DUTERROR.DI_TIMEOUT
    logger.debug(str(r))

    # charge
    curr_cycle = int(dut["PWRCYCS"]) + 1
    logger.info("[+] DUT " + str(dutnum) +
                " CYCLES: " + str(curr_cycle) + " is charging now")
    c = {"NUM": curr_cycle, "TIME": []}     # temp dict for this cycle's list
    for reg in REG_MAP:
        c.update({reg["name"]: []})
    r = dut_charge(c, start_s, timeout=LIMITS.MAX_CHARGE_TIME)
    if(r["timeout"]):
        if "CYCLES" in dut:
            dut["CYCLES"].append(c)
        else:
            dut.update({"CYCLES": []})
            dut["CYCLES"].append(c)
        global_db.update(dut)
        raise DUTERROR.CH_TIMEOUT
    logger.debug(str(r))
    logger.info("[+] " + str(dutnum) + " is charged")     # debug

    # discharge
    charge_relay(dutnum, open=True)
    discharge_relay(dutnum, open=False)

    logger.info("[+] DUT " + str(dutnum) +
                " CYCLES: " + str(curr_cycle) + " is discharging now")
    r = dut_discharge(c, start_s, timeout=LIMITS.MAX_DISCHANGE_TIME)
    if(r["timeout"]):
        if "CYCLES" in dut:
            dut["CYCLES"].append(c)
        else:
            dut.update({"CYCLES": []})
            dut["CYCLES"].append(c)
        global_db.update(dut)
        raise DUTERROR.DC_TIMEOUT
    logger.info("[+] " + str(dutnum) + " is discharged")     # debug

    if "CYCLES" in dut:
        dut["CYCLES"].append(c)
    else:
        dut.update({"CYCLES": []})
        dut["CYCLES"].append(c)

    # set IDLE
    dut["STATUS"] = DUTSTATUS.IDLE
    global_db.update(dut)


def main():
    try:
        atexit.register(shutdown)
        global_db.init()
        power_12V_on()
        while not global_db.check_all_idle():
            for i in DUTLIST:
                try:
                    loop(i)
                except DUTException, e:
                    if(e.code == DUTERROR.DUT_PASSED):
                        # make it pass
                        logger.info("DUT " + str(i) + " " + str(e))
                        global_db.update_status(i, DUTSTATUS.PASSED, e.message)
                    elif(e.code == DUTERROR.HR_TIMEOUT):
                        # HW is not Ready, maybe blank board, skip it.
                        logger.info("DUT " + str(i) + " " + str(e))
                        global_db.update_status(i, DUTSTATUS.BLANK, e.message)
                    else:
                        # make it fail
                        logger.error("DUT " + str(i) + " " + str(e))
                        global_db.update_status(i, DUTSTATUS.FAILED, e.message)
                    continue
        power_12V_off()
    except Exception, e:
        logger.error(str(e))


if __name__ == "__main__":
    main()
