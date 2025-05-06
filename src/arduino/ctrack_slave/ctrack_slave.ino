/*
 * Slave i2c code for controlling stage. BLOCKING
 */

//AccelStepper library
#include <AccelStepper.h>
#include <Wire.h>

#define RUNTO 1
#define RST 2

//#define STOPPING 4
//#define HOME 2

volatile int state;
bool stopped = false;

//define pin for bipolar motor driver board MP5600
const int dirPin = 8;
const int stepPin = 9;

//init of stepper instance
AccelStepper az(AccelStepper::DRIVER, stepPin, dirPin);

union Buffer {
  long numberOfSteps;
  byte longBytes[4];
};
Buffer buffer;

//void pin_ISR() {
//  if (enabInt == 1) {
//    state = STOPPING;
//    enabInt = 0;
//  }
//}

//setup acceleration and maximum speed
void setup() {
  pinMode(10, OUTPUT);//enable uStep
  pinMode(11, OUTPUT);
  digitalWrite(10,HIGH);
  digitalWrite(11,HIGH);

  //attachInterrupt(0, pin_ISR, FALLING);
  //enabInt = 1;

  Wire.begin(9);
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);

  state = RST;
  
  az.setMaxSpeed(4000.0);
  az.setAcceleration(500.0);

  Serial.begin(115200);
}

void receiveEvent(int a){
  stopped = false;
  while (Wire.available() > 0){
      buffer.longBytes[0] = Wire.read();
      buffer.longBytes[1] = Wire.read();
      buffer.longBytes[2] = Wire.read();
      buffer.longBytes[3] = Wire.read();
   }
  az.moveTo(az.currentPosition()+buffer.numberOfSteps);
  state = RUNTO;
}

void requestEvent(){
  Wire.write(stopped);
}

void loop() {
  switch (state){
    case RUNTO:
      az.runToPosition();
      stopped = true;
      state = RST;
      break;
    case RST:
      break;
  }
}
