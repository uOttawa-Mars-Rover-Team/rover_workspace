


int LA1_RPWM_Output = 10; // Arduino PWM output pin 5; connect to IBT-2 pin 1 (RPWM) Forward
int LA1_LPWM_Output = 11; // Arduino PWM output pin 6; connect to IBT-2 pin 2 (LPWM) Backward;
int LA2_RPWM_Output = 12;
int LA2_LPWM_Output = 13;


void setup() {
  // put your setup code here, to run once:
  //we also do some linear actuator setup stuff
    //maybe enable the LA and set the basic speed?
    //we setup the pin modes for the LA
    pinMode(LA1_RPWM_Output, OUTPUT);
    pinMode(LA1_LPWM_Output, OUTPUT);
    pinMode(LA2_RPWM_Output, OUTPUT);
    pinMode(LA2_LPWM_Output, OUTPUT);

}

void loop() {
  // put your main code here, to run repeatedly:
  //LA 1
  //forward

  //figure out if there's a way to make this code a little lighter (ex: remove the enable pin stuff or just put it at the end)
  //digitalWrite(R_EN, HIGH);
  Serial.println("Moving LA out");
  analogWrite(LA1_LPWM_Output, 0);
  analogWrite(LA2_LPWM_Output, 0);
  //analogWrite(LA1_RPWM_Output, 100);
  
  //analogWrite(LA2_RPWM_Output, 100);

  delay(5000);
  
  //digitalWrite(R_EN, LOW);
  analogWrite(LA1_RPWM_Output, 0);
  analogWrite(LA1_LPWM_Output, 0);
  analogWrite(LA2_RPWM_Output, 0);
  analogWrite(LA2_LPWM_Output, 0);
  delay(1000);

  //backwards accelerate to max speed and then decelerate
  Serial.println("Moving LA inward");
  //digitalWrite(L_EN, HIGH);
  analogWrite(LA1_RPWM_Output, 0);
  analogWrite(LA1_LPWM_Output, 100);
  analogWrite(LA2_RPWM_Output, 0);
  //analogWrite(LA2_LPWM_Output, 100);
  delay(5000);
  
  //digitalWrite(L_EN, LOW);
  analogWrite(LA1_LPWM_Output, 0);
  analogWrite(LA1_RPWM_Output, 0);
  analogWrite(LA2_LPWM_Output, 0);
  analogWrite(LA2_RPWM_Output, 0);
  delay(1000);


}
