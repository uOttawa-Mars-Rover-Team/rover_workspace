
//Interrupt service routines (ISRs) for all motors

//ISR for LA1 encoder
void counter_LA1(){
  //Serial.print("LA1 ISR!");
  if (millis() - motor[L1].trig_delay >= 13.24){
    motor[L1].trig_delay = millis();
    motor[L1].current += motor[L1].direction;
  }
}//end of counter_LA1

//ISR for LA2 encoder
void counter_LA2(){
  //Serial.print("LA2 ISR!");
  if (millis() - motor[L2].trig_delay >= 13.24){
    motor[L2].trig_delay = millis();
    motor[L2].current += motor[L2].direction;
  }
}//end of counter_LA2

//Gets the debounce time for any speed the LAs are going at
int getDebounceTime(int speed){
  if (speed > 200)
    //function derived after eye-balling oscilloscope readings
    return 265921*pow((speed),-1.43577);
  else
    //for speeds <= 200, function shoots up
    return 60;
}//end of getDebounceTime

//ISR for tower encoder
void towerCounter() {
  if (digitalRead(motor[TW].ENC_B) == HIGH)
    motor[TW].currentCount += 1;
  else
    motor[TW].currentCount -= 1;
}//end of towerCounter

//ISR for pitch encoder
void pitchCounter() {
  //Count only when the pin is high and motor is not rolling (differential)
  if (not motor[WR].direction) {
    if (digitalRead(motor[WP].ENC_B) == HIGH)
      motor[WP].currentCount += 1;
    else
      motor[WP].currentCount -= 1;
  }
}//end of pitchCounter
