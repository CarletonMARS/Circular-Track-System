//AccelStepper library
#include <AccelStepper.h>
#include <elapsedMillis.h>

#define RUNTO 1
#define HOMING 2
#define RESET 3
#define STOPPING 4

volatile int state;
volatile int enabInt;

elapsedMillis printTime;

//define pin for bipolar motor driver board MP5600
const int dirPin = 8;
const int stepPin = 9;

//init of stepper instance
AccelStepper stage(AccelStepper::DRIVER, stepPin, dirPin);

void pin_ISR() {
  if (enabInt == 1) {
    state = STOPPING;
    enabInt = 0;
  }
}

//setup acceleration and maximum speed
void setup() {
  Serial.begin(115200);

  pinMode(10, OUTPUT); //microstepping
  pinMode(11, OUTPUT);
  digitalWrite(10,HIGH); //enable uStep
  digitalWrite(11,HIGH);

  attachInterrupt(0, pin_ISR, FALLING);
  enabInt = 1;

  state = RESET;
  
  stage.setMaxSpeed(4000.0);
  stage.setAcceleration(500.0);
  //stage.moveTo(2000);
  //stage.setSpeed(1000);
}

void loop() {
  float mSpeed;
  long NumberofSteps;
  
  if (Serial.available() > 0) {
    String DiffAngleSTR = Serial.readStringUntil('\n');
    NumberofSteps =0;

    if (DiffAngleSTR.startsWith("a")){  //absolute movement, will use internally set origin point
      DiffAngleSTR.remove(0,1);
      NumberofSteps = DiffAngleSTR.toInt();
      stage.moveTo(NumberofSteps);
    }else if (DiffAngleSTR.startsWith("r")){ //reset origin
      stage.setCurrentPosition(0);
      Serial.println("r");
    }else{  //relative movement
      NumberofSteps = DiffAngleSTR.toInt();
      stage.moveTo(stage.currentPosition()+NumberofSteps);
      Serial.println(NumberofSteps);
    }
    state = RUNTO;
  }
  
  if (printTime >= 1000) {    // happens once per second
    printTime = 0;
    mSpeed = stage.speed();

//    Serial.print(mSpeed);
//    Serial.print("  ");
//    Serial.print(state);
//    Serial.print("  ");
//    Serial.println(stage.currentPosition());
  }
    
  switch (state){
    case RUNTO:
      stage.run();
      break;
    case HOMING:
      break;
    case RESET:
      if (enabInt == 0){
        stage.setAcceleration(500);
        enabInt = 1;
      }
      break;
    case STOPPING:
      stage.setAcceleration(2000.0);
      stage.stop();
      stage.runToPosition();
      Serial.println(stage.currentPosition());
      enabInt = 1;
      stage.setAcceleration(500);
      state = RESET;
    break;
  }
}
