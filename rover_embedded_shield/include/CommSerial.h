#pragma once
#include <Arduino.h>

class CommSerial {
public:
    CommSerial(HardwareSerial& rosSerial, HardwareSerial& boardSerial, uint32_t rosBaud, uint32_t boardBaud);

    void init();
    void update();          // call every loop — accumulates chars, sets flag
    bool messageReady();    // true when a full message is in buffer
    const char* getMessage(); // get the completed message
    void clearMessage();    // call after handling
    void forwardMessage(const char* msg);  // send to second Arduino

private:
    HardwareSerial& ros_;
    HardwareSerial& board_;
    uint32_t rosBaud_;
    uint32_t boardBaud_;

    static const uint8_t BUF_SIZE = 64;
    char buffer_[BUF_SIZE];
    uint8_t bufIdx_ = 0;
    bool messageReady_ = false;
};
