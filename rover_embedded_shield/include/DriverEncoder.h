#pragma once
#include <Arduino.h>
#include <SPI.h>

// AMT22 SPI absolute encoder driver
// Supports 12-bit and 14-bit resolution
// One instance per encoder, identified by CS pin

#define RES12 12
#define RES14 14

class DriverEncoder {
public:
    DriverEncoder(uint8_t csPin, uint8_t resolution = RES12);

    void     init();                // setup SPI and CS pin
    uint16_t getPosition();         // returns 0xFFFF on error
    bool     isOk();                // true if last read was valid
    void     setZero();             // zero the encoder
    void     reset();               // reset the encoder

private:
    uint8_t csPin_;
    uint8_t resolution_;
    bool    lastReadOk_ = false;

    static const uint8_t AMT22_NOP   = 0x00;
    static const uint8_t AMT22_ZERO  = 0x70;
    static const uint8_t AMT22_RESET = 0x60;

    uint16_t readPositionSPI();
    uint8_t  spiWriteRead(uint8_t sendByte, bool releaseLine);
    void     setCS(bool state);
};
