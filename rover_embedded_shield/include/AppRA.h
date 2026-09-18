#ifndef APP_RA_H
#define APP_RA_H

void appRA_setup();
void appRA_loop();

// Called by CommSerial — these are the two entry points into AppRA
void appRA_handleRA(char* payload);
void appRA_dispatchAxisCommand(char* msg);

#endif
