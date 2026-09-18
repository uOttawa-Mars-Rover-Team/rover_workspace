/*
 * This program is a more concrete example of how you could use the serial input function.
 * in this program we take in a command, and based of what it is we execute different actions.
 * In our case, a similar approch is going to be used to interpret the inputs
 * either comming from the joystick or the attached computer (when testing)
 * 
 * example from this website: https://www.norwegiancreations.com/2017/12/arduino-tutorial-serial-inputs/
 * 
 * Author of this version of the program: Olivier Caron (20-jan-2022)
 */

String command;
 
void setup() {
    Serial.begin(9600); 
}
 
void loop() {
    if(Serial.available()){
        command = Serial.readStringUntil('\n');
         
        if(command.equals("init")){
          //do something
            Serial.println("The init command was entered");
        }
        else if(command.equals("send")){
            //do something
            Serial.println("The send command was entered");
        }
        else if(command.equals("data")){
            //do something
            Serial.println("The data command was entered");
        }
        else if(command.equals("reboot")){
            //do something
            Serial.println("The reboot command was entered");
        }
        else{
            Serial.println("Invalid command");
        }
    }
}
