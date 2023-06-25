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
 
int EN_A = 2; // Arduino PWM output pin 4; connect to Adafruit 2052 EN A pin
int IN01 = 47; // Arduino PWM output pin 5; connect to Adafruit 2052 IN 1 pin
int IN02 = 48; // Arduino PWM outpin pin 6; connect to Adafruit 2052 IN 2 pin
 
void setup()
{
  pinMode(EN_A, OUTPUT);
  pinMode(IN01, OUTPUT);
  pinMode(IN02, OUTPUT);
}
 
void loop() {
  //extend LA
  digitalWrite(IN02, LOW);
  digitalWrite(IN01, HIGH);
  analogWrite(EN_A, 100);
  
  
  delay(2000);

  //stop actuator
  digitalWrite(IN01, LOW);
  digitalWrite(IN02, LOW);
  //analogWrite(EN_A, 0);

  delay(2000);
}
