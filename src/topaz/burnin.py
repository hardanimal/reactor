#!/usr/bin/env python
# encoding: utf-8
import atexit
import time
import os
import sys
import logging
from ColorizingStreamHandler import ColorizingStreamHandler

LOG_FILE = 'error.log'


def init_log():
    if os.path.isfile(LOG_FILE):
        os.remove(LOG_FILE)     # remove the log file

    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    # add stdout handler
    #stdhl = logging.StreamHandler(sys.stdout)
    stdhl = ColorizingStreamHandler(sys.stdout)
    stdhl.setFormatter(formatter)
    stdhl.setLevel(logging.DEBUG)   # print everything

    # add file handler
    hdlr = logging.FileHandler(LOG_FILE)
    hdlr.setFormatter(formatter)
    hdlr.setLevel(logging.WARNING)   # save WARNING, EEROR and CRITICAL to file

    logger.addHandler(hdlr)
    logger.addHandler(stdhl)
    logger.setLevel(logging.DEBUG)
    return logger

logger = init_log()

try:
    from i2c_adapter.i2c_adapter import DeviceAPI
except ImportError, e:
    logger.critical("[-] Module i2c_adapter is not found.")
    logger.warning("[!] program terminated...")
    exit(0)
try:
    from pymongo import MongoClient
    mongo_client = MongoClient('mongodb://localhost:27017/')
    db = mongo_client["topaz_bi"]
except ImportError, e:
    logger.critical("[-] MongoDB is not found. Need install it first.")
    logger.warning("[!] program terminated...")
    exit(0)

dutinfo_collection = db["dut_info"]         # collection for DUTs archived
dutburnin_collection = db["dut_burnin"]     # collection for detail burnin info
dutrunning_collection = db["dut_running"]   # collection for 128 running DUTs
dutrunning_collection.remove()              # delete the real time status

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


class LIMITS(object):
    VCAP_HIGH = 115
    VCAP_LOW = 50
    MAX_DISCHANGE_TIME = 60  # seconds
    MAX_CHARGE_TIME = 120
    POWER_CYCLE = 100


class DUTStatus(object):
    IDLE = 1        # dut is waiting for burn in
    BLANK = 2       # dut is not inserted in the slot
    TESTING = 3     # dut is in burn in
    FAILED = 4      # dut has failed in burn in
    PASSED = 5      # dut has passed in burn in


def query_map(mymap, **kvargs):
    """method to search the map (the list of dict, [{}, {}])
    params: mymap:  the map to search
            kvargs: query conditon key=value, key should be in the dict.
    return: the dict match the query contdtion or None.
    """
    for row in mymap:
        for k, v in kvargs.items():
            if(row[k] != v):
                break
            else:
                return row
    return None


EEPROM_REG_ADDRL = 0
EEPROM_REG_ADDRH = 1
EEPROM_REG_RWDATA = 2


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
    eep = query_map(EEP_MAP, name=eep_name)      # eep is one dict in eep_map
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
    reg = query_map(REG_MAP, name=reg_name)     # reg is one dict in reg_map
    addr = reg["addr"]
    return device.read_reg(addr)


def dut_info(dut_num):
    da = DeviceAPI(bitrate=100)
    da.open(portnum=0)
    da.slave_addr = 20
    dut = {"DUT_NUM": dut_num}
    for eep in EEP_MAP:
        try:
            eep_name = eep["name"]
            dut.update({eep_name: readvpd_byname(da, eep_name)})
        except RuntimeError, e:
            if(e.args[1] == 3):    # I2C read error, dut is not present
                dut.update({"DUT_STATUS": DUTStatus.BLANK})
                dutrunning_collection.insert(dut)
                logger.error("[-] " + "DUT not found on " + str(dut_num))
            else:
                logger.error("[-] " + str(e))
            return
    logger.info("[*] " + "Found " + dut["MODEL"] + " " +
                dut["SN"] + " on " + str(dut_num))
    # query the archived DUT info database
    query = {"SN": dut["SN"], "MODEL": dut["MODEL"]}
    if(dutinfo_collection.find_one(query)):
        # DUT already in DUT info
        logger.warning("[!] " + dut["SN"] + " already exists in dut_info database")
        return
    else:
        dut.update({"DUT_STATUS": DUTStatus.IDLE})
        dutrunning_collection.insert(dut)
    da.close()


def cycling(dut_num):
    da = DeviceAPI(bitrate=100)
    da.open(portnum=0)
    da.slave_addr = 20

    # get serial number and model from dut_running
    dut = dutrunning_collection.find_one({"DUT_NUM": dut_num})
    if(not dut):
        # dut info is not found at dut running collection
        logger.error("[-] DUT_NUM " + str(dut_num) + " is not present.")
        return

    # read current status, if IDLE, then TESTING
    if(dut["DUT_STATUS"] != DUTStatus.IDLE):
        logger.error("[-] DUT_NUM " + str(dut_num) + " is not IDLE.")
        return

    burninfo = {"DUT_NUM": dut_num}
    burninfo.update({"SN": dut["SN"], "MODEL": dut["MODEL"]})
    curr_cycle = int(dut["PWRCYCS"]) + 1

    #TODO power on dut, read HW_READY
    logger.info("[+] " + str(dut_num) + " is charging now")     # debug
    vcap = readreg_byname(da, "VCAP")
    start_s = time.time()
    vcaps, temps, times = [], [], []
    while(vcap < LIMITS.VCAP_HIGH):    # charging
        vcap = readreg_byname(da, "VCAP")
        temp = readreg_byname(da, "TEMP")
        curr_s = time.time() - start_s
        vcaps.append(vcap)
        temps.append(temp)
        times.append(curr_s)
        if(curr_s > LIMITS.MAX_CHARGE_TIME):
            # over charge time, fail
            dutrunning_collection.update({"DUT_NUM": dut_num}, {"$set": {"DUT_STATUS": DUTStatus.FAILED}})
            logger.error("[-] over charge time")
            return
        logger.info("[+] " + str(dut_num) + " VCAP: " + str(vcap) + " TEMP: " + str(temp) + " TIME: " + str(curr_s))
        time.sleep(2)
    thecycle = {"NUM": curr_cycle, "VCAP": vcaps, "TEMP": temps, "TIMES": times}
    burninfo.update({"CYCLES": thecycle})
    dutburnin_collection.save(burninfo)
    logger.info("[+] " + str(dut_num) + " is charged")     # debug

    #TODO power off dut, close discharge relay
    #print "[+] " + str(dut_num) + " Discharging now"     # debug
    #time.sleep(5)               # debug
    #vcap = readreg_byname(da, "VCAP")
    #start_s = time.time()
    #while(vcap > LIMITS.VCAP_LOW):    # discharging
    #    print "[+] " + str(dut_num) + " VCAP: " + str(vcap)    # debug
    #    burninfo = {"DUT_NUM": dut_num}
    #    burninfo.update({"SN": dut["SN"], "MODEL": dut["MODEL"]})
    #    burninfo.update({"STATUS": "discharging"})
    #    for reg in REG_MAP:
    #        burninfo.update({reg["name"]: readreg_byname(da, reg["name"])})
    #    vcap = burninfo["VCAP"]
    #    curr_s = time.time() - start_s
    #    burninfo.update({"TIME": curr_s})
    #    dutburnin_collection.insert(burninfo)
    #    if(curr_s > LIMITS.MAX_DISCHANGE_TIME):
    #        # over charge time, fail
    #        dutrunning_collection.update({"DUT_NUM": dut_num}, {"$set": {"DUT_STATUS": DUTStatus.FAILED}})
    #        print "[-] over discharge time"
    #        return
    #    time.sleep(2)

    dutrunning_collection.update({"DUT_NUM": dut_num}, {"$set": {"DUT_STATUS": DUTStatus.IDLE}})
    da.close()


def shutdown():
    """function when exit, exception
    """
    #dutrunning_collection.remove()  # delete the real time status
    mongo_client.close()
    logger.warning("[!] program shutdown...")


if __name__ == "__main__":
    atexit.register(shutdown)
    dut_info(1)
    cycling(1)
