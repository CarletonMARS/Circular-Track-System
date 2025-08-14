// AccelStepper library
#include <AccelStepper.h>
#include <elapsedMillis.h>
#include <EEPROM.h>  // NEW: for persistent zero on UNO R3

#define RUNTO 1
#define HOMING 2
#define RESET 3
#define STOPPING 4

volatile int state;
volatile int enabInt;

elapsedMillis printTime;

// define pin for bipolar motor driver board MP5600
const int dirPin = 8;
const int stepPin = 9;

// init of stepper instance
AccelStepper stage(AccelStepper::DRIVER, stepPin, dirPin);

// --- NEW: simple motion reporting flags ---
bool moveInProgress = false;    // true while a commanded move is running
bool reportedBusy    = false;   // ensure BUSY prints only once per move
bool reportedDone    = false;   // ensure DONE prints only once per move

// --- NEW: EEPROM constants for "zero set" persistence ---
static const int EEPROM_ADDR_MAGIC = 0;         // where we store a 32-bit signature
static const uint32_t ZERO_MAGIC   = 0x5A5AA55A; // "zero is defined" marker

void pin_ISR() {
  if (enabInt == 1) {
    state = STOPPING;
    enabInt = 0;
  }
}

// setup acceleration and maximum speed
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

  // --- NEW: restore zero if previously set (open-loop assumption: not moved while off) ---
  uint32_t magic = 0;
  EEPROM.get(EEPROM_ADDR_MAGIC, magic);
  if (magic == ZERO_MAGIC) {
    // Treat the current mechanical position at boot as 0 (same reference as when 'r' was set),
    // so 'a0' returns here after power cycle.
    stage.setCurrentPosition(0);
  }
}

void loop() {
  float mSpeed;
  long NumberofSteps;

  // ---- Serial command handling ----
  if (Serial.available() > 0) {
    String DiffAngleSTR = Serial.readStringUntil('\n');
    NumberofSteps = 0;

    // NEW: status query
    if (DiffAngleSTR == "?") {
      // We are "BUSY" if a move is in progress or the state machine is in RUNTO and not yet at target
      bool busy = moveInProgress || (state == RUNTO && stage.distanceToGo() != 0);
      Serial.println(busy ? "BUSY" : "IDLE");
      // do not change state on status query
    }
    else if (DiffAngleSTR.startsWith("a")) {  // absolute movement, uses internally set origin point
      DiffAngleSTR.remove(0, 1);
      NumberofSteps = DiffAngleSTR.toInt();
      stage.moveTo(NumberofSteps);

      // NEW: arm reporting for a fresh motion
      moveInProgress = true;
      reportedBusy = false;
      reportedDone = false;

      state = RUNTO;
    }
    else if (DiffAngleSTR.startsWith("r")) {  // reset origin
      stage.setCurrentPosition(0);
      Serial.println("r");

      // NEW: mark that zero has been defined, so on next boot we restore 0 at current mech position
      EEPROM.put(EEPROM_ADDR_MAGIC, ZERO_MAGIC);

      // reset flags (origin reset doesn't imply a move)
      moveInProgress = false;
      reportedBusy = false;
      reportedDone = false;
      // (state remains as-is; RESET is fine too)
    }
    else {  // relative movement
      NumberofSteps = DiffAngleSTR.toInt();
      stage.moveTo(stage.currentPosition() + NumberofSteps);
      Serial.println(NumberofSteps);  // keep your echo

      // NEW: arm reporting for a fresh motion
      moveInProgress = true;
      reportedBusy = false;
      reportedDone = false;

      state = RUNTO;
    }
  }

  if (printTime >= 1000) {  // happens once per second
    printTime = 0;
    mSpeed = stage.speed();

    // // debug prints if needed
    // Serial.print(mSpeed);
    // Serial.print("  ");
    // Serial.print(state);
    // Serial.print("  ");
    // Serial.println(stage.currentPosition());
  }

  // ---- NEW: emit BUSY/DONE once per move without changing your timing model ----
  // We consider a move "active" while in RUNTO and distanceToGo() != 0
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
      // Return to idle/reset state once target is reached
      state = RESET;
    }
  }

  // ---- Original state machine behavior ----
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
      stage.runToPosition();  // blocking just for the stop case (as before)
      Serial.println(stage.currentPosition());  // keep your existing print

      // NEW: report DONE once stop completes (so host can unblock)
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