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
 
//int SENSOR_PIN = 0; // center pin of the potentiometer
 
int LA1_RPWM_Output = 10; // Arduino PWM output pin 5; connect to IBT-2 pin 1 (RPWM) Forward
int LA1_LPWM_Output = 11; // Arduino PWM output pin 6; connect to IBT-2 pin 2 (LPWM) Backward;
int LA2_RPWM_Output = 12; // Arduino PWM output pin 5; connect to IBT-2 pin 1 (RPWM) Forward
int LA2_LPWM_Output = 13; // Arduino PWM output pin 6; connect to IBT-2 pin 2 (LPWM) Backward;
 
void setup()
{
  pinMode(LA1_RPWM_Output, OUTPUT);
  pinMode(LA1_LPWM_Output, OUTPUT);
  pinMode(LA2_RPWM_Output, OUTPUT);
  pinMode(LA2_LPWM_Output, OUTPUT);
  //pinMode(R_EN, OUTPUT);
  //pinMode(L_EN, OUTPUT);
}
 
void loop() {

  //forward accelerate to max speed and then decelerate
  //digitalWrite(R_EN, HIGH);
  for (int i = 0; i <= 255; i++) {
    analogWrite(LA1_RPWM_Output, i);
    analogWrite(LA2_RPWM_Output, i);
    delay(30);
  }
  for (int i = 255; i >= 0; i--) {
    analogWrite(LA1_RPWM_Output, i);
    analogWrite(LA2_RPWM_Output, i);
    delay(30);
  }

  //backwards accelerate to max speed and then decelerate
  //digitalWrite(L_EN, HIGH);
  for (int i = 0; i <= 255; i++) {
    analogWrite(LA1_LPWM_Output, i);
    analogWrite(LA2_LPWM_Output, i);
    delay(30);
  }
  for (int i = 255; i >= 0; i--) {
    analogWrite(LA1_LPWM_Output, i);
    analogWrite(LA2_LPWM_Output, i);
    delay(30);
  }
  

  
  
}
