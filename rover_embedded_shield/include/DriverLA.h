#ifndef DRIVER_LA_H
#define DRIVER_LA_H

#include <stdint.h>
#include "JrkG2.h"
#include "Arduino.h"

void DriverLA_InitI2C();

/**
 * Pololu Jrk G2 linear actuator over I2C. Construct with the Jrk address (e.g. 11, 12).
 *
 * moveMotor(speed, direction):
 *   direction: -1 retract, 0 stop, 1 extend
 *   speed: magnitude from kSpeedZero toward kMaxExtend / kMaxRetract (same semantics as arm driver).
 */
class DriverLA {
public:
    static constexpr uint16_t kSpeedZero = 2048;
    static constexpr uint16_t kMaxExtend = 2648;
    static constexpr uint16_t kMaxRetract = 1448;

    explicit DriverLA(uint8_t i2cAddress);

    void moveMotor(uint16_t speed, int8_t direction);

private:
    JrkG2I2C jrk_;
};

#endif