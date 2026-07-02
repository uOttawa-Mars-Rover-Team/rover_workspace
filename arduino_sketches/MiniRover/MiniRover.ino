#include <AFMotor.h>

int speed = 200;
AF_DCMotor motorLF(2);
AF_DCMotor motorLR(3);

void setup() {
  // put your setup code here, to run once:

}

void loop() {
  motorLF.setSpeed(speed);
  motorLR.setSpeed(speed);

  motorLF.run(BACKWARD);
  motorLR.run(BACKWARD);

  delay(2000);

  motorLF.run(FORWARD);
  motorLR.run(FORWARD);

  delay(2000);


}
