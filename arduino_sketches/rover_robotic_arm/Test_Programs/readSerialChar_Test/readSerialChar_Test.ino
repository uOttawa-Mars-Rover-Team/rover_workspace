/*
 * Small test program taken for the internet to test taking one char as an input and printing it back in the serial monitor.
 * if you send more than one character, each character is read one at a time and printed one at a time.
 * Website: https://www.norwegiancreations.com/2017/12/arduino-tutorial-serial-inputs/
 *
 */

char input;
 
void setup() {
    Serial.begin(9600); 
    delay(2000);  
 
    Serial.println("Type something!");
}
 
void loop() {
    if(Serial.available()){
        input = Serial.read();
        Serial.print("You typed: " );
        Serial.println(input);
    }
}
