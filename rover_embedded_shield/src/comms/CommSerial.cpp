#include "CommSerial.h"

CommSerial::CommSerial(HardwareSerial& boardSerial,
                       uint32_t        boardBaud,
                       const char*     prefix,
                       void          (*handler)(char* payload))
    : board_(boardSerial),
      boardBaud_(boardBaud),
      prefix_(prefix),
      handler_(handler)
{}

void CommSerial::init() {
    board_.begin(boardBaud_);
}

void CommSerial::update() {
    // accumulate replies coming back from other board
    while (board_.available()) {
        char c = board_.read();
        if (c == '\n' || c == '\r') {
            if (boardIdx_ > 0) {
                boardBuf_[boardIdx_] = '\0';
                boardIdx_   = 0;
                boardReady_ = true;
            }
        } else if (boardIdx_ < BUF_SIZE - 1) {
            boardBuf_[boardIdx_++] = c;
        }
    }

    // propagate reply to USB debug terminal
    if (boardReady_) {
        boardReady_ = false;
        Serial.print(F("[BOARD] "));
        Serial.println(boardBuf_);
    }
}

void CommSerial::handleMessage(char* msg) {
    uint8_t prefixLen = strlen(prefix_);

    // ── Message matches this board's prefix → call handler ──────────────────
    if (strncmp(msg, prefix_, prefixLen) == 0) {
        handler_(msg + prefixLen);   // strip prefix, pass payload
        return;
    }

    // ── S; legacy axis command → pass to handler without prefix strip ────────
    if (msg[0] == 'S' && msg[1] == ';') {
        handler_(msg);
        return;
    }

    // ── Unknown prefix → forward to other board ──────────────────────────────
    // If it's not ours, assume it belongs to the other board
    forwardMessage(msg);
    Serial.print(F("[SYS] Forwarded: "));
    Serial.println(msg);
}

void CommSerial::forwardMessage(const char* msg) {
    board_.print(msg);
    board_.print('\n');
}
