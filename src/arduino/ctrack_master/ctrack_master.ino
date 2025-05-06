/*
 * Master i2c code for reading steps from pc and 
 * reading analog input from pwr meter, and putting it
 * onto serial bus
 */
#include <Wire.h>
#include <elapsedMillis.h>

#define RUNTO 1
#define WAIT 2
#define REPORT 3
#define RST 4

volatile int state;
bool stopped;

union Buffer {
  long numberOfSteps;
  byte longBytes[4];
};
Buffer buffer;

const int transmitInterval = 500;
float sum = 0;
int samples = 0;
elapsedMillis elapsed;

void setup() {
  Wire.begin();
  
  pinMode(A0, INPUT);

  Serial.begin(115200);

  state = REPORT;
}

void loop() {
  if (Serial.available() > 0) {
    String DiffAngleSTR = Serial.readStringUntil('\n');
    buffer.numberOfSteps =0;
    buffer.numberOfSteps = DiffAngleSTR.toInt();
    state = RUNTO;
  }

  switch (state){
    case RUNTO:
      Wire.beginTransmission(9);
        for(int i=0;i<4;i++){
          Wire.write(buffer.longBytes[i]);
        }
      Wire.endTransmission();
      state = WAIT;
    break;
    
    case WAIT:
      
      Wire.requestFrom(9,1);
      
      // KM on 2023-06-11
      while (Wire.available() == 0) {
        Wire.requestFrom(9,1);
        if (Wire.available() > 0) {
          break;
        }
      }
      // end of addition
      
      if (Wire.available()>0){
        stopped = Wire.read();
      }
      if (stopped){
        state = REPORT;
      }else{
        state = WAIT;
      }
    break;

    case REPORT:
      sum += analogRead(A0);
      samples += 1;
      
      if (elapsed >= transmitInterval) {
        int avg = sum/samples;
        sum = 0;
        samples = 0;
        elapsed = 0;
        Serial.println(avg);
      }
    break;

    case RST:
    break;
  }
}
