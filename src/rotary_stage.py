################################
# Written by: David Song (david.song@carleton.ca)
# Updated: 8/30/2022
# Simple commands to connect to the Arduino and step the stepper motor
################################
import serial
import time

cal=0
arduino=''

class rotaryStage:
    
    #initializes a rotary stage object, which connects to the arduino
    # args: com_port: will almost always be COM10 but may change if USB is unplugged
    def __init__(self,COM_PORT):
        self.arduino = serial.Serial(COM_PORT,115200)
        self.cal = 800 # NEW: 800 steps per degree 1600 steps per revolution uStep enabled
        #OLD: 100 steps per degree, 200 steps per revolution, ignoring skipped steps
    
    def __del__(self):
        self.arduino.close()
    
    #disconnect arduino
    def disconnect(self):
        self.arduino.close()
        
    # Sends an encoded serial message to the arduino
    # The Arduino only accepts an integer number of steps (conversion is 200 steps for 1 rotation (100 steps for 1 degree))
    # Include a "t" at the beginning of the integer to make the motor step faster
    def send_msg(self, msg):
        self.arduino.write(msg.encode())
        #msg = self.arduino.readline().strip()
        #msg2 = msg.decode('ascii')
        return ("moving: " + msg)
    
    def read_msg(self):
        self.arduino.reset_input_buffer()
        time.sleep(1)
        msg = self.arduino.readline().strip()
        msg2 = msg.decode('ascii')
        return (msg2)              
    
    def step_ccw(self,step):
        MessageToArduino = str(round(step*self.cal))
        return self.send_msg(MessageToArduino)
        
    def step_cw(self,step):
        MessageToArduino = str(round(-1*step*self.cal))
        return self.send_msg(MessageToArduino)
    
    def reset_stage(self):
        #some extremely high value > 56000 steps so that the arm will be guaranteed to hit limit switch
        result1 = self.send_msg('a73000') #record the interrupt in the ccw direction (right side)
        print("stay clear of motion, and guide cables")
        time.sleep(20)
        result2 = self.send_msg('a-73000') #record 2nd interrupt in the cw direction (left  side)
        print("stay clear of motion, and guide cables")
        time.sleep(20)
        
        result1 = float(result1)
        result2 = float(result2)
        
        #find difference between the 2
        if result1 > result2:
            delta = result1-result2
        elif result2 > result1:
            delta = result2 - result1
        else:
            delta = 0
            
        print("computing delta: " + str(delta))    
        self.send_msg(str(int(delta/2)))
        print(delta/2)
        time.sleep(20)
        self.send_msg('r')
        print("stage zero set")
        