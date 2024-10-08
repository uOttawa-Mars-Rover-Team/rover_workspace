void setup() {
  // Start the serial communication at 115200 baud rate
  Serial.begin(500000);
}

void loop() {
  // Echo the position command back as feedback to simulate the arm moving to the setpoint
  while(Serial.available() == 0);
  char input = Serial.read();
  
  if (input == 'S'){
    input = 'f';
  }
  
  Serial.write(input);
}
