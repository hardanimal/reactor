#!/usr/bin/env python
# encoding: utf-8

"""i2c_adapter.py: API for aardvark i2c adapter.
the device can be found at http://www.totalphase.com/products/aardvark_i2cspi/
And rewrite the I2C part of original API aardvark_py.py
"""

__version__ = "1.0.0"
__author__ = "@boqiling"
__all__ = ["I2CConfig", "Adapter"]

import os
import inspect
from array import array
import imp
import platform

ext = platform.system() == 'Windows' and '.dll' or '.so'
dll_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
api = imp.load_dynamic('aardvark', dll_path + '/aardvark' + ext)

DEFAULT_REG_VAL = 0xFF

I2C_STATUS_MAP = [{"msg": "AA_I2C_STATUS_OK", "code": 0},
                  {"msg": "AA_I2C_STATUS_BUS_ERROR", "code": 1},
                  {"msg": "AA_I2C_STATUS_SLA_ACK", "code": 2},
                  {"msg": "AA_I2C_STATUS_SLA_NACK", "code": 3},
                  {"msg": "AA_I2C_STATUS_DATA_NACK", "code": 4},
                  {"msg": "AA_I2C_STATUS_ARB_LOST", "code": 5},
                  {"msg": "AA_I2C_STATUS_BUS_LOCKED", "code": 6},
                  {"msg": "AA_I2C_STATUS_LAST_DATA_ACK", "code": 7}]

AA_STATUS_MAP = [{"msg": "AA_OK", "code": 0},
                 {"msg": "AA_UNABLE_TO_LOAD_LIBRARY", "code": -1},
                 {"msg": "AA_UNABLE_TO_LOAD_DRIVER", "code": -2},
                 {"msg": "AA_UNABLE_TO_LOAD_FUNCTION", "code": -3},
                 {"msg": "AA_INCOMPATIBLE_LIBRARY", "code": -4},
                 {"msg": "AA_INCOMPATIBLE_DEVICE", "code": -5},
                 {"msg": "AA_COMMUNICATION_ERROR", "code": -6},
                 {"msg": "AA_UNABLE_TO_OPEN", "code": -7},
                 {"msg": "AA_UNABLE_TO_CLOSE", "code": -8},
                 {"msg": "AA_INVALID_HANDLE", "code": -9},
                 {"msg": "AA_CONFIG_ERROR", "code": -10},
                 {"msg": "AA_I2C_NOT_AVAILABLE", "code": -100},
                 {"msg": "AA_I2C_NOT_ENABLED", "code": -101},
                 {"msg": "AA_I2C_READ_ERROR", "code": -102},
                 {"msg": "AA_I2C_WRITE_ERROR", "code": -103},
                 {"msg": "AA_I2C_SLAVE_BAD_CONFIG", "code": -104},
                 {"msg": "AA_I2C_SLAVE_READ_ERROR", "code": -105},
                 {"msg": "AA_I2C_SLAVE_TIMEOUT", "code": -106},
                 {"msg": "AA_I2C_DROPPED_EXCESS_BYTES", "code": -107},
                 {"msg": "AA_I2C_BUS_ALREADY_FREE", "code": -108},
                 {"msg": "AA_SPI_NOT_AVAILABLE", "code": -200},
                 {"msg": "AA_SPI_NOT_ENABLED", "code": -201},
                 {"msg": "AA_SPI_WRITE_ERROR", "code": -202},
                 {"msg": "AA_SPI_SLAVE_READ_ERROR", "code": -203},
                 {"msg": "AA_SPI_SLAVE_TIMEOUT", "code": -204},
                 {"msg": "AA_SPI_DROPPED_EXCESS_BYTES", "code": -205},
                 {"msg": "AA_GPIO_NOT_AVAILABLE", "code": -400},
                 {"msg": "AA_I2C_MONITOR_NOT_AVAILABLE", "code": -500},
                 {"msg": "AA_I2C_MONITOR_NOT_ENABLED", "code": -501},
                 {"msg": "AA_NO_DEVICE_FOUND", "code": -600},
                 {"msg": "AA_UNABLE_TO_OPEN_PORT", "code": -601},
                 {"msg": "AA_PORT_DOES_NOT_EXSISTS", "code": -602}]


def _query_map(mymap, **kvargs):
    """method to search the map (the list of dict, [{}, {}])
    params: mymap:  the map to search
            kvargs: query conditon key=value, key should be in the dict.
    return: the dict match the query contdtion or None.
    """
    r = mymap
    for k, v in kvargs.items():
        r = filter(lambda row: row[k] == v,  r)
    return r


def raise_i2c_ex(num):
    ex = _query_map(I2C_STATUS_MAP, code=num)[0]
    if(ex["code"] != 0):
        raise RuntimeError(True, ex["code"], ex["msg"])


def raise_aa_ex(num):
    ex = _query_map(AA_STATUS_MAP, code=num)[0]
    if(ex["code"] != 0):
        raise RuntimeError(True, ex["code"], ex["msg"])


class I2CConfig(object):
    AA_CONFIG_GPIO_ONLY = 0x00
    AA_CONFIG_SPI_GPIO = 0x01
    AA_CONFIG_GPIO_I2C = 0x02
    AA_CONFIG_SPI_I2C = 0x03
    AA_CONFIG_QUERY = 0x80

    AA_CONFIG_SPI_MASK = 0x00000001
    AA_CONFIG_I2C_MASK = 0x00000002
    AA_I2C_PULLUP_NONE = 0x00
    AA_I2C_PULLUP_BOTH = 0x03
    AA_I2C_PULLUP_QUERY = 0x80

    AA_TARGET_POWER_NONE = 0x00
    AA_TARGET_POWER_BOTH = 0x03
    AA_TARGET_POWER_QUERY = 0x80

    AA_I2C_NO_FLAGS = 0x00
    AA_I2C_10_BIT_ADDR = 0x01
    AA_I2C_COMBINED_FMT = 0x02
    AA_I2C_NO_STOP = 0x04
    AA_I2C_SIZED_READ = 0x10
    AA_I2C_SIZED_READ_EXTRA1 = 0x20


def array_u08 (n):  return array('B', '\0'*n)
def array_u16 (n):  return array('H', '\0\0'*n)
def array_u32 (n):  return array('I', '\0\0\0\0'*n)
def array_u64 (n):  return array('K', '\0\0\0\0\0\0\0\0'*n)
def array_s08 (n):  return array('b', '\0'*n)
def array_s16 (n):  return array('h', '\0\0'*n)
def array_s32 (n):  return array('i', '\0\0\0\0'*n)
def array_s64 (n):  return array('L', '\0\0\0\0\0\0\0\0'*n)


class Adapter(object):
    '''USB-I2C Adapter API Class
    '''

    def __init__(self, **kvargs):
        '''constructor
        '''
        self.bitrate = kvargs.get('bitrate', 0)
        self.bus_timeout = kvargs.get('timeout', 25)
        self.handle = 0
        self.slave_addr = 0

    def __del__(self):
        '''destructor
        '''
        try:
            self.close()
        except Exception:
            pass

    def open(self, portnum=0):
        '''
        find ports, and open the port with portnum,
        config the aardvark tool params like bitrate, slave address etc,
        '''
        # first, need find how many devices, set devices=0
        total_port_num = api.py_aa_find_devices(0, array_u16(0))
        # then, need find how many devices, set devices=total_port_num
        # it's freaky here.
        devices = array_u16(total_port_num)
        total_port_num = api.py_aa_find_devices(total_port_num, devices)
        if total_port_num <= 0:
            raise_aa_ex(-600)
        elif portnum >= total_port_num:
            raise_aa_ex(-602)
        else:
            self.port = portnum

        # open port
        self.handle = api.py_aa_open(self.port)
        if(self.handle <= 0):
            raise_aa_ex(self.handle)
        # Ensure that the I2C subsystem is enabled
        api.py_aa_configure(self.handle,  I2CConfig.AA_CONFIG_SPI_I2C)
        api.py_aa_i2c_pullup(self.handle, I2CConfig.AA_I2C_PULLUP_BOTH)
        api.py_aa_target_power(self.handle, I2CConfig.AA_TARGET_POWER_NONE)
        # Set the bitrate, in khz
        self.bitrate = api.py_aa_i2c_bitrate(self.handle, self.bitrate)
        # Set the bus lock timeout, in ms
        api.py_aa_i2c_bus_timeout(self.handle, self.bus_timeout)
        # Free bus
        api.py_aa_i2c_free_bus(self.handle)

    def unique_id(self):
        """Return the unique identifier of the device. The identifier is the
        serial number you can find on the adapter without the dash. Eg. the
        serial number 0012-345678 would be 12345678.
        """
        return api.py_aa_unique_id(self.handle)

    def unique_id_str(self):
        """Return the unique identifier. But unlike :func:`unique_id`, the ID
        is returned as a string which has the format NNNN-MMMMMMM.
        """
        unique_id = self.unique_id()
        id1 = unique_id / 1000000
        id2 = unique_id % 1000000
        return '%04d-%06d' % (id1, id2)

    def write(self, wdata, config=I2CConfig.AA_I2C_NO_FLAGS):
        '''write data to slave address
        data can be byte or array of byte
        '''
        if(type(wdata) == int):
            data_out = array('B', [wdata])
            length = 1
        elif(type(wdata) == list):
            data_out = array('B', wdata)
            length = len(wdata)
        else:
            raise TypeError("i2c data to be written is not valid")
        (ret, num_written) = api.py_aa_i2c_write_ext(self.handle,
                                                     self.slave_addr,
                                                     config,
                                                     length,
                                                     data_out)
        if(ret != 0):
            api.py_aa_i2c_free_bus(self.handle)
            raise_i2c_ex(ret)
        if(num_written != length):
            raise_aa_ex(-103)

    def read(self, config=I2CConfig.AA_I2C_NO_FLAGS):
        '''read 1 byte from slave address
        '''
        # read 1 byte each time for easy
        length = 1
        data_in = array_u08(length)
        (ret, num_read) = api.py_aa_i2c_read_ext(self.handle,
                                                 self.slave_addr,
                                                 config,
                                                 length,
                                                 data_in)
        if(ret != 0):
            api.py_aa_i2c_free_bus(self.handle)
            raise_i2c_ex(ret)
        if(num_read != length):
            raise_aa_ex(-102)
        val = data_in[0]
        return val

    def write_reg(self, reg_addr, wdata):
        '''
        Write data list to slave device
        If write to slave device's register, data_list = [reg_addr, wdata]
        reg_addr: register address offset
        wdata: data to be write to SMBus register
        '''
        # data_out must be unsigned char
        data_out = [reg_addr, wdata]
        self.write(data_out)

    def read_reg(self, reg_addr):
        '''
        Read data from slave device's register
        write the [reg_addr] to slave device first, then read back.
        reg_addr: register address offset
        '''
        val = DEFAULT_REG_VAL
        self.write(reg_addr, I2CConfig.AA_I2C_NO_STOP)

        # read register data
        val = self.read()
        return val

    def sleep(self, ms):
        '''sleep for specified number of milliseconds
        '''
        api.py_aa_sleep_ms(ms)

    def close(self):
        '''close device
        '''
        api.py_aa_close(self.handle)


if __name__ == "__main__":
    da = Adapter(bitrate=400)
    da.open(portnum=0)
    da.slave_addr = 20
    print "Port: " + str(da.port)
    print "Handle: " + str(da.handle)
    print "Slave: " + str(da.slave_addr)
    print "Bitrate: " + str(da.bitrate)
    print da.read_reg(0x05)
    print da.read_reg(0x06)
    print da.read_reg(0x08)
    da.close()
