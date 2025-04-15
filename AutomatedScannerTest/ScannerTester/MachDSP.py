# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from . import _get_member_wrapper
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import cv2
from galvotestingPC.mso5000 import MSO5000
import time
import winsound
from datetime import datetime
import pyvisa as visa

import pickle


import os  # for directory creation

from io import StringIO

import shutil  # for script copy
from os import listdir
from os.path import isfile, join

import sys

from galvotestingPC.config import Config

_member_wrapper, _class_logger = _get_member_wrapper(__name__)

useArduino = 0
useGoogleSheets = 0
if useGoogleSheets:
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request


def main():

    ScopeConstr = Config.ScopeConstr
    verbosityLevel = Config.verbosityLevel
    passThreshold = Config.passThresholdMachDSP
    customPath = Config.customPath

    degPerV = 0.1  # MachDSP parameter
    maxPositive = 55  # MachDSP parameter - this many degrees motion
    maxInpV = 10  # maximum input voltage positive
    realInpV = 2.5  # voltage amplitude from generator
    degPP = maxPositive / maxInpV * realInpV * 2  # 2x to get PP from amplitude
    VPP = degPP / degPerV
    mVPP = VPP * 1000
    mVPerIdx = mVPP / 512

    mydpi = 150

    # mVPerIdx = 26.5 # How many mV is one index. 13580 mV / 512 idx

    redLineIdxStart = 35
    redLineIdxStop = 512 - 24
    # redLineIdxStart = 204 # ekvivalent 4000 / 10000
    # redLineIdxStop = 410 # ekvivalent 8000 / 10000

    programCycles = 1
    programCycle = 0

    p_cycles_end = 20  # n of averages

    test = MSO5000()

    rm = visa.ResourceManager()
    devs_found = rm.list_resources()

    def printVer(*args, **kwargs):
        if verbosityLevel >= 1:
            print("".join(map(str, args)), **kwargs)

    for dev in devs_found:
        if "USB" in dev:
            # test.inst = rm.open_resource(ScopeConstr)
            test.inst = rm.open_resource(dev)
        if "ASRL" in dev:
            try:
                instrument = rm.open_resource(dev)
            except:
                continue
            time.sleep(2)
            instrument.write("\n")
            time.sleep(0.1)
            while instrument.bytes_in_buffer > 0:
                try:
                    instrument.read()
                except:
                    continue
                time.sleep(0.1)
            sn = instrument.query("*IDN?\n")
            printVer(sn)
            if "TENMA 72-2540 V5.2 SN:10830844" in sn:
                zdroj = instrument
                continue
            if useArduino:
                if "Vrekrer,Arduino SCPI Dimmer,#00,v0.4" in sn:
                    arduino = instrument
                    continue
            instrument.close()

    if useArduino:
        if not arduino:
            sys.exit("Arduino not found")

    printVer("")

    if useGoogleSheets:
        # If modifying these scopes, delete the file token.pickle.
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

        # The ID and range of a sample spreadsheet.
        SPREADSHEET_ID = (
            "1Wd8k84VsuXXE5Y_Yse8Lv_naLBb-ivXsexCkUzF4HCQ"  # The real thing
        )
        # SPREADSHEET_ID = '1GUFbnPSxSErRqPejvWVlzIbiV8MEx5iTm5nOpM8I3ng' # Only for testing
        RowNumberRange = "Results!B1"

        """Shows basic usage of the Sheets API.
        Prints values from a sample spreadsheet.
        """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)

        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        # Read last row number from the sheet
        result = (
            sheet.values()
            .get(spreadsheetId=SPREADSHEET_ID, range=RowNumberRange)
            .execute()
        )
        rowNumber = result.get("values", [])

    f = input("Enter galvo SN: ")

    if useArduino:
        arduino.write("rel 1,1,10000")

    f_orig = f

    start_time = time.time()

    printVer("Setting scope...")

    devs = test.findDevs()
    for device in devs:
        if "USB" in device:
            printVer(device)
    printVer(devs)

    # test.conn(devs[0])

    test.conn(devs[0])
    printVer(test.identify())

    test.write(command=":RUN")  # Must run to set MDEPth...

    test.write(command=":ACQuire:MDEPth 100k")
    printVer("Mem depth: ", test.query(":ACQuire:MDEPth?"))

    test.write(command=":STOP")  # Must run to set MDEPth...

    time.sleep(1)  # Wait for scope to settle (?)

    test.write(command=":TRIGger:mode TIMeout")
    test.write(command=":TRIGger:coupling DC")
    test.write(command=":TRIGger:nreject 1")
    test.write(command=":TRIGger:timeout:source channel1")

    test.write(command=":TRIGger:TIMeout:SLOPe POSitive")

    test.write(command=":WAVeform:SOURce CHANnel3")
    printVer("Check: ", test.query(":WAVeform:SOURce?"))

    test.write(command=":WAVeform:MODE RAW")
    printVer("Check: ", test.query(":WAVeform:MODE?"))

    test.write(command=":WAVeform:FORMat BYTE")
    printVer("Check: ", test.query(":WAVeform:FORMat?"))

    test.write(command=":SOURce1:output:impedance fifty")  # CH1 50 Ohm
    test.write(command=":SOURce1:voltage:amplitude 2.5")  # CH1 2.5 Vpp
    test.write(command=":SOURce2:output:impedance fifty")  # CH2 50 Ohm
    test.write(command=":SOURce2:voltage:amplitude 1")  # CH2 1 Vpp

    test.write(command=":channel1:display 1")  # turn on ch1
    test.write(
        command=":channel2:display 1"
    )  # turn on ch2 (not really needed, but it is not working without it)
    test.write(command=":channel3:display 1")  # turn on ch3
    test.write(command=":channel1:SCALe 2")
    test.write(command=":channel1:offset 0")
    test.write(command=":channel3:SCALe 0.2")
    test.write(command=":channel3:offset 0")

    test.write(command=":channel3:BWLimit 20M ")

    # while True:
    #     fr = 5
    #     # function generator setup
    #     test.write(command=':SOURce1:output:state 1') # turn on generator
    #     test.write(command=':SOURce1:output:state 1') # turn on generator
    #     test.write(command=':SOURce2:output:state 1') # turn on generator
    #     test.setFrequency(freq=25, channel=1)
    #     test.setFunction(func='SQUare', channel=1)
    #     time.sleep(0.5)
    #     test.setFrequency(freq=fr, channel=1)
    #     #test.setFunction(func='sinusoid', channel=1)
    #     #time.sleep(0.5)
    #     test.setFunction(func='RAMP', channel=1)

    #     time.sleep(2)

    #     fr = 10
    #     test.write(command=':SOURce1:output:state 1') # turn on generator
    #     test.write(command=':SOURce1:output:state 1') # turn on generator
    #     test.write(command=':SOURce2:output:state 1') # turn on generator
    #     test.setFrequency(freq=25, channel=1)
    #     test.setFunction(func='SQUare', channel=1)
    #     time.sleep(0.5)
    #     test.setFrequency(freq=fr, channel=1)
    #     #time.sleep(0.5)
    #     test.setFunction(func='RAMP', channel=1)

    #     time.sleep(2)

    while True:
        programCycle = programCycle + 1

        mypath = os.path.join(customPath, "AllData/", f_orig)

        resultDir = os.path.join(customPath, "AllResults/", "")

        if not os.path.exists(resultDir):
            os.makedirs(resultDir)

        fileIndexStr = ""
        fileIndex = 0

        # create directory. If exists, create directory with number appended.
        if not os.path.exists(mypath):
            os.makedirs(mypath)
            scriptPath = os.path.join(mypath, "script")
            os.makedirs(scriptPath)
        else:
            fileIndex = 1
            while True:
                fileIndex = fileIndex + 1
                if not os.path.exists(mypath + "_" + str(fileIndex)):
                    fileIndexStr = "_" + str(fileIndex)
                    mypath = mypath + "_" + str(fileIndex)
                    os.makedirs(mypath)
                    scriptPath = os.path.join(mypath, "script")
                    os.makedirs(scriptPath)
                    break

        workingDirPath = os.path.dirname(os.path.realpath(__file__))
        # shutil.copy(__file__, scriptPath + os.sep + 'TestGalvoRepeatability.py')
        # shutil.copy(os.path.join(workingDirPath, 'config.py'), scriptPath + os.sep + 'config.py')

        mypath = mypath + "/"  # Working directory

        plt.close("all")

        p_cycles = 0
        while True:
            p_cycles = p_cycles + 1

            f = f_orig + "_" + str(p_cycles)  # Create file name with cycle index

            # m = [];

            if useArduino:
                arduino.write("rel 1,1,13000")

            fr = 50
            # function generator setup
            test.write(command=":SOURce1:output:state 1")  # turn on generator
            test.write(command=":SOURce2:output:state 1")  # turn on generator
            time.sleep(0.5)
            test.setFrequency(freq=25, channel=1)
            time.sleep(0.5)
            test.setFunction(func="SQUare", channel=1)
            time.sleep(0.5)
            test.setFrequency(freq=fr, channel=1)
            # test.setFunction(func='sinusoid', channel=1)
            time.sleep(0.5)
            test.setFunction(func="RAMP", channel=1)
            time.sleep(0.5)
            test.setFrequency(freq=fr, channel=2)
            time.sleep(0.5)
            test.setFunction(func="SQUare", channel=2)
            test.write(command=":TRIGger:TIMeout:TIME " + str(1 / fr / 4))
            test.write(command=":SOURce1:PHASe:INITiate")  # Align phase G1, G2

            test.write(command=":TIMebase:MAIN:SCALe 0.02")
            printVer("Timebase scale: ", test.query(":TIMebase:MAIN:SCALe?"))

            time.sleep(0.5)  # Wait for trigger

            test.write(command=":SINGLe")  # Wait for trigger

            tout = 0

            while not any(s in test.query(":TRIGger:STATus?") for s in ["RUN", "TD"]):
                time.sleep(0.05)
                tout = tout + 1
                if tout >= 30:
                    raise Exception("ERROR: Not triggered.")

            printVer("Measurement has started. Waiting until finish.")

            tout = 0
            while not "STOP" in test.query(":TRIGger:STATus?"):
                time.sleep(0.1)
                tout = tout + 1
                printVer(".", end="")
                if tout >= 200:
                    raise Exception("ERROR: Measurement takes too long.")

            printVer("Measurement finished.")

            time.sleep(1)  # Wait for scope to settle (?)

            printVer("data reading start")

            test.write(command=":WAVeform:STOP 100000")
            printVer("Stop reading data at: ", test.query(":WAVeform:STOP?"))

            data = test.inst.query_binary_values(":WAVeform:DATA?", datatype="B")

            printVer("data reading end")

            y_incr = test.query("YINCrement?")
            y_orig = test.query("YORigin?")
            y_ref = test.query("YREFerence?")

            printVer("y_incr: ", y_incr)
            printVer("y_orig: ", y_orig)
            printVer("y_ref: ", y_ref)

            dt = np.array(data).astype("float")

            dt = dt - float(y_ref) - float(y_orig)
            dt = dt * float(y_incr)

            dtRangeMaxV = (0 - float(y_ref) - float(y_orig)) * float(y_incr)
            dtRangeMinV = (255 - float(y_ref) - float(y_orig)) * float(y_incr)
            dtRangeMaxIdx = dtRangeMaxV * 1000 / mVPerIdx
            dtRangeMinIdx = dtRangeMinV * 1000 / mVPerIdx

            dt = dt.reshape(-1, 1)

            dt = dt.reshape(10, 10000)

            if p_cycles == 1:
                dtall10 = np.expand_dims(dt, axis=0)
            else:
                dtall10 = np.concatenate((dtall10, np.expand_dims(dt, axis=0)), axis=0)

            #
            ###############################################  50 ms ##################################
            #

            # function generator setup

            fr = 10
            # function generator setup
            test.write(command=":SOURce1:output:state 1")  # turn on generator
            test.write(command=":SOURce2:output:state 1")  # turn on generator
            if useArduino:
                arduino.write("rel 1,1,180")

            time.sleep(0.5)
            test.setFrequency(freq=25, channel=1)
            time.sleep(0.5)
            test.setFunction(func="SQUare", channel=1)
            time.sleep(0.5)
            test.setFrequency(freq=fr, channel=1)
            time.sleep(0.5)
            test.setFunction(func="RAMP", channel=1)
            time.sleep(0.5)
            test.setFrequency(freq=fr, channel=2)
            time.sleep(0.5)
            test.setFunction(func="SQUare", channel=2)
            test.write(command=":TRIGger:TIMeout:TIME " + str(1 / fr / 4))
            test.write(command=":SOURce1:PHASe:INITiate")  # Align phase G1, G2

            test.write(command=":TIMebase:MAIN:SCALe 0.1")
            printVer("Timebase scale: ", test.query(":TIMebase:MAIN:SCALe?"))

            test.write(command=":SINGLe")  # Wait for trigger

            time.sleep(0.5)  # Wait for trigger

            trg = test.query(":TRIGger:STATus?")

            printVer("Trigger status: ", trg)

            if trg != "STOP":
                printVer("Measurement has started. Waiting until finish.")
            else:
                raise Exception("ERROR: Not triggered.")

            while test.query(":TRIGger:STATus?") != "STOP":
                time.sleep(0.33)  # Wait until the scope hopefully measures what we need
                printVer(".", end="")

            printVer("Measurement finished.")

            time.sleep(1)  # Wait for scope to settle (?)

            # test.write(command=':WAVeform:SOURce CHANnel3')
            # printVer('Check: ', test.query(':WAVeform:SOURce?'))

            # test.write(command=':WAVeform:MODE RAW')
            # printVer('Check: ', test.query(':WAVeform:MODE?'))

            # test.write(command=':WAVeform:FORMat BYTE')
            # printVer('Check: ', test.query(':WAVeform:FORMat?'))

            # test.write(command=':WAVeform:STOP 10000000')
            # printVer('Stop reading data at: ', test.query(':WAVeform:STOP?'))

            printVer("data reading start")

            data = test.inst.query_binary_values(":WAVeform:DATA?", datatype="B")

            printVer("data reading end")

            y_incr = test.query("YINCrement?")
            y_orig = test.query("YORigin?")
            y_ref = test.query("YREFerence?")

            printVer("y_incr: ", y_incr)
            printVer("y_orig: ", y_orig)
            printVer("y_ref: ", y_ref)

            dt = np.array(data).astype("float")

            dt = dt - float(y_ref) - float(y_orig)
            dt = dt * float(y_incr)

            dt = dt.reshape(-1, 1)

            dt = dt.reshape(10, 10000)

            if p_cycles == 1:
                dtall50 = np.expand_dims(dt, axis=0)
            else:
                dtall50 = np.concatenate((dtall50, np.expand_dims(dt, axis=0)), axis=0)
            print("\r", end="")
            print("Progress: " + str(p_cycles) + "/" + str(p_cycles_end), end="")

            if p_cycles == p_cycles_end:
                break
                # exit program

        if useArduino:
            arduino.write("rel 1,1,150")
        np.save(
            mypath + f_orig + fileIndexStr + "_10ms" + ".npy",
            dtall10,
            allow_pickle=True,
            fix_imports=True,
        )
        np.save(
            mypath + f_orig + fileIndexStr + "_50ms" + ".npy",
            dtall50,
            allow_pickle=True,
            fix_imports=True,
        )
        # dtt = np.load(mypath + f + '.npy')

        ######## RESULT PLOT DOWN BEGIN

        fig, axs = plt.subplots(4, figsize=(1600 / mydpi, 1600 / mydpi), dpi=mydpi)
        fig.suptitle(f_orig + " sweep down")

        mean = np.average(dtall10, axis=1)
        mean = mean * 1000 / mVPerIdx  # convert to indexes
        sweepRange = int(mean.shape[1] / 2)
        redLineStart = int(sweepRange / 512 * redLineIdxStart)
        redLineEnd = int(sweepRange / 512 * redLineIdxStop)
        axs[0].set_title("10 ms")
        axs[0].set_ylim(dtRangeMinIdx, dtRangeMaxIdx)
        axs[0].set_xlim(sweepRange, 2 * sweepRange)
        axs[0].grid(True)
        for i in range(dtall10.shape[0]):
            axs[0].plot(mean[i, :])

        max = np.absolute(mean[0, :] - mean[1, :])
        for i in range(2, dtall10.shape[0]):
            max = np.maximum(max, np.absolute(mean[0, :] - mean[i, :]))

        max = cv2.GaussianBlur(max, (1, 31), 0, borderType=cv2.BORDER_REPLICATE)

        max10down = np.amax(max[sweepRange + redLineStart : sweepRange + redLineEnd])

        axs[1].set_title(str(round(max10down, 3)))
        axs[1].set_ylim(0, 0.2)
        axs[1].set_xlim(sweepRange, 2 * sweepRange)
        axs[1].grid(True)
        axs[1].plot(max)
        axs[1].plot([redLineStart, redLineEnd], [passThreshold, passThreshold], "r")
        axs[1].plot(
            [sweepRange + redLineStart, sweepRange + redLineEnd],
            [passThreshold, passThreshold],
            "r",
        )

        mean = np.average(dtall50, axis=1)
        mean = mean * 1000 / mVPerIdx  # convert to indexes
        sweepRange = int(mean.shape[1] / 2)
        redLineStart = int(sweepRange / 512 * redLineIdxStart)
        redLineEnd = int(sweepRange / 512 * redLineIdxStop)
        axs[2].set_title("50 ms")
        axs[2].set_ylim(-0.5, 0.5)
        axs[2].set_xlim(sweepRange, 2 * sweepRange)
        axs[2].grid(True)
        for i in range(dtall10.shape[0]):
            axs[2].plot(mean[i, :])

        max = np.absolute(mean[0, :] - mean[1, :])
        for i in range(2, dtall10.shape[0]):
            max = np.maximum(max, np.absolute(mean[0, :] - mean[i, :]))

        max = cv2.GaussianBlur(max, (1, 31), 0, borderType=cv2.BORDER_REPLICATE)

        max50down = np.amax(max[sweepRange + redLineStart : sweepRange + redLineEnd])

        axs[3].set_title(str(round(max50down, 3)))
        axs[3].set_ylim(0, 0.2)
        axs[3].set_xlim(sweepRange, 2 * sweepRange)
        axs[3].grid(True)
        axs[3].plot(max)
        axs[3].plot([redLineStart, redLineEnd], [passThreshold, passThreshold], "r")
        axs[3].plot(
            [sweepRange + redLineStart, sweepRange + redLineEnd],
            [passThreshold, passThreshold],
            "r",
        )

        plt.savefig(
            resultDir + f_orig + fileIndexStr + "_down" + ".png",
            bbox_inches="tight",
            dpi=mydpi,
        )

        ######## RESULT PLOT DOWN END

        ######## RESULT PLOT UP BEGIN
        fig, axs = plt.subplots(4, figsize=(1600 / mydpi, 1600 / mydpi), dpi=mydpi)
        fig.suptitle(f_orig + " sweep up")
        mean = np.average(dtall10, axis=1)
        mean = mean * 1000 / mVPerIdx  # convert to indexes
        axs[0].set_title("10 ms")
        axs[0].set_ylim(dtRangeMinIdx, dtRangeMaxIdx)
        axs[0].set_xlim(sweepRange, 0)
        axs[0].grid(True)
        for i in range(dtall10.shape[0]):
            axs[0].plot(mean[i, :])

        sweepRange = mean.shape[1] / 2
        redLineStart = int(sweepRange / 512 * redLineIdxStart)
        redLineEnd = int(sweepRange / 512 * redLineIdxStop)

        max = np.absolute(mean[0, :] - mean[1, :])
        for i in range(2, dtall10.shape[0]):
            max = np.maximum(max, np.absolute(mean[0, :] - mean[i, :]))

        max = cv2.GaussianBlur(max, (1, 31), 0, borderType=cv2.BORDER_REPLICATE)

        max10up = np.amax(max[redLineStart:redLineEnd])

        axs[1].set_title(str(round(max10up, 3)))
        axs[1].set_ylim(0, 0.2)
        axs[1].set_xlim(sweepRange, 0)
        axs[1].grid(True)
        axs[1].plot(max)
        axs[1].plot([redLineStart, redLineEnd], [passThreshold, passThreshold], "r")
        axs[1].plot(
            [sweepRange + redLineStart, sweepRange + redLineEnd],
            [passThreshold, passThreshold],
            "r",
        )

        mean = np.average(dtall50, axis=1)
        mean = mean * 1000 / mVPerIdx  # convert to indexes
        axs[2].set_title("50 ms")
        axs[2].set_ylim(-0.5, 0.5)
        axs[2].set_xlim(sweepRange, 0)
        axs[2].grid(True)
        for i in range(dtall10.shape[0]):
            axs[2].plot(mean[i, :])

        sweepRange = int(mean.shape[1] / 2)
        redLineStart = int(sweepRange / 512 * redLineIdxStart)
        redLineEnd = int(sweepRange / 512 * redLineIdxStop)

        max = np.absolute(mean[0, :] - mean[1, :])
        for i in range(2, dtall10.shape[0]):
            max = np.maximum(max, np.absolute(mean[0, :] - mean[i, :]))

        max = cv2.GaussianBlur(max, (1, 31), 0, borderType=cv2.BORDER_REPLICATE)

        max50up = np.amax(max[redLineStart:redLineEnd])

        axs[3].set_title(str(round(max50up, 3)))
        axs[3].set_ylim(0, 0.2)
        axs[3].set_xlim(sweepRange, 0)
        axs[3].grid(True)
        axs[3].plot(max)
        axs[3].plot([redLineStart, redLineEnd], [passThreshold, passThreshold], "r")
        axs[3].plot(
            [sweepRange + redLineStart, sweepRange + redLineEnd],
            [passThreshold, passThreshold],
            "r",
        )

        plt.savefig(
            resultDir + f_orig + fileIndexStr + "_up" + ".png",
            bbox_inches="tight",
            dpi=mydpi,
        )

        ######## RESULT PLOT UP END

        print()
        print("Program duration: %s s." % round((time.time() - start_time)))
        print("Done for ", f_orig + fileIndexStr, ".")

        print()
        print("10 ms   up: ", round(max10up, 3))
        print("10 ms down: ", round(max10down, 3))
        print("50 ms   up: ", round(max50up, 3))
        print("50 ms down: ", round(max50down, 3))

        minThreshold = 0.02  # Number too low - something's wrong. Dosconnected cable?

        if (
            max10up < minThreshold
            or max10down < minThreshold
            or max50up < minThreshold
            or max50down < minThreshold
        ):
            testResult = "BAD CONTACT"
            print(
                "Some results are less than "
                + str(minThreshold)
                + ". Suspect for a bad contact."
            )
            duration = 1000  # milliseconds
            freq = 440  # Hz
            for i in range(0, 1):
                winsound.Beep(freq, duration)
                time.sleep(1)
        else:
            if (
                max10up < passThreshold
                and max10down < passThreshold
                and max50up < passThreshold
                and max50down < passThreshold
            ):
                testResult = "OK"
                print("")
                print("    OK    ")
                print("")
                print("   o  o   ")
                print(" \      / ")
                print("  \____/  ")
                print("")
                duration = 100  # milliseconds
                freq = 600  # Hz
                for i in range(0, 3):
                    winsound.Beep(freq, duration)
                    time.sleep(0.1)
            else:
                testResult = "FAIL"
                print("")
                print("   FAIL    ")
                print("")
                print("   *  *   ")
                print("   ____   ")
                print("  /    \  ")
                print(" /      \ ")
                print("")
                duration = 1000  # milliseconds
                freq = 440  # Hz
                for i in range(0, 1):
                    winsound.Beep(freq, duration)
                    time.sleep(1)
        with open("All_galvos.txt", "a") as allgf:
            allgf.write(
                str(datetime.now())
                + ", "
                + f_orig
                + fileIndexStr
                + ", "
                + str(passThreshold)
                + ", "
                + str(round(max10up, 3))
                + ", "
                + str(round(max10down, 3))
                + ", "
                + str(round(max50up, 3))
                + ", "
                + str(round(max50down, 3))
                + ", "
                + testResult
                + "\n"
            )
            allgf.close()

        if useGoogleSheets:
            # Write data to google sheets

            resultData = []
            resultData.append(
                [
                    str(datetime.now()),
                    f_orig + fileIndexStr,
                    passThreshold,
                    round(max10up, 3),
                    round(max10down, 3),
                    round(max50up, 3),
                    round(max50down, 3),
                    testResult,
                ]
            )

            #### Write resultData to the google sheet
            service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range="Results!A:H",
                body={"majorDimension": "ROWS", "values": resultData},
                valueInputOption="USER_ENTERED",
            ).execute()

        if programCycle == programCycles:
            break

    printVer("Exiting.")

    test.write(command=":SOURce1:output:state 0")  # Turn off generator
    test.write(command=":SOURce2:output:state 0")  # Turn off generator

    if useArduino:
        arduino.write("rel 1,0")
        arduino.close()
    test.inst.close()

    # duration = 200  # milliseconds
    # freq = 550  # Hz
    # for i in range(0,3):
    #     winsound.Beep(freq, duration)
    #     time.sleep(0.2)


if __name__ == "__main__":
    main()