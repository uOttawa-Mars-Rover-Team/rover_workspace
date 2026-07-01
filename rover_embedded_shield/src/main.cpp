#include "TaskJointControl.h"
#include <TimerThree.h>

TaskJointControl robotArm(6);

DriverStepper tw("Tower", 55, 54, 16, 17,  5000, 1000000, 1000.0);
DriverStepper wp("Pitch", 4,  5,  3,  2, 10000, 1000000, 2500.0);
DriverStepper wr("Roll",  8,  9,  7,  6, 20000, 1000000, 2500.0);      
DriverStepper ee("EE",   12, 13, 11, 10, 20000, 1000000, 2500.0); 

DriverLA LA1(12);
DriverLA LA2(11);

static unsigned long t0 = 0;


void timerIsr() {
    //sei();
    robotArm.updateSteppers();
}

void setup() {
    Serial.begin(115200);

    robotArm.addStepper(&tw);
    robotArm.addStepper(&wp);
    robotArm.addStepper(&wr);
    robotArm.addStepper(&ee);

    DriverLA_InitI2C();
    robotArm.addLA(&LA1);
    robotArm.addLA(&LA2);

    robotArm.init();

    Timer3.initialize(400);
    Timer3.attachInterrupt(timerIsr);

    Serial.println("Robot Arm Test Initialized");
    t0 = millis();
}

static int8_t lastStage = -1;

void loop() {
    unsigned long cycleTime = (millis() - t0) % 12000;
    int8_t stage;

    if      (cycleTime < 4000)  stage = 1;
    else if (cycleTime < 8000)  stage = 0;
    else                        stage = -1;

    if (stage != lastStage) {
        lastStage = stage;
        if      (stage == 1)  robotArm.parseMessage("1;1;1;1;1;1");
        else if (stage == 0)  robotArm.parseMessage("0;0;0;0;0;0");
        else                  robotArm.parseMessage("-1;-1;-1;-1;-1;-1");
    }

    static unsigned long lastLog = 0;
    if (millis() - lastLog > 3000) {
        if      (stage == 1)  Serial.println("All Forward");
        else if (stage == 0)  Serial.println("All Stop");
        else                  Serial.println("All Reverse");
        lastLog = millis();
    }
}


