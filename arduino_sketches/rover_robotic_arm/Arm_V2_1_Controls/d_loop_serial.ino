
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
      Serial.print("Switched to mode: ");
      Serial.println(mode);
      for (int i = TW ; i < LAST ; i++) {
        tmp = strtok(NULL, ";");
        motor[i].desired = 0;
      }
      Serial.println("!");
    } else if (equalsStr(tmp, "I")) {

      mode = "I";
      Serial.print("Switched to mode: ");
      Serial.println(mode);
      for (int i = TW ; i <= WP ; i++) {
        tmp = strtok(NULL, ";");
        motor[i].desired = motor[i].current;
      }
      for (int i = WR ; i <= EE ; i++) {
        tmp = strtok(NULL, ";");
        motor[i].desired = 0.0;
      }
      Serial.println("!");
    } else if (equalsStr(tmp, "S")) {

      //Extract variables
      Serial.print("Desired States: ");
      for (int i = TW ; i < LAST ; i++) {
        tmp = strtok(NULL, ";");
        motor[i].desired = atof(tmp);
        Serial.print(motor[i].desired);
        Serial.print(";");
      }
      Serial.println("!");
    }  else if (equalsStr(tmp, "reset")) {
      for (int i = TW ; i < LAST ; i++) {
        motor[i].direction = 0.0;
        motor[i].current = 0.0;
        motor[i].desired = 0.0;
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
        motor[i].current = atof(tmp);
      }
      Serial.println("Current states changed!");
    } else {
      Serial.println("Invalid command received!");
    }
  }//end of serial available

  //Every dashb_delay ms, sample encoder data and allow 
  if (millis() - dashb_t >= dashb_delay) {

    //Publishing/printing below
    Serial.print("f;");
    for (int i = TW ; i < LAST ; i++) {
      Serial.print(motor[i].current);
      Serial.print(";");
    }
    Serial.println("!");
    //Publishing/printing below
    Serial.print("d;");
    for (int i = TW ; i < LAST ; i++) {
      Serial.print(motor[i].desired);
      Serial.print(";");
    }
    Serial.println("!");
    
    //update timer until enc_delay is over
    dashb_t = millis();
  }//end of dashboard delay if statement
