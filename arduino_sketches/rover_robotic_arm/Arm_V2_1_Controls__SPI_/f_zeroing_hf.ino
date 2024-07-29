
//Everything to do with zeroing the motors

//Zero End Effector to middle position 
//***CHECK SIGNS IN MOVETO FUNCTIONS***
void zeroEndEffector() {
  int state;
 
  Serial.print("\nZeroing EE!");//add ! delimiter for receiving node
  
  // set max speed and acceleration, we could alternatively set these values based on function inputs
  endEffector.setMaxSpeed(50.0);
  endEffector.setAcceleration(1000.0); //Default 1000
  //set target position for max range, this target accounts for the worst case scenario of the initial stepper position

  bool breakCondition = false;
  while (not breakCondition){
    LS1.loop();
    state = LS1.getState();
    endEffector.run();

    endEffector.moveTo(motor[EE].MAX_RANGE*2);

    endEffector.run();
  
    if(state == 0){
      Serial.print("zeroingDone;!");

      break;
    }
    //endEffector.run(); //moves motor towards target position

    //Exit when command equals stop
    if (Serial.available()) {
      
      //use memset to 'empty' input buffer; may not be necessary,
      //but ensures that input is in a well-defined state
      memset(input, 0, sizeof(input));

      //characters from the serial input are read into the input array
      //readBytesUntil returns the number of characters read to the size variable
      byte size = Serial.readBytesUntil('!', input, INPUT_SIZE);

      //Add the final 0 to end the C string
      input[size] = 0;

      tmp = strtok(input, ";");
      mode = tmp;

      if (equalsStr(mode, "stop")) {
        breakCondition = true;
      }
    }
  }
 
  endEffector.stop(); //stop motor
  endEffector.setCurrentPosition(motor[EE].MAX_RANGE);
  Serial.print("\nEE STOPPING!");//add ! delimiter for receiving node
  endEffector.move(-motor[EE].MAX_RANGE); //relative position, should move stepper to the middle
  // run the motor until the distance from the target position is 0.
  
  
  while (endEffector.distanceToGo() != 0){
    endEffector.run();
  }
  long numSteps = endEffector.currentPosition(); // returns our position relative to our initial point
  Serial.print("\nEE zeroing complete!");//add ! delimiter for receiving node
  stopAll();
}//end of zeroEndEffector

//Wrist zeroing function (to midpoint)
//CHECK SIGNS
//INCOMPLETE (uses multistepper, adapt to current)
void zeroWristPitch(){
  stopAll();
  // condition for while loop
  int homeFlag = 0;
  // positions
  long positions[2] = {motor[WP].MAX_RANGE, -motor[WP].MAX_RANGE};
  // set speeds and target positions
  wristPitch.setMaxSpeed(500.0);

  while (homeFlag == 0){
    //wristEE.run(); // move stepper to target position
    if (LS2.getState() == LOW){ // if limit switch is pressed
      homeFlag = 1; // break out of while loop, so motors are not being run anymore
    }
  }
  // move them back to the middle
}//end of zeroWristPitch
