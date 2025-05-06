import pyvisa as visa
from pyvisa.resources import MessageBasedResource
from enum import Enum
import util
import numpy as np


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
IF_BW_FREQ_MIN = 10
IF_BW_FREQ_MAX = 6000
IF_BW_FREQ = [10, 30, 100, 300, 1000, 3000, 3700, 6000]

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
                self.rm = visa.ResourceManager()
                self.vna = self.rm.open_resource(
                    "GPIB1::{}::INSTR".format(address),
                    resource_pyclass=MessageBasedResource,
                )
                self.vna.timeout = (
                    None  # Avoid timing out for time consuming measurements.
                )
                self.connected = True
                #util.dprint("Opened connection to VNA")
            except visa.VisaIOError:
                self.connected = False
                return False

        # Configure display immediately upon connecting
        #self.display_4_channels()

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
            "STAR {a:.{b}f}GHz;".format(a=sweep_params.start / 1.0e9, b=FREQ_DECIMALS)
        )
        self.write(
            "STOP {a:.{b}f}GHz;".format(a=sweep_params.stop / 1.0e9, b=FREQ_DECIMALS)
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
    
    def set_if_bw(self, Freq):
        if Freq >= IF_BW_FREQ_MIN and Freq <= IF_BW_FREQ_MAX:
            self.write("IFBW{}HZ;".format(Freq))
            
    def get_if_bw(self):
        return self.query("IFBW?;")
    
    def WriteData(self, filepath, Angle, Freq):
        Angle = f'{float(Angle):.3f}'
        print("Writing Data Angle: " + Angle + " Deg")
        path = filepath + Angle + ".csv";
        # S11Mag = self.get_mag("CHAN1");
        S12Mag = self.get_mag("CHAN2");
        S21Mag = self.get_mag("CHAN3");
        # S22Mag = self.get_mag("CHAN4");
        # S11Phase = self.get_phase("CHAN1");
        S12Phase = self.get_phase("CHAN2");
        S21Phase = self.get_phase("CHAN3");
        # S22Phase = self.get_phase("CHAN4");
        with open(path, 'w+', newline='', encoding = 'utf-8') as myfile:
            myfile.write("Angle of: " + Angle + "\n")
            myfile.write("Freq [GHz],")
            myfile.write(', '.join(str(item) for item in Freq)+'\n')
            # myfile.write("S11 [Mag],")
            # myfile.write(', '.join(str(item) for item in S11Mag)+'\n')
            # myfile.write("S11 [Phase],")
            # myfile.write(', '.join(str(item) for item in S11Phase)+'\n')
            ########## 2/5/2023 -- Only extracting S12 to improve speed of 
            myfile.write("S12 [Mag],")
            myfile.write(', '.join(str(item) for item in S12Mag)+'\n')
            myfile.write("S12 [Phase],")
            myfile.write(', '.join(str(item) for item in S12Phase)+'\n')
            myfile.write("S21 [Mag],")
            myfile.write(', '.join(str(item) for item in S21Mag)+'\n')
            myfile.write("S21 [Phase],")
            myfile.write(', '.join(str(item) for item in S21Phase)+'\n')
            # myfile.write("S22 [Mag],")
            # myfile.write(', '.join(str(item) for item in S22Mag)+'\n')
            # myfile.write("S22 [Phase],")
            # myfile.write(', '.join(str(item) for item in S22Phase)+'\n')
    
#####TEMPORARY#####
    def WriteData_singlePoint(self, filepath, name, Freq):
        print("Writing Data for point: " + name + " Deg")
        path = filepath + name + ".csv";
        S12Mag = self.get_mag("CHAN2");
        S21Mag = self.get_mag("CHAN3");
        S12Phase = self.get_phase("CHAN2");
        S21Phase = self.get_phase("CHAN3");
        with open(path, 'w+', newline='', encoding = 'utf-8') as myfile:
            myfile.write("point of: " + name + "\n")
            myfile.write("Freq [GHz],")
            myfile.write(', '.join(str(item) for item in Freq)+'\n')
            myfile.write("S12 [Mag],")
            myfile.write(', '.join(str(item) for item in S12Mag)+'\n')
            myfile.write("S12 [Phase],")
            myfile.write(', '.join(str(item) for item in S12Phase)+'\n')
            myfile.write("S21 [Mag],")
            myfile.write(', '.join(str(item) for item in S21Mag)+'\n')
            myfile.write("S21 [Phase],")
            myfile.write(', '.join(str(item) for item in S21Phase)+'\n')
#####TEMPORARY#####
            
    def WriteSelectData(self, filepath, Angle, Freq, Channel):
        print("Writing Data Angle: " + Angle + " Deg")
        path = filepath + Angle + ".csv";
        
        if 's11' in Channel:
            S11Mag = self.get_mag("CHAN1");
            S11Phase = self.get_phase("CHAN1");
        
        if 's12' in Channel:
            S12Mag = self.get_mag("CHAN2");        
            S12Phase = self.get_phase("CHAN2");
        
        if 's22' in Channel:
            S21Mag = self.get_mag("CHAN3");        
            S21Phase = self.get_phase("CHAN3");
        
        if 's21' in Channel:
            S22Mag = self.get_mag("CHAN4");        
            S22Phase = self.get_phase("CHAN4");

        with open(path, 'w+', newline='', encoding = 'utf-8') as myfile:
            myfile.write("Angle of: " + Angle + "\n")
            myfile.write("Freq [GHz],")
            myfile.write(', '.join(str(item) for item in Freq)+'\n')
            myfile.write("S11 [Mag],")
            myfile.write(', '.join(str(item) for item in S11Mag)+'\n')
            myfile.write("S11 [Phase],")
            myfile.write(', '.join(str(item) for item in S11Phase)+'\n')
            myfile.write("S12 [Mag],")
            myfile.write(', '.join(str(item) for item in S12Mag)+'\n')
            myfile.write("S12 [Phase],")
            myfile.write(', '.join(str(item) for item in S12Phase)+'\n')
            myfile.write("S21 [Mag],")
            myfile.write(', '.join(str(item) for item in S21Mag)+'\n')
            myfile.write("S21 [Phase],")
            myfile.write(', '.join(str(item) for item in S21Phase)+'\n')
            myfile.write("S22 [Mag],")
            myfile.write(', '.join(str(item) for item in S22Mag)+'\n')
            myfile.write("S22 [Phase],")
            myfile.write(', '.join(str(item) for item in S22Phase)+'\n')
        
