#ifndef _ARM_DRIVER_SERVO_H_
#define _ARM_DRIVER_SERVO_H_

//------------------------------------------
//  Includes
//------------------------------------------
#include <stdint.h>
#include <Servo.h>

//------------------------------------------
//  Defines
//------------------------------------------
#define ARM_DRIVER_SERVO_DEFAULT_MIN_DEG    0
#define ARM_DRIVER_SERVO_DEFAULT_MAX_DEG    180
#define ARM_DRIVER_SERVO_DEFAULT_INIT_DEG   90

//------------------------------------------
//  Datatype Definitions
//------------------------------------------

/**
 * @brief Single-axis servo driver with a non-blocking, ms-per-step state machine.
 *
 * @details Wraps one Arduino Servo and advances currentDeg toward targetDeg by
 * +/- 1 degree each time tick() is called and msPerStep_ has elapsed since the
 * last step. The driver layer in the team-lead architecture: 6 of these are
 * composed into 3 ArmTask_CameraMount instances (x, y per mount).
 */
class ArmDriver_Servo
{
public:
    /**
     * @brief Lifecycle state of one axis. Only MOVING actually advances the
     * servo on tick(); all other states are quiescent.
     */
    enum class State : uint8_t
    {
        IDLE,       /**< Not initialized to a target, or stop() called. */
        MOVING,     /**< Stepping toward targetDeg_ at msPerStep_ cadence. */
        AT_TARGET,  /**< currentDeg_ == targetDeg_, away from bounds. */
        AT_LIMIT    /**< currentDeg_ has reached minDeg_ or maxDeg_. */
    };

    /**
     * @brief Attach servo to PWM pin and seed the initial position.
     *
     * Must be called once from setup() before any other method on this object.
     * Writes initialDeg to the servo immediately so the physical horn is
     * centered at boot.
     *
     * @param pwmPin     PWM-capable Arduino pin
     * @param minDeg     mechanical lower bound, inclusive
     * @param maxDeg     mechanical upper bound, inclusive (>= minDeg)
     * @param initialDeg starting angle, clamped to [minDeg, maxDeg]
     *
     * @return void
     */
    void init(uint8_t pwmPin,
              uint8_t minDeg     = ARM_DRIVER_SERVO_DEFAULT_MIN_DEG,
              uint8_t maxDeg     = ARM_DRIVER_SERVO_DEFAULT_MAX_DEG,
              uint8_t initialDeg = ARM_DRIVER_SERVO_DEFAULT_INIT_DEG);

    /**
     * @brief Aim at an absolute angle, advancing 1 degree every msPerStep ms.
     *
     * @details Clamps targetDeg to [minDeg_, maxDeg_]. Transitions to MOVING
     * unless the servo is already at the requested angle, in which case the
     * resulting state is AT_LIMIT (if at a bound) or AT_TARGET.
     *
     * @param targetDeg  absolute target angle in degrees
     * @param msPerStep  delay between consecutive 1-degree steps
     *
     * @return void
     */
    void setTarget(uint8_t targetDeg, uint16_t msPerStep);

    /**
     * @brief Aim relative to currentDeg_ by deltaDeg (signed).
     *
     * @details Convenience wrapper around setTarget() for incremental commands
     * like the legacy svu / svd nudges. The new target is clamped.
     *
     * @param deltaDeg   signed degree delta, positive moves toward maxDeg_
     * @param msPerStep  delay between consecutive 1-degree steps
     *
     * @return void
     */
    void incrementTarget(int16_t deltaDeg, uint16_t msPerStep);

    /**
     * @brief Halt the state machine. The servo holds at currentDeg_.
     *
     * @return void
     */
    void stop();

    /**
     * @brief Drive the state machine forward.
     *
     * @details Call from loop() with millis(). No-op when state_ is not MOVING
     * or when fewer than msPerStep_ ms have elapsed since the last step.
     *
     * @param now_ms current value of millis()
     *
     * @return void
     */
    void tick(unsigned long now_ms);

    uint8_t getCurrentDeg() const;
    State   getState()      const;

private:
    Servo         servo_;
    uint8_t       pin_;
    uint8_t       minDeg_;
    uint8_t       maxDeg_;
    uint8_t       currentDeg_;
    uint8_t       targetDeg_;
    uint16_t      msPerStep_;
    unsigned long lastStep_ms_;
    State         state_;
};

#endif
