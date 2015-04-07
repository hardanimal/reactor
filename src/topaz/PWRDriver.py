#!/usr/bin/env python
# encoding: utf-8

'''
Module Name:    PWRDriver.py
Author(s):      PZHO
Description:    This module implements communications with power supply via
                USB interface.
Dependencies:   win32com or comtypes
'''

import comtypes
import comtypes.client
import array
import math
import thread
from time import sleep
# import UpgradePPCOM
import os


class PowerSupplyDevice(object):
    voltage = 5
    current = 10


    def __init__(self):

        self.m_output = None

        try:
            self._PWR = comtypes.client.CreateObject("Kikusui4800.Kikusui4800")

            # See if there was an error connecting to the bridge
            if self._PWR is None:
                print "Failed to create a reference to the COM object."

        except Exception as ex:
            print "exception"

    def open(self, port="USB0::0x0B3E::0x1014::NB003730::0::INSTR", option=""):
        Status = self._PWR.Initialize(port, True, False, option)

        if Status != 0:
            raise Exception('OpenPort Exception', 'port can not be opened')
            print "fail to open port"

        print self._PWR.Identity.InstrumentModel + " Ver" + self._PWR.Identity.InstrumentFirmwareRevision
        errorCode = 0
        StrErrMessage = ""
        self._PWR.Utility.ErrorQuery(errorCode, StrErrMessage)
        #print errorCode
        while errorCode != 0:
            self._PWR.Utility.ErrorQuery(errorCode, StrErrMessage)

        return

    def close(self):
        self._PWR.close()
        return

    def reset(self):
        if not self._PWR.Initialized:
            return

        try:
            self._PWR.Reset()
            errorCode = 0
            StrErrMessage = ""
            self._PWR.Utility.ErrorQuery(errorCode, StrErrMessage)
            #print errorCode
            while errorCode != 0:
                self._PWR.Utility.ErrorQuery(errorCode, StrErrMessage)
        except Exception as ex:
            raise Exception("Reset exception")

        return

    def openChannel(self, channelName="N5!C1"):
        self.m_output = self._PWR.Outputs.Item["N5!C1"]
        print self.m_output

        return

    def setVoltage(self, volt):
        #set output voltage
        if not self._PWR.Initialized:
            return
        try:
            self.m_output.VoltageLevel = volt

        except Exception as ex:
            raise Exception("Set voltage exception")
        return

    def setCurrentLimit(self, currentLimit):
        #set current output
        if not self._PWR.Initialized:
            return
        try:
            self.m_output.CurrentLimit = currentLimit

        except Exception as ex:
            raise Exception("Set Current limit exception")

        return

    def activeOutput(self):
        #enable voltage output
        if not self._PWR.Initialized:
            return
        try:
            self.m_output.Enabled = True

        except Exception as ex:
            raise Exception("enable output exception")

        return

    def De_activeOutput(self):
        #disable voltage output
        if not self._PWR.Initialized:
            return
        try:
            self.m_output.Enabled = False

        except Exception as ex:
            raise Exception("diable output exception")
        return

    def setOVP(self, volt):
        #set OVP limit
        if not self._PWR.Initialized:
            return
        try:
            self.m_output.OVPLimit = volt

        except Exception as ex:
            raise Exception("Set OVP limit exception")
        return

    def setOCP(self, current):
        #set OCP limit
        if not self._PWR.Initialized:
            return
        try:
            self.m_output.OCPLimit = current

        except Exception as ex:
            raise Exception("Set OCP limit exception")
        return

    def measureVolt(self):
        #measure output voltage
        if not self._PWR.Initialized:
            return
        try:
            measuredVolt = self.m_output.Measure(1)
        except Exception as ex:
            raise Exception("Measure voltage exception")

        return measuredVolt

    def measureCurrent(self):
        #measure output current
        if not self._PWR.Initialized:
            return
        try:
            measuredCurrent = self.m_output.Measure(0)
        except Exception as ex:
            raise Exception("Measure current exception")

        return measuredCurrent

    def QueryState(self):
        #Query the state of output
        if not self._PWR.Initialized:
            return
        try:
            if self.m_output.QueryState(0):
                return "CV"
            if self.m_output.QueryState(1):
                return "CC"
            if self.m_output.QueryState(2):
                return "OVP"
            if self.m_output.QueryState(3):
                return "OCP"
            if self.m_output.QueryState(4):
                return "UNR"
            if self.m_output.QueryState(1001):
                return "CP"

        except Exception as ex:
            raise Exception("Measure current exception")


def main():
    PS = PowerSupplyDevice()
    PS.open()
    PS.openChannel()
    PS.setVoltage(12)
    PS.activeOutput()
    sleep(5)
    print PS.measureVolt()
    print PS.QueryState()
    #print PS.measureCurrent()


if __name__ == '__main__':
    main()
