#ifndef COMM_SERIAL_H
#define COMM_SERIAL_H

#include <Arduino.h>

class CommSerial {
public:
    CommSerial(HardwareSerial& rosSerial, HardwareSerial& boardSerial,
               uint32_t rosBaud, uint32_t boardBaud);

    void init();

    // Call every loop() iteration. Drains available bytes from both ports
    // into their respective buffers, non-blocking.
    void update();

    // --- ROS/router-facing channel (e.g. Serial from GNC/router) ---
    bool messageReady();
    const char* getMessage();
    void clearMessage();

    // --- Board-facing piggyback channel (e.g. Serial3/Serial1 to other board) ---
    bool boardMessageReady();
    const char* getBoardMessage();
    void clearBoardMessage();

    // Send a message out to the piggybacked board, terminator appended automatically
    void forwardMessage(const char* msg);

    // Send a message out to the ROS/router-facing side, terminator appended automatically
    void forwardToRos(const char* msg);

private:
    static const uint8_t BUF_SIZE = 64;
    static const char TERMINATOR = '!';

    HardwareSerial& ros_;
    HardwareSerial& board_;
    uint32_t rosBaud_;
    uint32_t boardBaud_;

    char buffer_[BUF_SIZE];
    uint8_t bufIdx_ = 0;
    bool messageReady_ = false;

    char boardBuffer_[BUF_SIZE];
    uint8_t boardBufIdx_ = 0;
    bool boardMessageReady_ = false;

    // Shared parsing logic for a single incoming byte into a given buffer.
    // Returns true if a complete message just became ready.
    bool feedByte(char c, char* buf, uint8_t& idx, bool& readyFlag);
};

#endif
