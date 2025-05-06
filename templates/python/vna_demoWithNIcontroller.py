# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 23:55:26 2020

@author: aashoor
"""

"""Interfacing class and methods to communicate with an Agilent 8720ES VNA.

Adapted from code written by Carlos Daniel Flores Pinedo
(carlosdanielfp@outlook.com). All these command sequences where based on the
programer's manual for the 8720ES S-Parameter Network Analizer Programmer's
Manual.

Written by Ville Tiukuvaara
"""
import visa
from pyvisa.resources import MessageBasedResource
import myNumbers
from enum import Enum
import serial
import time
import util
from enum import Enum
import numpy as np
import pickle
import struct

import nidaqmx


# Constants for VNA
FREQ_MIN = 0.05e9  # in Hz
FREQ_MAX = 40.05e9  # in Hz
POINTS_MIN = 3  # Number of steps
POINTS_MAX = 1601  # Number of steps
POINTS_DEFAULT = 101
POINTS = [3, 11, 21, 26, 51, 101, 201, 401, 801, 1601]
POWER_MIN = -15  # in dBm
POWER_MAX = -5
AVERAGING_MIN = 1
AVERAGING_MAX = 999
FREQ_DECIMALS = 2
POWER_DECIMALS = 1


class wgTestVoltageSetter:
    
    def __init__(self, devName='PXI1Slot2'):
        self.devName = devName
        
        # Each csv file specifies a voltage setting for channels
        # Tuple below gives the port IDs (recognized by NI) and their order
        self.portIDs = (
            'ao0',
            'ao1',
        )

    
    def setVoltages(self, var_vin, pind_vin):
        

        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(
                self.devName+'/'+'ao0',
                'ao0',
                0, 
                10
                )
            task.start()
            task.write(var_vin)
            task.stop()
        
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(
                self.devName+'/'+'ao1',
                'ao1',
                0, 
                1.87
                )
            task.start()
            task.write(pind_vin)
            task.stop()
        

class VNAError(Exception):
    """Simple error exception for VNA."""

    pass


class CalType(Enum):
    """Represents a calibration type."""

    CALIRESP = 0
    CALIRAI = 1
    CALIS111 = 2  # 1 port cal on port 1
    CALIS221 = 3  # 1 port cal on port 2
    CALIFUL2 = 4  # 2 port cal


# How much data is needed for each calibration type
CAL_DATA_LENGTH = {
    CalType.CALIRESP: 1,
    CalType.CALIRAI: 2,
    CalType.CALIS111: 3,
    CalType.CALIS221: 3,
    CalType.CALIFUL2: 12,
}


class SParam(Enum):
    """Enum for S-params."""

    S11 = "S11"
    S12 = "S12"
    S21 = "S21"
    S22 = "S22"


# Connect each S-param to a VNA channel
CHANNELS = {
    SParam.S11: "CHAN1",
    SParam.S12: "CHAN2",
    SParam.S21: "CHAN3",
    SParam.S22: "CHAN4",
}


class FreqSweepParams:
    """Paremeters for a frequency sweep, not the measured data itself."""

    def __init__(self, start, stop, points, power, averaging, sparams):
        """Initializes with given params.

        Args:
            start (float): start freq in Hz
            stop (float): stop freq in Hz
            points (int): how many points in sweep
            power (float): power level in mdB
            averging (int): number of samples for averaging
            sparams (list): list of SParam objects for which ones to measure
        """
        self.start = start  # Start freq in GHz
        self.stop = stop  # Stop freq in GHz
        self.points = points  # Number of points
        self.power = power  # Power in dBm
        self.averaging = averaging  # Averaging factor
        assert isinstance(sparams, list)
        self.sparams = sparams

    def for_sparams(self, sp):
        """Returns new FreqSweepParams with sparams changed to sp."""
        assert isinstance(sp, list)
        return FreqSweepParams(
            self.start, self.stop, self.points, self.power, self.averaging, sp
        )

    def __str__(self):
        """Return string representation."""
        sp = " ".join([s.value for s in self.sparams])
        return "<FreqSweepParams start:{:.3E} stop:{:.3E} points:{:d} power:{:.2f} averaging:{:.0f} sp: [{}]".format(
            self.start, self.stop, self.points, self.power, self.averaging, sp
        )

    def validation_messages(self, check_sparams=False):
        """Checks if sweep is valid and list of errors (strings) if not.

        Returns None if valid.
        """
        errors = []
        if self.start < FREQ_MIN or self.start > FREQ_MAX:
            errors.append(
                "Start frequency should be {} GHz to {} GHz".format(
                    FREQ_MIN / 1e9, FREQ_MAX / 1e9
                )
            )
        if self.stop < FREQ_MIN or self.stop > FREQ_MAX:
            errors.append(
                "Start frequency should be {} GHz to {} GHz".format(
                    FREQ_MIN / 1e9, FREQ_MAX / 1e9
                )
            )
        if self.start >= self.stop:
            errors.append("Stop frequency should be greater than start frequency")
        if self.points < POINTS_MIN or self.points > POINTS_MAX:
            errors.append(
                "Number of points should be from {} to {}".format(
                    POINTS_MIN, POINTS_MAX
                )
            )
        if self.power < POWER_MIN or self.power > POWER_MAX:
            errors.append(
                "Power level should be between {} dBm and {} dBm".format(
                    POWER_MIN, POWER_MAX
                )
            )
        if self.averaging < AVERAGING_MIN or self.averaging > AVERAGING_MAX:
            errors.append(
                "Averaging factor should be between {} and {}".format(
                    AVERAGING_MIN, AVERAGING_MAX
                )
            )
        if len(self.sparams) == 0 and check_sparams:
            errors.append("No S-parameters are selected")
        if len(errors) > 0:
            return errors
        else:
            return None


class CalStep(Enum):
    """Steps required in calibration sequence."""

    BEGIN = 0
    OPEN_P1 = 1
    SHORT_P1 = 2
    LOAD_P1 = 3
    OPEN_P2 = 4
    SHORT_P2 = 5
    LOAD_P2 = 6
    THRU = 7
    ISOLATION = 8
    INCOMPLETE = 9
    COMPLETE = 10


class CalibrationStepDetails:
    """Info about a given CalStep"""

    def __init__(self, prompt, next_steps):
        self.prompt = prompt
        self.next_steps = next_steps


# Info about a given CalStep
CAL_STEPS = {
    CalStep.BEGIN: "",
    CalStep.OPEN_P1: "Connect OPEN at port 1",
    CalStep.SHORT_P1: "Connect SHORT at port 1",
    CalStep.LOAD_P1: "Connect LOAD at port 1",
    CalStep.OPEN_P2: "Connect OPEN at port 2",
    CalStep.SHORT_P2: "Connect SHORT at port 2",
    CalStep.LOAD_P2: "Connect LOAD at port 2",
    CalStep.THRU: "Connect THRU",
    CalStep.ISOLATION: "Run isolation calibration?",
}


class VNA:
    """Interface with a GPIB instrument using the Visa library.

    Use it to do full 2 port calibrations, set measurement parameters and get measurement data.
    """

    def __init__(self, dummy=False):
        """Init that doesn't do much.

        If dummy is set to true, the VNA acts as a dummy that doesn't actually
        connect to a VNA and can be used for testing.
        """
        self.dummy = dummy
        self.cal_ok = False
        self.connected = False
        self.cal_type = None
        self.cal_params = None
        self.averaging_factor = 1

        self.rm = None
        self.vna = None

    def __del__(self):
        """Disconnect from VNA if object deleted."""
        try:
            self.disconnect()
        except:
            pass

    def connect(self, address):
        """Establish a connection with the VNA.

        Returns true after successful connection.
        """
        if self.dummy:
            self.connected = True
        else:
            try:
                # print('MADE IT HERE')
                
                self.rm = visa.ResourceManager()
                self.vna = self.rm.open_resource(
                    "GPIB0::{}::INSTR".format(address),
                    resource_pyclass=MessageBasedResource,
                )
                
                
                self.vna.timeout = (
                    None  # Avoid timing out for time consuming measurements.
                )
                self.connected = True
                
                util.dprint("Opened connection to VNA")
                
                
            except visa.VisaIOError:
        
                
                self.connected = False
                return False

        # Configure display immediately upon connecting
        
        self.display_4_channels()
        
        

        self.cal_type = self.get_cal_type()
        self.cal_ok = self.cal_type is not None

    def disconnect(self):
        """Disconnect from VNA."""
        if self.dummy:
            self.connected = False
            self.cal_ok = False
            return

        if self.connected:
            try:
                self.vna.close()
            except visa.VisaIOError:
                pass
            self.vna = None
            self.rm = None

        self.connected = False
        self.cal_ok = False
        self.cal_params = None

    def write(self, msg):
        """Write message to VNA."""
        if len(msg) < 200:
            # Print out short messages for debugging
            util.dprint(msg)
        else:
            util.dprint(msg[0:30] + " ...")
        if not self.dummy:
            self.vna.write(msg)

    def read(self):
        """Read message from VNA."""
        if self.dummy:
            return "1"
        else:
            return self.vna.read()

    def query(self, msg):
        """Query (write and read) with VNA."""
        if len(msg) < 200:
            util.dprint(msg)
        else:
            util.dprint(msg[0:30] + " ...")
        if self.dummy:
            return "1"
        else:
            return self.vna.query(msg)

    def display_4_channels(self):
        """Displays the 4 channels in a 2x2 grid with one slot for each.
        Assigns S11 to CHAN1, S12 to CHAN3, S21 to CHAN2, and S22 to CHAN4."""
        self.write("DUACON;")
        self.write("SPLID4;")
        self.write("OPC?;WAIT;")
        self.write("{};AUTO;".format(CHANNELS[SParam.S11]))
        self.write("S11;")
        self.write("AUXCON;")
        self.write("LOGM;")
        self.write("{};AUTO;".format(CHANNELS[SParam.S12]))
        self.write("S21;")
        self.write("AUXCON;")
        self.write("LOGM;")
        self.write("{};AUTO;".format(CHANNELS[SParam.S21]))
        self.write("S12;")
        self.write("LOGM;")
        self.write("{};AUTO;".format(CHANNELS[SParam.S22]))
        self.write("S22;")
        self.write("LOGM;")

    def get_cal_type(self):
        """Checks what kind of calibration is present in VNA.

        Returns the first kind of calibration that is detected
        """
        for t in CalType:
            name = t.name
            if bool(int(self.query(name + "?;"))):
                return t
        return None

    def set_sweep_params(self, sweep_params):
        """Set the FreqSweepParams for measurement."""
        assert isinstance(sweep_params, FreqSweepParams)
        # self.measurement_params = sweep_params
        self.write(
            "STAR {a:.{b}f}GHz;".format(a=sweep_params.start / 1e9, b=FREQ_DECIMALS)
        )
        self.write(
            "STOP {a:.{b}f}GHz;".format(a=sweep_params.stop / 1e9, b=FREQ_DECIMALS)
        )
        self.write("POIN {a:d};".format(a=sweep_params.points))
        self.write("POWE {a:.{b}f};".format(a=sweep_params.power, b=POWER_DECIMALS))
        self.averaging_factor = sweep_params.averaging

    def get_sweep_params(self):
        """Get the FreqSweepParams for measurement."""
        start = float(self.query("STAR?;"))
        stop = float(self.query("STOP?;"))
        points = int(float(self.query("POIN?;")))
        power = float(self.query("POWE?;"))

        if self.dummy and isinstance(self.cal_params, FreqSweepParams):
            return self.cal_params

        return FreqSweepParams(start, stop, points, power, self.averaging_factor, [])

    def sweep(self):
        """Triggers a sweep (with averging if selected)."""
        self.write("CONT;")
        for i in ("CHAN1", "CHAN2", "CHAN3", "CHAN4"):
            self.write(i + ";AUTO;")
            if self.averaging_factor < 2:
                self.write("AVEROOFF;")
            else:
                self.write("AVERFACT{};".format(self.averaging_factor))
                self.write("AVEROON;")

        if not self.dummy:
            # self.vna.query_ascii_values("OPC?;SING;")
            if self.averaging_factor < 2:
                self.query("OPC?;SING;")
            else:
                self.query("OPC?;NUMG{};".format(self.averaging_factor))

    def get_freq(self):
        """Returns a numpy array with the values of frequency
        from the x-axis.
        """
        self.write(
            "OUTPLIML;"
        )  # Asks for the limit test results to extract the stimulus components
        aux = []
        x = self.read().split("\n")  # Split the string for each point

        if self.dummy:
            return np.empty(0)

        for i in x:
            if i == "":
                break
            aux.append(
                float(i.split(",")[0])
            )  # Split each string and get only the first value as a float number
        return np.asarray(aux)

    def get_mag(self, chan="CHAN1"):
        """Returns a numpy array with the logarithmic magnitude values
        on the channel specified.

        Args:
            chan (str): String specifying the channel to get the values from
        """
        self.write("FORM5;")  # Use binary format to output data
        self.write(chan + ";")  # Select channel
        self.write("LOGM;")  # Show logm values
        res = []

        if self.dummy:
            return np.empty(0)

        aux = self.vna.query_binary_values(
            "OUTPFORM;", container=tuple, header_fmt="hp"
        )  # Ask for the values from channel and format them as tuple
        for i in range(
            0, len(aux), 2
        ):  # Only get the first value of every data pair because the other is zero
            res.append(aux[i])
        return np.asarray(res)

    def get_phase(self, chan="CHAN1"):
        """Returns a numpy array with the phase values
        on the channel specified.

        Args:
            chan (str): String specifying the channel to get the values from
        """
        self.write("FORM5;")  # Use binary format to output data
        self.write(chan + ";")
        self.write("PHAS;")
        res = []

        if self.dummy:
            return np.empty(0)

        aux = self.vna.query_binary_values(
            "OUTPFORM;", container=tuple, header_fmt="hp"
        )  # Ask for the values from channel and format them as tuple
        for i in range(
            0, len(aux), 2
        ):  # Only get the first value of every data pair because the other is zero
            res.append(aux[i])
        return np.asarray(res)

    def measure(self, sweep_params):
        """Perform a measurement of the given sweep_params.

        Returns a list of MeasData objects.
        """
        assert isinstance(sweep_params, FreqSweepParams)
        
        if not self.connected:
            return None
        
        self.set_sweep_params(sweep_params)
        # if not self.dummy:
        #    sweep_params_read = self.get_sweep_params()

        self.sweep()
        freq = self.get_freq()

        if self.dummy:
            freq = np.linspace(
                sweep_params.start, sweep_params.stop, sweep_params.points
            )

        data = []
        self.write("Entering")
        for sp in sweep_params.sparams:
            self.write(sp)
            mag = self.get_mag(CHANNELS[sp])
            phase = self.get_phase(CHANNELS[sp])
            self.write("IN S PARAM")
            # For a dummy object, generate random data
            if self.dummy:
                diff = max(freq) - min(freq)
                mag = (
                    -5
                    + 3 / diff * (freq - sweep_params.start)
                    + np.random.random(len(freq)) * 0.5
                )
                phase = (
                    -180
                    + 360 / diff * (freq - sweep_params.start)
                    + np.random.random(len(freq)) * 5
                )

            data.append(MeasData(sweep_params.for_sparams([sp]), freq, mag, phase))

        return data

    def measure_all(self, sweep_params):
        """Perform a measurement of all S-parameters for current calibration.

        Returns a list of MeasData objects.
        """
        assert isinstance(sweep_params, FreqSweepParams)

        if self.cal_type == CalType.CALIFUL2:
            sweep_params = sweep_params.for_sparams([sp for sp in SParam])
        elif self.cal_type == CalType.CALIS111:
            sweep_params = sweep_params.for_sparams([SParam.S11])
        elif self.cal_type == CalType.CALIS221:
            sweep_params = sweep_params.for_sparams([SParam.S22])

        return self.measure(sweep_params)
    
class MeasData:
    """Represents a frequency sweep measurement of a single S-param."""

    def __init__(self, sweep_params, freq, mag, phase):
        assert isinstance(sweep_params, FreqSweepParams)
        self.sweep_params = sweep_params
        self.freq = freq
        self.mag = mag
        self.phase = phase


def WriteData(filepath, Angle, Freq):
    """
    path is where it is being saved as a csv with the labeled file
    the Rest command restarts averaging on the VNA
    the time.sleep allows 5 seconds for averaging to happen before getting data, this can be increased
    """
    path = filepath + Angle + ".csv"
    v.write("REST;")
    time.sleep(2)
    print("Getting and Writing Datafile: " + Angle)
    
    S11Phase = v.get_phase("CHAN1")
    
    S12Phase = v.get_phase("CHAN2")
    S21Phase = v.get_phase("CHAN3")
    S22Phase = v.get_phase("CHAN4")
    S11Mag = v.get_mag("CHAN1")
    S12Mag = v.get_mag("CHAN2")
    S21Mag = v.get_mag("CHAN3")
    S22Mag = v.get_mag("CHAN4")

    
    with open(path, 'w+', newline = '', encoding = 'utf-8') as myfile:
        # myfile.write("Angle of: " + Angle + "\n")
        myfile.write("Freq [GHz],")
        myfile.write(', '.join(str(item) for item in Freq)+'\n')
        
        myfile.write("S11 [dB],")
        myfile.write(', '.join(str(item) for item in S11Mag)+'\n')
        myfile.write("S12 [dB],")
        myfile.write(', '.join(str(item) for item in S12Mag)+'\n')
        myfile.write("S21 [dB],")
        myfile.write(', '.join(str(item) for item in S21Mag)+'\n')
        myfile.write("S22 [dB],")
        myfile.write(', '.join(str(item) for item in S22Mag)+'\n')
        
        myfile.write("S11 [Phase],")
        myfile.write(', '.join(str(item) for item in S11Phase)+'\n')
        myfile.write("S12 [Phase],")
        myfile.write(', '.join(str(item) for item in S12Phase)+'\n')
        myfile.write("S21 [Phase],")
        myfile.write(', '.join(str(item) for item in S21Phase)+'\n')
        myfile.write("S22 [Phase],")
        myfile.write(', '.join(str(item) for item in S22Phase)+'\n')
        

if __name__ == "__main__":
    Cal = 35075/82.10591482
    """
    Cal is Steps/Degree
    Meas 1 is to do measurements, 0 means it will move the angle specified
    """
    Meas = 1
    
    if Meas == 0:
        """
        Start Angle is what angle you are starting at
        End Angle is where you want to end up at
        COM5 is the typical arduino communication channel can change to different COM Number
        """
        pass
    else:
        # """
        # Start Angle, End Angle and Increment are all in thousandths of a degree so -10,000 is -10 degrees
        # Increment is how often you want to measure
        # """
        # StartAngle = 0
        # EndAngle = 4000
        # Increment = 1000
        # """
        # Cur is to keep track of any half steps that might occur
        # """
        # Cur = 0
        util.debug_messages = False
        v = VNA(False)
        v.connect(16)
    
        
        # arduino = serial.Serial('COM5', 115200)
        time.sleep(1)
        Freq = v.get_freq()/1e9
        

        path = 'C:\\Users\\keiganmacdonell\\Desktop\\July30__AAUC-measurement\\measurements\\'
       
       
        # var_vin = np.linspace(0, 20, 21)
        # pind_vin = np.linspace(0.6,1.87,20)
        
        var_vin = np.linspace(0, 10, 11)
        # var_vin = (20.0,)
        pind_vin = np.linspace(0.6,1.87,10)
        
        
        
        # Set up wgTestVoltageSetter
        vs = wgTestVoltageSetter()
        
        
        for vin1 in var_vin:
            
            for vin2 in pind_vin:
                
                # Set output voltages
                
                vs.setVoltages(var_vin, vin2)
                # vs.setVoltages(0, vin2) # for use with the power supply
            
                fileName = 'vV-' + '{:.2f}'.format(vin1) + '_vP-' + '{:.2f}'.format(vin2)
            
                WriteData(path, fileName, Freq)
                
                