#include <AccelStepper.h>
#include <MultiStepper.h>
#include <Servo.h>
#include <ezButton.h>
#include <Adafruit_NeoPixel.h>


Servo funnelFlap;
Servo linearActuator;
Servo drill;
Servo vacuum;

Adafruit_NeoPixel strip(30, 19, NEO_GRB + NEO_KHZ800);

ezButton vacTopLS(29);
ezButton vacBottomLS(18);

AccelStepper rotaryArray(AccelStepper::DRIVER, 10, 9);
AccelStepper vacTube(AccelStepper::DRIVER, 2, 3);


void setup() {
  Serial.begin(15200);
  Serial.setTimeout(10);

  strip.begin();
  strip.fill(strip.Color(244, 224, 181));
  strip.setBrightness(50);
  strip.show();

  vacTube.setMaxSpeed(3000);
  vacTube.setAcceleration(1000);
  vacTube.setSpeed(3000);
  rotaryArray.setMaxSpeed(3000);
  rotaryArray.setAcceleration(1000);
  rotaryArray.setSpeed(3000);

  vacTopLS.setDebounceTime(50);
  vacBottomLS.setDebounceTime(50);

  funnelFlap.attach(0);
  funnelFlap.write(0);

  linearActuator.attach(12);
  linearActuator.write(90);

  vacuum.attach(11);
  vacuum.write(90);

  drill.attach(13);
  drill.write(90);
}


void messageReader() {
  if (Serial.available() > 0) {
    int incomingMsg = Serial.parseInt();
    if (incomingMsg == 102) {
      flap();
    }else if (incomingMsg == 119) {
      moveVacTubeUp();
      Serial.println("Moving vac tube up");
    }else if (incomingMsg == 115) {
      moveVacTubeDown();
      Serial.println("Moving vac tube down");
    }else if (incomingMsg == 273) {
      moveLinearActuatorUp();
      Serial.println("Moving linear actuator up");
    }else if (incomingMsg == 274) {
      moveLinearActuatorDown();
      Serial.println("Moving linear actuator down;");
    }else if (incomingMsg == 118) {
      toggleVac();
    }else if (incomingMsg == 49) {
      drillSpeed(0);
      Serial.println("Drill stopped;");
    }else if (incomingMsg == 50) {
      drillSpeed(1);
      Serial.println("Drill 25% speed;");
    }else if (incomingMsg == 51) {
      drillSpeed(2);
      Serial.println("Drill 50% speed;");
    }else if (incomingMsg == 52) {
      drillSpeed(3);
      Serial.println("Drill 75% speed;");
    }else if (incomingMsg == 53) {
      drillSpeed(4);
      Serial.println("Drill 100% speed;");
    }else if (incomingMsg == 54) {
      drillSpeed(-1);
      Serial.println("Drill reversing;");
    }else if (incomingMsg == 275) {
      moveRotaryArrayRight();
      Serial.println("Moving rotary array right;");
    }else if (incomingMsg == 276) {
      moveRotaryArrayLeft();
      Serial.println("Moving rotary array left;");
    } else if (incomingMsg == 112)  {
      panic();
      Serial.println("everything stopped;");
    } else if (incomingMsg == 100) {
      discoMode();
      Serial.println("Party!;");
    }
  }
}

int flapStatus = 0;

void flap() {
  if (flapStatus == 0) {
    funnelFlap.write(180);
    flapStatus = 1;
    Serial.println("flap open;");
  } else if (flapStatus == 1){
    funnelFlap.write(0);
    flapStatus = 0;
    Serial.println("flap closed;");
  }
}

bool vacTubeMoving = false;
int vacTubeDir = 0;

void moveVacTubeUp() {
  if (vacTubeMoving == false) {
    vacTubeMoving = true;
    vacTubeDir = 1;
    vacTube.move(100000);
  } else if (vacTubeMoving == true){
    vacTubeMoving = false;
    vacTubeDir = 0;
    vacTube.stop();
  }
}


void moveVacTubeDown() {
  if (vacTubeMoving == false) {
    vacTubeMoving = true;
    vacTubeDir = -1;
    vacTube.move(-100000);
  } else if (vacTubeMoving == true){
    vacTubeMoving = false;
    vacTubeDir = 0;
    vacTube.stop();
  }
}

bool linearActuatorMoving = false;


void moveLinearActuatorUp() {
  if (linearActuatorMoving == false) {
    linearActuatorMoving = true;
    linearActuator.write(90);
  } else {
    linearActuator.write(90);
    linearActuatorMoving = false;
    while(Serial.available()){Serial.read();}
  }
}

void moveLinearActuatorDown() {
  if (linearActuatorMoving == false) {
    linearActuatorMoving = true;
    linearActuator.write(180);
  } else {
    linearActuator.write(90);
    linearActuatorMoving = false;
    while(Serial.available()){Serial.read();}
  }
}

bool vacStatus = 0;

void toggleVac() {
  if (vacStatus == 0) {
    vacStatus = 1;
    Serial.println("Vac on;");
    for (int i = 90; i >= 0; i = i -1) {
      vacuum.write(i);
      delay(10);
    }


  } else if (vacStatus = 1) {
    vacuum.write(90);
    vacStatus = 0;
    Serial.println("Vac off;");
    for (int i = 0; i <= 90; i++) {
      vacuum.write(i);
      delay(10);
    }
  }
}

void drillSpeed(int speed) {
  if (speed == 0) {
    drill.write(90);
  } else if (speed == 1) {
    drill.write(112.5);
  } else if (speed == 2) {
    drill.write(135);
  } else if (speed == 3) {
    drill.write(157.5);
  } else if (speed == 4) {
    drill.write(180);
  } else if (speed == -1) {
    drill.write(45);
  }
}


bool rotaryArrayMoving = false;

void moveRotaryArrayRight() {
  if (rotaryArrayMoving == false) {
    rotaryArrayMoving = true;
    rotaryArray.move(100000);
  } else if (rotaryArrayMoving == true){
    rotaryArrayMoving = false;
    rotaryArray.stop();
  }
}

void moveRotaryArrayLeft() {
  if (rotaryArrayMoving == false) {
    rotaryArrayMoving = true;
    rotaryArray.move(-100000);
  } else if (rotaryArrayMoving == true){
    rotaryArrayMoving = false;
    rotaryArray.stop();
  }
}


void panic() {
  rotaryArrayMoving = false;
  rotaryArray.stop();
  vacTubeMoving = false;
  vacTubeDir = false;
  vacTube.stop();
  funnelFlap.write(0);
  linearActuatorMoving = false;
  linearActuator.write(90);
  drill.write(90);
  vacuum.write(90);
}

bool discoModeStatus = false;

void discoMode() {
  if (discoModeStatus == false) {
    strip.gamma32(0);
    strip.show();
  } else {
    strip.fill(strip.Color(244, 224, 181));
    strip.show();
  }
}


void loop() {
  vacTopLS.loop();
  vacBottomLS.loop();
  messageReader();
  if (vacTubeMoving == true) {
    if (vacTubeDir == 1) {
      if (vacTopLS.getState()) {
        vacTube.run();
      } else {
        vacTube.stop();
        vacTubeDir = 0;
        vacTubeMoving = 0;
      }
    } else if (vacTubeDir == -1) {
      if (vacBottomLS.getState()) {
        vacTube.run();
      } else {
        vacTube.stop();
        vacTubeDir = 0;
        vacTubeMoving = 0;
      }
    }
  }

  if (rotaryArrayMoving == true) {
    rotaryArray.run();
  }
}


