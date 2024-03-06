
//Start of loop plus limit switch logic

void loop() {
  //we do some of the needed setup to get the limitSwitches working
  LS1.loop(); //MUST call the loop() function first
  LS2.loop();
  LS3.loop();
  LS4.loop();

  //When LS's are pressed the states are toggled to allow/disallow movement to a direction
  if (EEStopClose == LS1.getState()) {
    if (LS1.getState()) {
      Serial.print("\nLS1 unpressed; EE may close!");
    } else {
      Serial.print("\nLS1 pressed; no EE closing!");
    }
    EEStopClose = !LS1.getState();
  }
  if (EEStopOpen == LS2.getState()) {
    if (LS2.getState()) {
      Serial.print("\nLS2 unpressed; EE may open!");
    } else {
      Serial.print("\nLS2 pressed; no EE opening!");
    }
    EEStopOpen = !LS2.getState();
  }
  if (wristStopUp == LS3.getState()) {
    if (LS3.getState()) {
      Serial.print("\nLS3 unpressed; wrist may pitch up!");
    } else {
      motor[WP].direction = 0;
      Serial.print("\nLS3 pressed; no pitching up!");
    }
    wristStopUp = !LS3.getState();
  }
  if (wristStopDown == LS4.getState()) {
    if (LS4.getState()) {
      Serial.print("\nLS4 unpressed; wrist may pitch down!");
    } else {
      motor[WP].direction = 0;
      Serial.print("\nLS4 pressed; no pitching down!");
    }
    wristStopDown = !LS4.getState();
  }
