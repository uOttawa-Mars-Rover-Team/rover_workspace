/*
 * This small program is again an example of how one could input a whole line.
 * This is done using the readStringUntil() function which reads the data sent in the Serial buffer until the specified character arrives.
 * in this case the '\n' character
 */

String my_name;
 
void setup() {
    Serial.begin(9600);
 
    delay(2000);
 
    Serial.println("What is your name?");
}
 
 
 
void loop() {
    if(Serial.available()){
        my_name = Serial.readStringUntil('\n');
 
        Serial.println("Nice to meet you, " + my_name + "!");
    }
}
