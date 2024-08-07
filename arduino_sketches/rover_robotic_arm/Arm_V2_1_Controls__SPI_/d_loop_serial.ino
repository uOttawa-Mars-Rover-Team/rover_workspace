
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
    if (verbose) {
      Serial.print("\nNew command received: ");
      Serial.println(input);
    }

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
      for (int i = TW ; i < LAST ; i++) {
        tmp = strtok(NULL, ";");
        motor[i].desiredPos = atof(tmp);
      }
      if (verbose) {
        Serial.print("Desired set to: ");
        for (int i = TW ; i < LAST ; i++) {
          Serial.print(motor[i].desiredPos);
          Serial.print(";");
        }
        Serial.println("!");
      }
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
    }
    
    //Toggle related stuff (steppers, laser and emergency stop)
    else if (equalsStr(tmp, "stepper1")) {
      if (digitalRead(motor[TW].BOOT_PIN))
        digitalWrite(motor[TW].BOOT_PIN, LOW);
      else
        digitalWrite(motor[TW].BOOT_PIN, HIGH);

    } else if (equalsStr(tmp, "stepper2")) {
      if (digitalRead(motor[WP].BOOT_PIN))
        digitalWrite(motor[WP].BOOT_PIN, LOW);
      else
        digitalWrite(motor[WP].BOOT_PIN, HIGH);
      
    } else if (equalsStr(tmp, "stepper3")) {
      if (digitalRead(motor[WR].BOOT_PIN))
        digitalWrite(motor[WR].BOOT_PIN, LOW);
      else
        digitalWrite(motor[WR].BOOT_PIN, HIGH);
      
    } else if (equalsStr(tmp, "stepper4")) {
      if (digitalRead(motor[EE].BOOT_PIN))
        digitalWrite(motor[EE].BOOT_PIN, LOW);
      else
        digitalWrite(motor[EE].BOOT_PIN, HIGH);

    } else if (equalsStr(tmp, "laser")) {
      if (digitalRead(LASER_PIN))
        digitalWrite(LASER_PIN, LOW);
      else
        digitalWrite(LASER_PIN, HIGH);

    } else if (equalsStr(tmp, "stop")) {
      emergency_stop_en = not emergency_stop_en;

    }
    
    //LED related stuff
    else if (equalsStr(tmp, "test_laser")) {
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
    if (not graph) {

      Serial.println();
      Serial.print("Tower_Pose:");
      Serial.println(motor[TW].currentPos); //apply conversion using wrist mtr 1:50 and belt 1:10 => div by 500
      Serial.print(",");
      Serial.print("Tower_Ideal:");
      Serial.println(motor[TW].desiredPos);
      Serial.print("!");
    }

    //Publishing/printing feedback below

    


    //////testing: delete this block and replace with one below////////

    motor[TW].currentPos = (360*float(motor[TW].enc_count)/4096 + float(motor[TW].enc_turns)*360)/50;
    motor[TW].currentPos *= motor[TW].sign;
    /*Serial.print("tower current ----------------");
    Serial.print("!");
    Serial.print(motor[TW].currentPos);
    Serial.println("!");*/

    Serial.println();
    Serial.print("f;");
    Serial.print(motor[TW].currentPos);
    Serial.print(";");
    for (int i = L1 ; i < LAST ; i++) {
      Serial.print(motor[i].desiredPos);
      Serial.print(";");
    }
    Serial.print("!");
    //////testing: delete this block and replace with one below////////

    /*Serial.println();
    Serial.print("f;");
    for (int i = TW ; i < WR ; i++) {
      motor[i].currentPos = 360*float(motor[i].enc_count)/4096 + float(motor[i].enc_turns)*360;
      motor[i].currentPos *= motor[i].sign;
      Serial.print(motor[i].currentPos);
      Serial.print(";");
    }
    motor[WR].currentPos = wristRoll.currentPosition();
    Serial.print(motor[WR].currentPos*0.036);
    Serial.print(";0.00;");
    Serial.print("!");*/
    /*
    //Publishing/printing velocities
    Serial.println();
    Serial.print("v;");
    for (int i = TW ; i < LAST ; i++) {
      Serial.print(motor[i].velocity);
      Serial.print(";");
    }
    Serial.print("!");
    */

    /*debugging, uncomment later
    //Publishing/printing desired pos below
    Serial.println();
    Serial.print("d;");
    for (int i = TW ; i < LAST ; i++) {
      Serial.print(motor[i].desiredPos);
      Serial.print(";");
    }
    Serial.print("!");
    */

    //Publishing gpio feedback
    Serial.println();
    Serial.print("g;");
    Serial.print(digitalRead(motor[TW].BOOT_PIN));
    Serial.print(";");
    Serial.print(digitalRead(motor[WP].BOOT_PIN));
    Serial.print(";");
    Serial.print(digitalRead(motor[WR].BOOT_PIN));
    Serial.print(";");
    Serial.print(digitalRead(motor[EE].BOOT_PIN));
    Serial.print(";");
    Serial.print(digitalRead(LASER_PIN));
    Serial.print(";");
    Serial.print(emergency_stop_en);
    Serial.print(";!");

    //update timer until enc_delay is over
    dashb_t = millis();
  }//end of dashboard delay if statement
