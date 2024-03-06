
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
    //Manual: "M;1000;-1000;0;0;0;0;!"
    //IK: "I;10000;200;200;1000;-1000;-1000;!"
    Serial.print("\nNew command received: ");
    Serial.println(input);

    tmp = strtok(input, ";");

    if (equalsStr(tmp, "I") or equalsStr(tmp, "M")) {

      //Extract variables
      mode = tmp;
      Serial.print("Mode: ");
      Serial.println(mode);
      Serial.print("Desired States: ");
      for (int i = TW ; i < LAST ; i++) {
        tmp = strtok(NULL, ";");
        motor[i].desired = atof(tmp);
        Serial.print(motor[i].desired);
        Serial.print(";");
      }
    } else if (equalsStr(mode, "reset")) {
      for (int i = TW ; i < LAST ; i++) {
        motor[i].direction = 0.0;
        motor[i].current = 0.0;
        motor[i].desired = 0.0;
      }
    Serial.print("!");
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
