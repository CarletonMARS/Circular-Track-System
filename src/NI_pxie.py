import nidaqmx
# import sys

class voltageSetter:
    
    def __init__(self, devName='PXI1Slot2'):
        self.devName = devName

    def setVoltage(self, portID='a0', voltageOut=0):
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(
                self.devName+'/'+portID,
                portID,
                0, 
                10
                )
            task.start()
            task.write(voltageOut)
            task.stop()

# if __name__ == "__main__":
#     v_bias = .0
#     vs = voltageSetter();
#     for ch in range(0,32):
#         vs.setVoltage('ao'+str(ch), v_bias)
#     sys.exit(0)
        