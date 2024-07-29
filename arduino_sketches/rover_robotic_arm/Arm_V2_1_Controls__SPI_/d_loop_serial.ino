
//Everything to do with serial comms is here (read and writing)

  //We check if a command has been given and then interpret it
  if (Serial.available()) {
    
    //use memset to 'empty' input buffer; may not be necessary,
    //but ensures that input is in a well-defined state
    memset(input, 0, sizeof(input));

    //characters from the serial input are read into the input array
    //readBytesUntil returns the number of characters read to the size variable
    byte size = Serial.readBytesUntil('!', input, INPUT_SIZE);

    //Add the final 0 to end the C string
    input[size] = 0;

    //Typical command example:
    //Manual: "M;1024;-1024;0;0;0;0;!"
    //IK: "I;1.57;2.0;3.0;0.5;-1024;-1024;!"
    Serial.print("\nNew command received: ");
    Serial.println(input);

    tmp = strtok(input, ";");

    if (equalsStr(tmp, "M")) {

      mode = "M";
      Serial.println("Mode: Manual!");
      for (int i = TW ; i < LAST ; i++) {
        tmp = strtok(NULL, ";");
        motor[i].desiredPos = 0;
      }
      Serial.println("Speeds = 0!");
    } else if (equalsStr(tmp, "I")) {

      mode = "I";
      Serial.println("Mode: IK!");
      for (int i = TW ; i <= WP ; i++) {
        tmp = strtok(NULL, ";");
        motor[i].desiredPos = motor[i].currentPos;
      }
      for (int i = WR ; i <= EE ; i++) {
        tmp = strtok(NULL, ";");
        motor[i].desiredPos = 0.0;
      }
      Serial.println("Desired states/speeds = current/0!");
    } else if (equalsStr(tmp, "S")) {

      //Extract variables
      Serial.print("Desired set to: ");
      for (int i = TW ; i < LAST ; i++) {
        tmp = strtok(NULL, ";");
        motor[i].desiredPos = atof(tmp);
        Serial.print(motor[i].desiredPos);
        Serial.print(";");
      }
      Serial.println("!");
    } else if (equalsStr(tmp, "set0")) {
      for (int i = TW ; i < LAST ; i++) {
        motor[i].direction = 0;
        motor[i].currentPos = 0.0;
        motor[i].desiredPos = 0.0;
        motor[i].enc_count = 0;
        motor[i].enc_turns = 0;
        setZeroSPI(motor[i].ENC_PIN);
      }
      Serial.println("Direction, current and desired states reset!");
    } else if (equalsStr(tmp, "dir0")) {
      for (int i = TW ; i < LAST ; i++) {
        motor[i].direction = 0.0;
      }
      Serial.println("Direction reset!");
    } else if (equalsStr(tmp, "set")) {
      for (int i = TW ; i < LAST ; i++) {
        tmp = strtok(NULL, ";");
        motor[i].currentPos = atof(tmp);
      }
      Serial.println("Current states changed!");
    } else if (equalsStr(tmp, "reboot_tw")) {
      rebootDriver(TW);
      Serial.println("Tower driver rebooted!");
      
    } else if (equalsStr(tmp, "reboot_wp")) {
      rebootDriver(WP);
      Serial.println("Wrist pitch driver rebooted!");
      
    } else if (equalsStr(tmp, "reboot_wr")) {
      rebootDriver(WR);
      Serial.println("Wrist roll driver rebooted!");
      
    } else if (equalsStr(tmp, "reboot_ee")) {
      rebootDriver(EE);
      Serial.println("End effector driver rebooted!");
      
    } else if (equalsStr(tmp, "test_laser")) {
      digitalWrite(LASER_PIN, LOW);
      delay(100);
      digitalWrite(LASER_PIN, HIGH);
      Serial.println("Turning laser on and off!");
    } else if (equalsStr(tmp, "white")) {
      writeLED(255,255,255);
      Serial.println("LED set to white!");
      
    } else if (equalsStr(tmp, "red")) {
      writeLED(255,0,0);
      Serial.println("LED set to red!");
      
    } else if (equalsStr(tmp, "green")) {
      writeLED(0,255,0);
      Serial.println("LED set to green!");
      
    } else if (equalsStr(tmp, "blue")) {
      writeLED(0,0,255);
      Serial.println("LED set to blue!");
      
    } else {
      Serial.println("Invalid command received!");
    }
  }//end of serial available

  //Every dashb_delay ms, publish stuff
  if (millis() - dashb_t >= dashb_delay) {

    //Publishing/printing feedback below
    Serial.print("f;");
    for (int i = TW ; i < LAST ; i++) { 
      motor[i].currentPos = 360*float(motor[i].enc_count)/4096 + float(motor[i].enc_turns)*360;
      Serial.print(motor[i].currentPos);
      Serial.print(";");
    }
    Serial.println("!");
    
    //Publishing/printing desired pos below
    Serial.print("d;");
    for (int i = TW ; i < LAST ; i++) {
      Serial.print(motor[i].desiredPos);
      Serial.print(";");
    }
    Serial.println("!");
    /*
    //Publishing/printing turns below
    Serial.print("t;");
    for (int i = TW ; i < LAST ; i++) {
      Serial.print(motor[i].enc_turns);
      Serial.print(";");
    }
    Serial.println("!");
    //Publishing/printing turns below
    Serial.print("e;");
    for (int i = TW ; i < LAST ; i++) {
      Serial.print(motor[i].enc_count);
      Serial.print(";");
    }
    Serial.println("!");
    */
    //update timer until enc_delay is over
    dashb_t = millis();
  }//end of dashboard delay if statement
