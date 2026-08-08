#pragma once
#include <Arduino.h>

class CommSerial {
public:
    // boardSerial  : the HardwareSerial port for inter-board link
    // boardBaud    : baud rate for inter-board link
    // prefix       : message prefix this board owns e.g. "GNC;" or "RA;"
    // handler      : function called with payload when prefix matches
    CommSerial(HardwareSerial& boardSerial,
               uint32_t        boardBaud,
               const char*     prefix,
               void          (*handler)(char* payload));

    void init();                            // start inter-board serial
    void update();                          // accumulate replies from other board
    void handleMessage(char* msg);          // route by prefix
    void forwardMessage(const char* msg);   // send raw message to other board

private:
    HardwareSerial& board_;
    uint32_t        boardBaud_;
    const char*     prefix_;
    void          (*handler_)(char* payload);

    static const uint8_t BUF_SIZE = 64;
    char    boardBuf_[BUF_SIZE];
    uint8_t boardIdx_   = 0;
    bool    boardReady_ = false;
};
