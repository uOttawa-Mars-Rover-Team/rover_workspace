#include "DriverLA.h"

void DriverLA_InitI2C() { Wire.begin(); }

DriverLA::DriverLA(uint8_t i2cAddress) : jrk_(i2cAddress) {}


void DriverLA::moveMotor(uint16_t speed, int8_t direction) {
    if (direction == 1) { //extend
        int32_t target =
            static_cast<int32_t>(kSpeedZero) + static_cast<int32_t>(speed);
        if (target > static_cast<int32_t>(kMaxExtend)) {
            jrk_.setTarget(kMaxExtend);
        } else {
            jrk_.setTarget(static_cast<uint16_t>(target));
        }
    } else if (direction == -1) {
        int32_t target =
            static_cast<int32_t>(kSpeedZero) - static_cast<int32_t>(speed);
        if (target < static_cast<int32_t>(kMaxRetract)) {
            jrk_.setTarget(kMaxRetract);
        } else {
            jrk_.setTarget(static_cast<uint16_t>(target));
        }
    } else {
        jrk_.stopMotor();
    }
}
