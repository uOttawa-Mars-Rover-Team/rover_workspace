
//Everything to do with actuating the motors


  //Every enc_delay ms, sample encoder data and move motors when needed
  if (millis() - encoder_t >= enc_delay) {

    if (equalsStr(mode,"M")) {
      for (int i = TW ; i < LAST ; i++) {
        if (motor[i].desired < 0.0 and not motor[i].direction) {
          motor[i].direction = -1;
          moveMotors(i, -1);
        }
        else if (motor[i].desired > 0.0 and not motor[i].direction) {
          motor[i].direction = 1;
          moveMotors(i, 1);
        }
        else if (floatsEqual(motor[i].desired, 0.0, 2) and motor[i].direction) {
          motor[i].direction = 0;
          moveMotors(i, 0);
        }
      }
      
    } else {//IK mode

      //Move first 4 motors that have encoder data
      for (int i = TW ; i <= WP ; i++) 
        motorHomeToCount(i);
      
      //Move last 2 remaining motors by speed
      for (int i = WR ; i <= EE ; i++) {
        if (motor[i].desired < 0.0 and not motor[i].direction) {
          motor[i].direction = -1;
          moveMotors(i, -1);
        }
        else if (motor[i].desired > 0.0 and not motor[i].direction) {
          motor[i].direction = 1;
          moveMotors(i, 1);
        }
        else if (floatsEqual(motor[i].desired, 0.0, 2) and motor[i].direction) {
          motor[i].direction = 0;
          moveMotors(i, 0);
        }
      }
    }//end of IK mode
    
    for (int i = TW ; i < LAST ; i++) {
      tmpEncPos = getPositionSPI(motor[i].ENC, RES12);
      if (tmpEncPos != 0xFFFF) {
        if (i == TW) {
          if (abs((int)tmpEncPos - (int)tmpEncPosPrev) > 1) {
            Serial.print(((int)tmpEncPos - (int)tmpEncPosPrev));
            if ((int)tmpEncPos < (int)tmpEncPosPrev and motor[i].direction == 1) {
              section++;
              Serial.print("Section switched to: ");
              Serial.println(section);
              Serial.print("!");
            } else if ((int)tmpEncPos > (int)tmpEncPosPrev and motor[i].direction == -1) {
              section--;
              Serial.print("Section switched to: ");
              Serial.println(section);
              Serial.print("!");
            }
          }
          motor[i].current = getResultingRadian(section, (float)tmpEncPos*0.00153398078789);
        } else {
          motor[i].current = (float)tmpEncPos*0.00153398078789;
        }
      }
    }
      
    //update timer until enc_delay is over
    encoder_t = millis();
  }//end of encoder delay if statement

  //Motor is allowed to run whenever it's in one of the cases
  //- mode == "M" (in manual mode) and desired speed is zero (floatsEqual(desiredStates[0], 0.0)
  if (motor[0].direction)
    tower.run();

  //LAs handled by moveMotor
  
  //Similar to tower, just with extra limit switch logic
  if (motor[3].direction or motor[4].direction)
    //Can move the wrist (differential) if:
    //- LS3 is not clicked and pitching down
    //- LS4 is not clicked and pitching up
    if ((LS3.getState() and motor[WP].direction == -1) | (LS4.getState() and motor[WP].direction == 1)) {
      wristEE.run();
    }
  
  //similar to tower and similar limit switch logic to pitch
  if (motor[5].direction)
    //EE only allowed to close if LS1 is not pressed
    //EE only allowed to open if LS2 is not pressed
    if ((LS1.getState() and motor[EE].direction == -1) | (LS2.getState() and motor[EE].direction == 1)) 
      endEffector.run();
  
} //end of loop()

//Uses encoder data to home the motor to a position
void motorHomeToCount(int i) {

  //Is current position equal to desired up to n decimal places
  if (not floatsEqual(motor[i].current, motor[i].desired, 2)) {

    //Current position lower than desired, move positive direction (dir = 1)
    //Want to run this once (blocking) so check if we are not already going (dir == 1)
    if (motor[i].current < motor[i].desired and motor[i].direction != 1) {
      //distanceDelta[i] = abs(motor[i].desired-motor[i].direction);
      motor[i].direction = 1;
      moveMotors(i, 1);//starting speed (speeds < 150 result in no extension)
      //dirChangeMillis[i] = millis();
    }

    //Current position higher than desired, move towards negative direction (dir = 1)
    //Want to run this once (blocking) so check if we are not already going (dir == 1)
    else if (motor[i].current > motor[i].desired and motor[i].direction != -1) {
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
      tower.moveTo(dir*motor[i].MAX_RANGE);
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
      LA1.setTarget(2048+dir*motor[i].speed);
    //stop LA motor
    else 
      LA1.stopMotor();
  }
  //LA2 
  else if (i == L2) {
    if (dir != 0) 
      LA2.setTarget(2048+dir*motor[i].speed);
    else 
      LA2.stopMotor();
  }
  //Wrist pitch
  else if (i == WP) {
    if (dir != 0) {
      wristRight.setMaxSpeed(motor[i].speed);
      wristLeft.setMaxSpeed(motor[i].speed);

      long tmpPositions[2] = {-dir*motor[i].MAX_RANGE, dir*motor[i].MAX_RANGE};
      wristEE.moveTo(tmpPositions);
    }
  } 
  //Wrist roll
  else if (i == WR) {
    if (dir != 0) {
      wristRight.setMaxSpeed(motor[i].speed);
      wristLeft.setMaxSpeed(motor[i].speed);

      //we set the target of the motors
      long tmpPositions[2] = {-dir*motor[i].MAX_RANGE, -dir*motor[i].MAX_RANGE};
      wristEE.moveTo(tmpPositions);
    }
  }
  //End effector 
  else {
    if (dir != 0) {
      endEffector.setMaxSpeed(motor[i].speed);
      endEffector.moveTo(dir*motor[i].MAX_RANGE);
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
  if (equalsStr(mode,"M")) {
    return abs((int)motor[i].desired);
  } else {
    int speedMin = 0;
    int speedMax = 0;
    if (i == L1 or i == L2) {
      speedMin = 200;
      speedMax = 600;
      return 600;
    } else {
      speedMin = 0;
      speedMax = 500;
      return 150;
    }
  }

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

float getResultingRadian(int section, float radian) {
  return section*0.628318530718 + radian*0.1;
}
