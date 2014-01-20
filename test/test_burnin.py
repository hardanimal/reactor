#!/usr/bin/env python
# encoding: utf-8

from topaz import burnin
from topaz.timeout import timethis
import unittest
import time
device = burnin.global_da
device.slave_addr = burnin.I2CADDR.DUT


class BurninTestCases(unittest.TestCase):
    def test_querymap(self):
        query = burnin.query_map(burnin.REG_MAP, name="VCAP")
        result = [{"name": "VCAP", "addr": 0x08}]
        self.assertEqual(query, result)

        query = burnin.query_map(burnin.REG_MAP, name="TEST")
        self.assertEqual(query, [])

    def test_readvpd(self):
        device.open()
        result = burnin.readvpd_byname(device, "MODEL")
        self.assertEqual(result, "501DCB00")
        device.close()

    def test_readreg(self):
        device.open()
        result = burnin.readreg_byname(device, "VCAP")
        self.assertGreaterEqual(result, 10)
        device.close()


class TimeThisTestCases(unittest.TestCase):
    def test_timeout(self):

        @timethis
        def delaysec(n):
            time.sleep(n)

        timeout = delaysec(2, timeout=1)
        result = {'result': None, 'timeout': True, 'eplased': None}
        self.assertEqual(timeout, result)


if __name__ == "__main__":
    unittest.main()
