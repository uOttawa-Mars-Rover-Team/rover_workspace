void setup() {
  // Start the serial communication at 115200 baud rate
  Serial.begin(115200);
}

void loop() {
  while(Serial.available() == 0);
  Serial.write(Serial.read());
}
