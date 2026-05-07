/*
 * Description: rover_embedded_shield demo entry point.
 *              Instantiates 3 ArmTask_CameraMount and exercises them with a
 *              non-blocking XY sweep so the servo subsystem can be smoke-
 *              tested on a Mega 2560. The application-layer command parser
 *              (ArmApp_Comms) lives in a later branch; this main is a stand-
 *              in so the driver and task layers can be flashed in isolation.
 * Authors:
 */
//------------------------------------------
//  Includes
//------------------------------------------
#include <Arduino.h>
#include "ArmTask_CameraMount.h"

//------------------------------------------
//  Defines
//------------------------------------------
#define BAUDRATE                9600
#define MOUNT_COUNT             3
#define DEFAULT_MS_PER_STEP     60      /* matches legacy servo_delay = 60 ms */
#define SWEEP_DWELL_MS          1000    /* pause once mounts settle */

/* Placeholder PWM pin assignments. Replace with real wiring once the team
 * confirms which Mega PWM pins (2-13, 44-46) the camera servos land on. */
#define CAM0_PIN_X  2
#define CAM0_PIN_Y  3
#define CAM1_PIN_X  4
#define CAM1_PIN_Y  5
#define CAM2_PIN_X  6
#define CAM2_PIN_Y  7

//------------------------------------------
//  Datatype Definitions
//------------------------------------------

//------------------------------------------
//  Global Variables
//------------------------------------------
ArmTask_CameraMount cameras[MOUNT_COUNT];

//------------------------------------------
//  Local Variables
//------------------------------------------
static unsigned long sweepNext_ms = 0;
static uint8_t       sweepStep    = 0;

//------------------------------------------
//  Local Function Prototypes
//------------------------------------------
static void runDemoSweep(unsigned long now_ms);
static bool allMountsIdle();

//------------------------------------------
//  Global Function Definitions
//------------------------------------------
void setup()
{
    Serial.begin(BAUDRATE);

    cameras[0].init(CAM0_PIN_X, CAM0_PIN_Y);
    cameras[1].init(CAM1_PIN_X, CAM1_PIN_Y);
    cameras[2].init(CAM2_PIN_X, CAM2_PIN_Y);

    Serial.println(F("rover_embedded_shield: 3 camera mounts initialized"));
}

void loop()
{
    unsigned long now = millis();

    for (uint8_t i = 0; i < MOUNT_COUNT; i++) {
        cameras[i].tick(now);
    }

    runDemoSweep(now);
}

//------------------------------------------
//  Local Function Definitions
//------------------------------------------

/**
 * @brief Cycle through hard-coded XY targets so a tester can see all 3 mounts
 *        actually move on hardware. To be replaced with the real serial
 *        command dispatcher (ArmApp_Comms) in a later branch.
 *
 * @return void
 */
static void runDemoSweep(unsigned long now_ms)
{
    if (now_ms < sweepNext_ms) {
        return;
    }
    if (!allMountsIdle()) {
        return;
    }

    switch (sweepStep) {
        case 0:
            cameras[0].setTargetXY(45,  135, DEFAULT_MS_PER_STEP);
            cameras[1].setTargetXY(135, 45,  DEFAULT_MS_PER_STEP);
            cameras[2].setTargetXY(90,  90,  DEFAULT_MS_PER_STEP);
            break;
        case 1:
            cameras[0].setTargetXY(135, 45,  DEFAULT_MS_PER_STEP);
            cameras[1].setTargetXY(45,  135, DEFAULT_MS_PER_STEP);
            cameras[2].setTargetXY(0,   180, DEFAULT_MS_PER_STEP);
            break;
        case 2:
        default:
            cameras[0].setTargetXY(90,  90,  DEFAULT_MS_PER_STEP);
            cameras[1].setTargetXY(90,  90,  DEFAULT_MS_PER_STEP);
            cameras[2].setTargetXY(180, 0,   DEFAULT_MS_PER_STEP);
            break;
    }

    sweepStep    = (sweepStep + 1) % 3;
    sweepNext_ms = now_ms + SWEEP_DWELL_MS;
}

static bool allMountsIdle()
{
    for (uint8_t i = 0; i < MOUNT_COUNT; i++) {
        if (!cameras[i].isIdle()) {
            return false;
        }
    }
    return true;
}
