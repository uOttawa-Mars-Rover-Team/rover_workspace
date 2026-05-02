// -------------------Default EndEffector move

// #include "DriverStepper.h"

// // Variable names: stepMotor1, stepMotor2, ...

// // DriverStepper stepMotor1(
// //   "Motor1", //    name:   label for debugging/printing
// //   6,        //    step:   STEP pin number
// //   7,        //    dir:    DIR pin number
// //   17,       //    boot:   BOOT/ENABLE pin (your init() drives HIGH)
// //   68,       //    fault:  FAULT pin (input, pullup)
// //   5000,     //    accel:  acceleration (steps/sec^2)
// //   1000000,  //    range:  maxRange (steps) used for long/continuous move commands
// //   3000.0    //    spd:    max speed (steps/sec)
// // );

// DriverStepper stepMotor1(
//   "EndEffector", // name
//   12,            // step pin
//   13,            // dir pin
//   11,            // boot/enable pin
//   10,            // fault pin
//   20000,         // accel (from reference)
//   1000000,       // range
//   2500.0         // max speed
// );

// static uint8_t direction = 1;
// static float cmdSpeed = 2500; // positive is open for EE
// static unsigned long t0 = millis();

// void setup() {
//   Serial.begin(115200);
//   stepMotor1.init();
// }

// void loop() {

//   if (millis() - t0 < 2000){
//     stepMotor1.moveMotor(cmdSpeed);
//   }
//   else{
//     stepMotor1.moveMotor(0);
//     delay(1000);
//     direction *=-1;
//     t0 = millis();

//     if (cmdSpeed < 3000) {
//       cmdSpeed = (cmdSpeed)*-1;
//     }
//   }
// }



// --------------------- Usage of TaskEE.cpp
// #include "TaskEE.h"

// // Initialize TaskEE object with the verified EE pins
// TaskEE endEffector(
//   "EndEffector", // name
//   12,            // step pin
//   13,            // dir pin
//   11,            // boot/enable pin
//   10,            // fault pin
//   20000,         // accel
//   1000000,       // range
//   2500.0         // max speed
// );

// static float testSpeed = 2500;
// static unsigned long t0 = 0;
// static bool isClosing = true; // Flag to ensure close() runs first

// void setup() {
//   Serial.begin(115200);
//   endEffector.init();
  
//   Serial.println("EE Task Started - Initializing Sequence");
//   t0 = millis();
// }

// void loop() {
//   // Check if 1.5 seconds (1500ms) has passed
//   if (millis() - t0 < 1200) {
//     if (isClosing) {
//       // First 1.5s: Close the EE (negative direction handled by TaskEE)
//       endEffector.close(testSpeed);
//     } else {
//       // Next 1.5s: Open the EE (positive direction handled by TaskEE)
//       endEffector.open(testSpeed);
//     }
//   } else {
//     // Stop the motor briefly between transitions
//     endEffector.stop();
//     delay(1000); // 0.5s pause
    
//     // Toggle between Closing and Opening
//     isClosing = !isClosing;
    
//     // Reset timer for the next 1.5s segment
//     t0 = millis();
    
//     if (isClosing) {
//       Serial.println("Starting CLOSE sequence (1.5s)");
//     } else {
//       Serial.println("Starting OPEN sequence (1.5s)");
//     }
//   }
// }


// ----------------- Usage of TaskJoint.cpp
#include "TaskJointCtrl.h"

// Instantiate the master Joint Controller
TaskJointCtrl robotArm;

// Global timer variable
static unsigned long t0 = 0;

void setup() {
  // Start serial communications
  Serial.begin(115200);
  
  // Initialize all motors (Tower, Pitch, Roll, End Effector)
  robotArm.init();
  
  Serial.println("Robot Arm Sequential Test Initialized");
  
  // Record the start time
  t0 = millis();
}

void loop() {
  unsigned long cycleTime = (millis() - t0) % 6000;

  if (cycleTime < 2000) {
    // STAGE 1 (0s to 1s): Move FORWARD
    robotArm.MoveEE(1); 
    robotArm.MoveWP(1);
    robotArm.MoveWR(1);
    robotArm.MoveTW(1);
    
    static unsigned long lastLog1 = 0;
    if (millis() - lastLog1 > 3000) {
       Serial.println("Stage 1: Forward (+1)");
       lastLog1 = millis();
    }
  } 
  else if (cycleTime < 4000) {
    // STAGE 2 (1s to 2s): STOP
    robotArm.MoveEE(0);
    robotArm.MoveWP(0);
    robotArm.MoveWR(0);
    robotArm.MoveTW(0);

    static unsigned long lastLog2 = 0;
    if (millis() - lastLog2 > 3000) {
       Serial.println("Stage 2: Stop (0)");
       lastLog2 = millis();
    }
  }
  else {
    // STAGE 3 (2s to 3s): Move REVERSE
    robotArm.MoveEE(-1);
    robotArm.MoveWP(-1);
    robotArm.MoveWR(-1);
    robotArm.MoveTW(-1);

    static unsigned long lastLog3 = 0;
    if (millis() - lastLog3 > 6000) {
       Serial.println("Stage 3: Reverse (-1)");
       lastLog3 = millis();
    }
  }
}