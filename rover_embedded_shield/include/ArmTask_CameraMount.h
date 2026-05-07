#ifndef _ARM_TASK_CAMERA_MOUNT_H_
#define _ARM_TASK_CAMERA_MOUNT_H_

//------------------------------------------
//  Includes
//------------------------------------------
#include <stdint.h>
#include "ArmDriver_Servo.h"

//------------------------------------------
//  Defines
//------------------------------------------

//------------------------------------------
//  Datatype Definitions
//------------------------------------------

/**
 * @brief One dual-axis camera mount = pair of ArmDriver_Servo (x, y).
 *
 * @details The "TaskServo" in the team-lead architecture: coordinates two
 * single-axis ArmDriver_Servo instances as a single (x, y) unit. The rover
 * carries 3 of these (one per camera). The mount itself has no state machine;
 * it simply forwards lifecycle calls (init / setTargetXY / stop / tick) to
 * both children, and aggregates their state for isIdle().
 */
class ArmTask_CameraMount
{
public:
    /**
     * @brief Attach both axes; must be called once from setup().
     *
     * @param pinX  PWM pin for the X axis servo
     * @param pinY  PWM pin for the Y axis servo
     * @param initX initial X angle, clamped to [0, 180]
     * @param initY initial Y angle, clamped to [0, 180]
     *
     * @return void
     */
    void init(uint8_t pinX, uint8_t pinY,
              uint8_t initX = 90, uint8_t initY = 90);

    /**
     * @brief Aim both axes at absolute (xDeg, yDeg) at msPerStep cadence.
     *
     * @return void
     */
    void setTargetXY(uint8_t xDeg, uint8_t yDeg, uint16_t msPerStep);

    /**
     * @brief Nudge both axes by signed (dx, dy) at msPerStep cadence.
     *
     * @return void
     */
    void incrementXY(int16_t dx, int16_t dy, uint16_t msPerStep);

    /**
     * @brief Halt both axes. Servos hold at their current angles.
     *
     * @return void
     */
    void stop();

    /**
     * @brief Forward the tick to both axes. Call from loop() with millis().
     *
     * @return void
     */
    void tick(unsigned long now_ms);

    /**
     * @brief True iff neither axis is currently MOVING.
     *
     * @details Useful for the demo / future application layer to detect that
     * the mount has reached its commanded pose so a new command can be issued.
     */
    bool isIdle() const;

    const ArmDriver_Servo& x() const;
    const ArmDriver_Servo& y() const;

private:
    ArmDriver_Servo x_;
    ArmDriver_Servo y_;
};

#endif
