#include "DriverEncoder.h"

DriverEncoder::DriverEncoder(uint8_t csPin, uint8_t resolution)
    : csPin_(csPin), resolution_(resolution)
{}

void DriverEncoder::init() {
    pinMode(csPin_, OUTPUT);
    digitalWrite(csPin_, HIGH);
    SPI.begin();
}

uint16_t DriverEncoder::getPosition() {
    uint16_t pos = readPositionSPI();
    lastReadOk_  = (pos != 0xFFFF);
    return pos;
}

bool DriverEncoder::isOk() {
    return lastReadOk_;
}

void DriverEncoder::setZero() {
    spiWriteRead(AMT22_NOP,  false);
    delayMicroseconds(3);
    spiWriteRead(AMT22_ZERO, true);
    delay(250);
}

void DriverEncoder::reset() {
    spiWriteRead(AMT22_NOP,   false);
    delayMicroseconds(3);
    spiWriteRead(AMT22_RESET, true);
    delay(250);
}

// ── Private ───────────────────────────────────────────────────────────────────

uint16_t DriverEncoder::readPositionSPI() {
    uint16_t pos = spiWriteRead(AMT22_NOP, false) << 8;
    delayMicroseconds(3);
    pos |= spiWriteRead(AMT22_NOP, true);

    // checksum validation
    bool b[16];
    for (int i = 0; i < 16; i++) b[i] = (0x01) & (pos >> i);

    bool oddOk  = (b[15] == !(b[13]^b[11]^b[9]^b[7]^b[5]^b[3]^b[1]));
    bool evenOk = (b[14] == !(b[12]^b[10]^b[8]^b[6]^b[4]^b[2]^b[0]));

    if (!oddOk || !evenOk) return 0xFFFF;

    pos &= 0x3FFF;   // mask checkbits

    if (resolution_ == RES12 && pos != 0xFFFF) pos >>= 2;

    return pos;
}

uint8_t DriverEncoder::spiWriteRead(uint8_t sendByte, bool releaseLine) {
    setCS(LOW);
    delayMicroseconds(3);
    uint8_t data = SPI.transfer(sendByte);
    delayMicroseconds(3);
    setCS(releaseLine ? HIGH : LOW);
    return data;
}

void DriverEncoder::setCS(bool state) {
    digitalWrite(csPin_, state ? HIGH : LOW);
}
