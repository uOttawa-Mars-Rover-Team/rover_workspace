/* Firgelli Automations
 * Limited or no support: we do not have the resources for Arduino code support
 * 
 * Program demos how a motor driver controls direction & speed of a linear actuator 
 */
 
byte Speed = 0; // Intialize Varaible for the speed of the motor (0-255);
int RPWM = 11;  //connect Arduino pin 10 to IBT-2 pin RPWM
int LPWM = 12;  //connect Arduino pin 11 to IBT-2 pin LPWM

void setup() {
pinMode(11, OUTPUT); // Configure pin 10 as an Output
pinMode(12, OUTPUT); // Configure pin 11 as an Output

}

void loop() {
  // Extend Actuator at Full Speed
  Speed = 255;
  analogWrite(RPWM, 0);
  analogWrite(LPWM, Speed);
  
  delay(2000); // 2 Seconds
  
  // Stop Actuator
  analogWrite(RPWM, 0);
  analogWrite(LPWM, 0);

  delay(2000); // 2 Seconds

  // Retract Actuator at Half Speed
  Speed = 127;
  analogWrite(RPWM, Speed);
  analogWrite(LPWM, 0);
  
  delay(2000); // 2 Seconds
  
  // Stop Actuator
  analogWrite(RPWM, 0);
  analogWrite(LPWM, 0);

  delay(2000); // 2 Seconds

}
