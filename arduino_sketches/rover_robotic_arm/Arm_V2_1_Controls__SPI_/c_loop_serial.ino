
//Everything to do with serial comms is here (read and writing)
void loop(){
  //We check if a command has been given and then interpret it

 
  if (Serial.available()) {

    // read serial line character by character on each loop (i.e. one character per loop)
    char head = Serial.read();
    // Serial.print("Head: ");
    // Serial.println(head);
    if(head == '!'){
      input[size] = '\0';
      commandFlag = true;
      //Serial.print("Recieved input: ");
      //Serial.println(input);
      // Serial.print("Recieved Size: ");
      // Serial.println(size);
    } else if (head == '\n'){
      // do nothing, make sure this not added to the string
    } else if(size < INPUT_SIZE - 1 ){
      //Serial.println("Trigger ye?");
      input[size++] = (char)head;
    }
    else{
      //size = 0;
    }
    // byte size = Serial.readBytesUntil('!', input, INPUT_SIZE);

    //Typical command example:
    //Manual: "S;1024;-1024;0;0;0;0;!"
    //IK: "S;TW Position;SL Position;EL Position;RL Velocity;EE Velocity;" --> Degrees precise to two decimal points

    if (commandFlag){
      
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
          motor[i].speed = 0;
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

      } else if (equalsStr(tmp, "stepper_safety")) {
        stepper_safety_en = not stepper_safety_en;

      } else if (equalsStr(tmp, "laser")) {
        if (digitalRead(LASER_PIN))
          digitalWrite(LASER_PIN, LOW);
        else
          digitalWrite(LASER_PIN, HIGH);

      } else if (equalsStr(tmp, "stop")) {
        emergency_stop_en = not emergency_stop_en;

      } else if (equalsStr(tmp, "v")){ 
        if (verbose)  
          verbose = false;
        else
          verbose = true;
      }else if (equalsStr(tmp, "roll")) {
        motor[WR].desiredPos = 0.4;

      } else if (equalsStr(tmp, "unroll")) {
        motor[WR].desiredPos = -0.4;

      } else if (equalsStr(tmp, "roll_stop")) {
        motor[WR].desiredPos = 0;

      } else if (equalsStr(tmp, "ee_open")) {
        motor[EE].desiredPos = -0.4;

      } else if (equalsStr(tmp, "ee_close")) {
        motor[EE].desiredPos = 0.4;

      } else if (equalsStr(tmp, "ee_stop")) {
        motor[EE].desiredPos = 0;

      } else if (equalsStr(tmp, "wrist_angle_abs")) {
        wrist_angle_abs = not wrist_angle_abs;

      }
      
      //LED related stuff
      else if (equalsStr(tmp, "test_laser")) {
        digitalWrite(LASER_PIN, LOW);
        delay(100);
        digitalWrite(LASER_PIN, HIGH);
        Serial.println("Turning laser on and off!");
      } else {
        Serial.println("Invalid command received!");
      }

      commandFlag = false;
      size = 0;
    }
  
  }//end of serial available

  //Every dashb_delay ms, publish stuff
  if (millis() - dashb_t >= dashb_delay and verbose) {
    //Publishing/printing feedback below
    Serial.println();
    Serial.print("f;");
    for (int i = TW ; i < WR ; i++) {
      Serial.print(motor[i].currentPos);
      Serial.print(";");
    }
    Serial.print("!");

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
