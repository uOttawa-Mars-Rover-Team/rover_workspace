#include "CommSerial.h"

CommSerial::CommSerial(HardwareSerial& rosSerial, HardwareSerial& boardSerial, uint32_t rosBaud, uint32_t boardBaud)
    : ros_(rosSerial), board_(boardSerial), rosBaud_(rosBaud), boardBaud_(boardBaud)
{}

void CommSerial::init() {
    ros_.begin(rosBaud_);
    board_.begin(boardBaud_);
}

void CommSerial::update() {
    while (ros_.available() && !messageReady_) {
        char c = ros_.read();
        if (c == '\n') {
            buffer_[bufIdx_] = '\0';   // null terminate
            bufIdx_ = 0;
            messageReady_ = true;
        } else if (bufIdx_ < BUF_SIZE - 1) {
            buffer_[bufIdx_++] = c;
        }
        // silently drop chars if buffer overflows
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

void CommSerial::forwardMessage(const char* msg) {
    board_.print(msg);
    board_.print('\n');
}
