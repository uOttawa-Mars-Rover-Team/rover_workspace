/*
IBT-2 Motor Control Board driven by Arduino.
 
Speed and direction controlled by a potentiometer attached to analog input 0.
One side pin of the potentiometer (either one) to ground; the other side pin to +5V
 
Connection to the IBT-2 board:
IBT-2 pin 1 (RPWM) to Arduino pin 5(PWM)
IBT-2 pin 2 (LPWM) to Arduino pin 6(PWM)
IBT-2 pins 3 (R_EN), 4 (L_EN), 7 (VCC) to Arduino 5V pin
IBT-2 pin 8 (GND) to Arduino GND
IBT-2 pins 5 (R_IS) and 6 (L_IS) not connected
*/
 
int RPWM_Output = 3; // Arduino PWM output pin 5; connect to IBT-2 pin 1 (RPWM) Forward
int LPWM_Output = 2; // Arduino PWM output pin 6; connect to IBT-2 pin 2 (LPWM) Backward;
int R_EN = 30;
int L_EN = 33;
 
void setup()
{
  pinMode(RPWM_Output, OUTPUT);
  pinMode(LPWM_Output, OUTPUT);
  pinMode(R_EN, OUTPUT);
  pinMode(L_EN, OUTPUT);

  digitalWrite(R_EN, HIGH);
  digitalWrite(L_EN, HIGH);
}
 
void loop() {

  //forward accelerate to max speed and then decelerate

  
  analogWrite(RPWM_Output, 100);
  analogWrite(LPWM_Output, 0);
  //analogWrite(LPWM_Output, 100);
  delay(2000);

  // Stop Actuator
  analogWrite(RPWM_Output, 0);
  analogWrite(LPWM_Output, 0);
  
 delay(2000);
 
  // //backwards accelerate to max speed and then decelerate
  analogWrite(LPWM_Output, 100);
  analogWrite(RPWM_Output, 0);
  delay(2000);

  // Stop Actuator
  analogWrite(RPWM_Output, 0);
  analogWrite(LPWM_Output, 0);

  delay(2000);
  
}
