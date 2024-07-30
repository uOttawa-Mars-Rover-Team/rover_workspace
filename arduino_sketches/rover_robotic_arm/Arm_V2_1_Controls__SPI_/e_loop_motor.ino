

  //Every enc_delay ms, sample encoder data and move motors when needed
  if (millis() - encoder_t >= enc_delay) {

    //For joints TW - WP, retrive encoder position and store as radians
    for (int i = TW ; i <= WP ; i++) {
      updatePositionAndVelocity(i, encoder_t);
    }

    //update timer until enc_delay is over
    encoder_t = millis();
  }//end of encoder delay if statement

//Everything to do with actuating the motors

  //Every enc_delay ms, sample encoder data and move motors when needed
  if (millis() - motor_t >= motor_delay) {
    
    if (equalsStr(mode,"M")) {
      for (int i = TW ; i < LAST ; i++) {
        if (motor[i].desiredPos < 0.0 and not motor[i].direction) {
          motor[i].direction = -1;
          moveMotors(i, -1);
        }
        else if (motor[i].desiredPos > 0.0 and not motor[i].direction) {
          motor[i].direction = 1;
          moveMotors(i, 1);
        }
        else if (floatsEqual(motor[i].desiredPos, 0.0, 2) and motor[i].direction) {
          motor[i].direction = 0;
          moveMotors(i, 0);
        }
      }
      
    } else {//IK mode

      //Move first 4 motors that have encoder data
      //Move tower up to 1 degree around the goal
      motorHomeToCount(TW, 1.00);
      //Move LA1 & 2 up to 0.5 degrees around the goal
      motorHomeToCount(L1, 0.75);
      motorHomeToCount(L2, 0.75);
      //Move wrist up to 0.5 degrees around the goal
      motorHomeToCount(WP, 0.75);
      //Move wrist up to 0.5 degrees around the goal
      motorHomeToCount(WR, 0.75);
      
      //Move last 2 remaining motors by speed
      for (int i = EE ; i < LAST ; i++) {
        //move towards negative direction
        if (motor[i].desiredPos < 0.0 and not motor[i].direction) {
          motor[i].direction = -1;
          moveMotors(i, -1);
        }
        //move towards positive direction
        else if (motor[i].desiredPos > 0.0 and not motor[i].direction) {
          motor[i].direction = 1;
          moveMotors(i, 1);
        }
        //stop if stop cmd is received
        else if (floatsEqual(motor[i].desiredPos, 0.0, 2) and motor[i].direction) {
          motor[i].direction = 0;
          moveMotors(i, 0);
        }
      }
    }//end of IK mode
    
    //update timer until enc_delay is over
    motor_t = millis();
  }//end of encoder delay if statement

  //Motor is allowed to run whenever it's in one of the cases
  //- mode == "M" (in manual mode) and desired speed is zero (floatsEqual(desiredStates[0], 0.0)
  if (motor[TW].direction)
    tower.run();

  //LAs handled by moveMotor
  
  //Similar to tower, just with extra limit switch logic
  if (motor[WP].direction)
    //Can move the wrist (differential) if:
    //- LS3 is not clicked and pitching down
    //- LS4 is not clicked and pitching up
    if ((LS3.getState() and motor[WP].direction == -1) | (LS4.getState() and motor[WP].direction == 1)) {
      wristPitch.run();
    }
    
  if (motor[WR].direction)
    wristRoll.run();
  
  //similar to tower and similar limit switch logic to pitch
  if (motor[EE].direction)
    //EE only allowed to close if LS1 is not pressed
    //EE only allowed to open if LS2 is not pressed
    if ((LS1.getState() and motor[EE].direction == -1) | (LS2.getState() and motor[EE].direction == 1)) 
      endEffector.run();
  
} //end of loop()

//Uses encoder data to home the motor to a position
void motorHomeToCount(int i, float difference) {

  //Is current position equal to desired up to n decimal places
  if (not floatsEqual(motor[i].currentPos, motor[i].desiredPos, difference)) {

    //Current position lower than desired, move positive direction (dir = 1)
    //Want to run this once (blocking) so check if we are not already going (dir == 1)
    if (motor[i].currentPos < motor[i].desiredPos and motor[i].direction != 1) {
      //distanceDelta[i] = abs(motor[i].desired-motor[i].direction);
      motor[i].direction = 1;
      moveMotors(i, 1);//starting speed (speeds < 150 result in no extension)
      //dirChangeMillis[i] = millis();
    }

    //Current position higher than desired, move towards negative direction (dir = 1)
    //Want to run this once (blocking) so check if we are not already going (dir == 1)
    else if (motor[i].currentPos > motor[i].desiredPos and motor[i].direction != -1) {
      //distanceDelta[i] = abs(motor[i].desired-motor[i].direction);
      motor[i].direction = 1;
      moveMotors(i, -1);
      //dirChangeMillis[i] = millis();
    }

    //Here whenever the motors are already moving towards a direction
    //So all this does is smoothly change the speed (PID)
    else {
      //moveMotors(i, motor[i].direction);
    }

  //Current position is relatively close to desired
  //Want to run this once (blocking) so check if we are not already stopped (dir == 0)
  } else if (motor[i].direction != 0) {
    //dirChangeMillis[i] = millis();
    motor[i].direction = 0;
    moveMotors(i, 0);//stops motor
  }

}//end of motorHomeToCount

//Basic logic for controlling motors
//Should not be called often since its blocking
void moveMotors(int i, int dir) {

  motor[i].speed = calculateNextSpeed(i);
  motor[i].direction = dir;

  //Tower motor
  if (i == TW) {
    //Moves to whichever direction towards a step goal
    if (dir != 0) {
      tower.setMaxSpeed(motor[i].speed);
      tower.move(-motor[i].sign*dir*motor[i].MAX_RANGE);
    }
    //stops stepper
    else {
      tower.stop();
      tower.runToPosition();
    }
  }
  //LA1
  else if (i == L1) {
    //extend (dir == 1) or retract (dir == -1)
    if (dir != 0)
      LA1.setTarget(2048+dir*motor[i].sign*motor[i].speed);
    //stop LA motor
    else 
      LA1.stopMotor();
  }
  //LA2 
  else if (i == L2) {
    if (dir != 0) 
      LA2.setTarget(2048+dir*motor[i].sign*motor[i].speed);
    else 
      LA2.stopMotor();
  }
  //Wrist pitch
  else if (i == WP) {
    if (dir != 0) {
      wristPitch.setMaxSpeed(motor[i].speed);
      wristPitch.move(-motor[i].sign*dir*motor[i].MAX_RANGE);
    }
    else {
      wristPitch.stop();
      wristPitch.runToPosition();
    }
  }
  //Wrist roll
  else if (i == WR) {
    if (dir != 0) {
      wristRoll.setMaxSpeed(motor[i].speed);
      wristRoll.move(motor[i].sign*dir*motor[i].MAX_RANGE);
    }
    else {
      wristRoll.stop();
      wristRoll.runToPosition();
    }
  }
  //End effector 
  else {
    if (dir != 0) {
      endEffector.setMaxSpeed(motor[i].speed);
      endEffector.move(motor[i].sign*dir*motor[i].MAX_RANGE);
    }
    else {
      endEffector.stop();
      endEffector.runToPosition();
    }
  }
} //end of moveMotors()

void stopAll() {
  for (int i = TW ; i < LAST ; i++)
    moveMotors(i, 0);
}

//Calculates what the next speed should be depending on time since change of direction & proximity
//Curve used: https://www.desmos.com/calculator/lcbo7ici8g
int calculateNextSpeed(int i) {

  //Temporary function that returns a speed depending on the motor
  //For use with IK when not PID'ing (constant speed)
  int nextSpeed = 0;
  if (equalsStr(mode,"M")) {
    nextSpeed = abs((int)motor[i].desiredPos);
  } else {
    switch (i) {
      case TW:
        nextSpeed = 200;
        break;
      case L1:
        nextSpeed = 300;
        break;
      case L2:
        nextSpeed = 300;
        break;
      case WP:
        nextSpeed = 200;
        break;
      case WR:
        nextSpeed = 200;
        break;
      case EE:
        nextSpeed = 200;
        break;
      default:
        nextSpeed = 0;
        break;
    }
    
  }

return nextSpeed;

/*
  double r_steepness = 8;//acceleration
  double y_intercept = 0.015;
  double t_delta = (double)(millis()-startTime motor)/1000;//time since motor started moving
  double f_t = (2/3.1415926536)*atan(r_steepness*t_delta);

  //Counts remaining til desired count
  double countsR = (double)abs(motor[i].desired-motor[i].current);
  double k_adjust = 1.0322580645156 - 1/((countsR/20)+1);
  double s_final = (speedMax-s_base)*k_adjust*f_t + speedMin;

  return (int) s_final;*/
}//end of calculateNextSpeed

//Reboots the motor driver
void rebootDriver(int i) {
  digitalWrite(motor[i].BOOT_PIN, LOW);
  delay(1); //takes ~7.5 microseconds so 1 ms = 1000 microseconds should be fine
  digitalWrite(motor[i].BOOT_PIN, HIGH);
}
