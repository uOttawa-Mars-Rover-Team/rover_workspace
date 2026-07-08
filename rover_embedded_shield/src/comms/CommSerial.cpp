#include "CommSerial.h"

CommSerial::CommSerial(HardwareSerial& rosSerial, HardwareSerial& boardSerial,
                       uint32_t rosBaud, uint32_t boardBaud)
    : ros_(rosSerial), board_(boardSerial), rosBaud_(rosBaud), boardBaud_(boardBaud)
{}

void CommSerial::init() {
    ros_.begin(rosBaud_);
    board_.begin(boardBaud_);
}

bool CommSerial::feedByte(char c, char* buf, uint8_t& idx, bool& readyFlag) {
    if (c == TERMINATOR) {
        buf[idx] = '\0';
        idx = 0;
        readyFlag = true;
        return true;
    } else if (c == '\n' || c == '\r') {
        // Ignore stray line-ending bytes that may accompany the terminator;
        // they are not part of the message payload.
        return false;
    } else if (idx < BUF_SIZE - 1) {
        buf[idx++] = c;
        return false;
    } else {
        // Buffer overflow: message is malformed or longer than expected.
        // Reset so the next terminator can start a clean message,
        // rather than silently discarding all future bytes forever.
        idx = 0;
        return false;
    }
}

void CommSerial::update() {
    while (ros_.available() && !messageReady_) {
        char c = ros_.read();
        feedByte(c, buffer_, bufIdx_, messageReady_);
    }

    while (board_.available() && !boardMessageReady_) {
        char c = board_.read();
        feedByte(c, boardBuffer_, boardBufIdx_, boardMessageReady_);
    }
}

bool CommSerial::messageReady() {
    return messageReady_;
}

const char* CommSerial::getMessage() {
    return buffer_;
}

void CommSerial::clearMessage() {
    messageReady_ = false;
}

bool CommSerial::boardMessageReady() {
    return boardMessageReady_;
}

const char* CommSerial::getBoardMessage() {
    return boardBuffer_;
}

void CommSerial::clearBoardMessage() {
    boardMessageReady_ = false;
}

void CommSerial::forwardMessage(const char* msg) {
    board_.print(msg);
    board_.print(TERMINATOR);
}

void CommSerial::forwardToRos(const char* msg) {
    ros_.print(msg);
    ros_.print(TERMINATOR);
}
