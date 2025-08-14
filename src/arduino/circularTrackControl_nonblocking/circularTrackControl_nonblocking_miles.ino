// AccelStepper library
#include <AccelStepper.h>
#include <elapsedMillis.h>
#include <EEPROM.h>  // for persistent zero on UNO R3

// ---- States (original) ----
#define RUNTO     1
#define HOMING    2
#define RESET     3
#define STOPPING  4

// ---- Globals ----
volatile int state;
volatile int enabInt;

elapsedMillis printTime;

// define pin for bipolar motor driver board MP5600
const int dirPin = 8;
const int stepPin = 9;

// init of stepper instance
AccelStepper stage(AccelStepper::DRIVER, stepPin, dirPin);

// ---- Motion reporting flags (NEW) ----
bool moveInProgress = false;   // true while a commanded move is running
bool reportedBusy    = false;  // ensure BUSY prints only once per move
bool reportedDone    = false;  // ensure DONE prints only once per move

// ---- EEPROM markers (NEW) ----
static const int EEPROM_ADDR_MAGIC = 0;          // where we store a 32-bit signature
static const uint32_t ZERO_MAGIC   = 0x5A5AA55A; // "zero is defined" marker

// ---- ISR (original) ----
void pin_ISR() {
  if (enabInt == 1) {
    state = STOPPING;
    enabInt = 0;
  }
}

// ---- Setup (original + NEW restore zero) ----
void setup() {
  Serial.begin(115200);

  pinMode(10, OUTPUT); // microstepping
  pinMode(11, OUTPUT);
  digitalWrite(10, HIGH); // enable uStep
  digitalWrite(11, HIGH);

  attachInterrupt(0, pin_ISR, FALLING);
  enabInt = 1;

  state = RESET;

  stage.setMaxSpeed(4000.0);
  stage.setAcceleration(500.0);
  // stage.moveTo(2000);
  // stage.setSpeed(1000);

  // Restore zero if previously set (assumes mechanics were not moved while off)
  uint32_t magic = 0;
  EEPROM.get(EEPROM_ADDR_MAGIC, magic);
  if (magic == ZERO_MAGIC) {
    // Treat current mechanical position at boot as 0 so 'a0' returns here.
    stage.setCurrentPosition(0);
  }
}

// ---- Main loop ----
void loop() {
  float mSpeed;
  long NumberofSteps;

  // ---- Serial command handling ----
  if (Serial.available() > 0) {
    String DiffAngleSTR = Serial.readStringUntil('\n');
    NumberofSteps = 0;

    // Status query (NEW)
    if (DiffAngleSTR == "?") {
      // BUSY if move armed/in RUNTO and still has distance to go
      bool busy = moveInProgress || (state == RUNTO && stage.distanceToGo() != 0);
      Serial.println(busy ? "BUSY" : "IDLE");
      // do not change state on status query
    }
    // Absolute movement (original)
    else if (DiffAngleSTR.startsWith("a")) {
      DiffAngleSTR.remove(0, 1);
      NumberofSteps = DiffAngleSTR.toInt();
      stage.moveTo(NumberofSteps);

      // Arm reporting for a fresh motion (NEW)
      moveInProgress = true;
      reportedBusy = false;
      reportedDone = false;

      state = RUNTO;
    }
    // Reset origin (original)
    else if (DiffAngleSTR.startsWith("r")) {
      stage.setCurrentPosition(0);
      Serial.println("r");

      // Persist "zero set" marker (NEW)
      EEPROM.put(EEPROM_ADDR_MAGIC, ZERO_MAGIC);

      // Reset flags (origin reset doesn't imply a move)
      moveInProgress = false;
      reportedBusy = false;
      reportedDone = false;
      // state remains unchanged (RESET is fine)
    }
    // Relative movement (original)
    else {
      NumberofSteps = DiffAngleSTR.toInt();
      stage.moveTo(stage.currentPosition() + NumberofSteps);
      Serial.println(NumberofSteps);  // keep your echo

      // Arm reporting for a fresh motion (NEW)
      moveInProgress = true;
      reportedBusy = false;
      reportedDone = false;

      state = RUNTO;
    }
  }

  // Optional once-per-second debug (original, commented)
  if (printTime >= 1000) {
    printTime = 0;
    mSpeed = stage.speed();
    // Serial.print(mSpeed);
    // Serial.print("  ");
    // Serial.print(state);
    // Serial.print("  ");
    // Serial.println(stage.currentPosition());
  }

  // ---- BUSY/DONE handshake (NEW, minimal impact) ----
  // Consider a move "active" while in RUNTO and distanceToGo() != 0
  if (state == RUNTO) {
    if (stage.distanceToGo() != 0) {
      if (moveInProgress && !reportedBusy) {
        Serial.println("BUSY");
        reportedBusy = true;
      }
    } else {
      // Reached target
      if (moveInProgress && !reportedDone) {
        Serial.println("DONE");
        reportedDone = true;
      }
      moveInProgress = false;
      // Return to idle/reset state once target is reached (original behavior)
      state = RESET;
    }
  }

  // ---- Original state machine ----
  switch (state) {
    case RUNTO:
      // Keep stepping toward the target non-blocking
      stage.run();
      break;

    case HOMING:
      // (no changes)
      break;

    case RESET:
      if (enabInt == 0) {
        stage.setAcceleration(500);
        enabInt = 1;
      }
      // stay in RESET until a new command arrives
      break;

    case STOPPING:
      // Increase accel for a quick stop, then block until position reached
      stage.setAcceleration(2000.0);
      stage.stop();
      stage.runToPosition();                  // blocking just for the stop case (as before)
      Serial.println(stage.currentPosition()); // keep your existing print

      // Report DONE once stop completes so host can unblock (NEW)
      if (!reportedDone) {
        Serial.println("DONE");
        reportedDone = true;
      }
      moveInProgress = false;
      reportedBusy = false;

      enabInt = 1;
      stage.setAcceleration(500);
      state = RESET;
      break;
  }
}