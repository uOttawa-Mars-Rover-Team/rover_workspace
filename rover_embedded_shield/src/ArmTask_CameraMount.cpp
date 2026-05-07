/*
 * Description: Dual-axis camera mount task. Owns a pair of ArmDriver_Servo
 *              (x, y) and exposes them as one (x, y) unit. The "TaskServo"
 *              in the team-lead architecture; the rover carries 3 of these.
 * Authors:
 */
//------------------------------------------
//  Includes
//------------------------------------------
#include "ArmTask_CameraMount.h"

//------------------------------------------
//  Global Defines
//------------------------------------------

//------------------------------------------
//  Datatype Definitions
//------------------------------------------

//------------------------------------------
//  Global Variables
//------------------------------------------

//------------------------------------------
//  Local Variables
//------------------------------------------

//------------------------------------------
//  Local Function Prototypes
//------------------------------------------

//------------------------------------------
//  Global Functions Definitions
//------------------------------------------

/**
 * @brief Attach both axes with default 0..180 mechanical range.
 *
 * @details Per-axis bounds can be tightened later if the team confirms a
 * narrower physical range; for now the legacy 0..180 sweep is preserved.
 *
 * @return void
 */
void ArmTask_CameraMount::init(uint8_t pinX, uint8_t pinY,
                               uint8_t initX, uint8_t initY)
{
    x_.init(pinX, ARM_DRIVER_SERVO_DEFAULT_MIN_DEG,
                  ARM_DRIVER_SERVO_DEFAULT_MAX_DEG, initX);
    y_.init(pinY, ARM_DRIVER_SERVO_DEFAULT_MIN_DEG,
                  ARM_DRIVER_SERVO_DEFAULT_MAX_DEG, initY);
}

/**
 * @brief Issue absolute targets to both axes simultaneously.
 *
 * @return void
 */
void ArmTask_CameraMount::setTargetXY(uint8_t xDeg, uint8_t yDeg,
                                      uint16_t msPerStep)
{
    x_.setTarget(xDeg, msPerStep);
    y_.setTarget(yDeg, msPerStep);
}

/**
 * @brief Issue signed deltas to both axes simultaneously.
 *
 * @return void
 */
void ArmTask_CameraMount::incrementXY(int16_t dx, int16_t dy,
                                      uint16_t msPerStep)
{
    x_.incrementTarget(dx, msPerStep);
    y_.incrementTarget(dy, msPerStep);
}

/**
 * @brief Halt both axes; equivalent to legacy 'svs'.
 *
 * @return void
 */
void ArmTask_CameraMount::stop()
{
    x_.stop();
    y_.stop();
}

/**
 * @brief Tick both children. Each ArmDriver_Servo decides independently
 *        whether enough time has elapsed for its next 1-degree step.
 *
 * @return void
 */
void ArmTask_CameraMount::tick(unsigned long now_ms)
{
    x_.tick(now_ms);
    y_.tick(now_ms);
}

/**
 * @brief Mount is idle iff neither axis is in the MOVING state.
 *
 * @details AT_TARGET, AT_LIMIT, and IDLE all count as "not moving". Use this
 * before issuing a new XY target if you want to wait for the previous one to
 * settle.
 */
bool ArmTask_CameraMount::isIdle() const
{
    return x_.getState() != ArmDriver_Servo::State::MOVING
        && y_.getState() != ArmDriver_Servo::State::MOVING;
}

const ArmDriver_Servo& ArmTask_CameraMount::x() const { return x_; }
const ArmDriver_Servo& ArmTask_CameraMount::y() const { return y_; }

//------------------------------------------
//  Local Function Definition
//------------------------------------------
