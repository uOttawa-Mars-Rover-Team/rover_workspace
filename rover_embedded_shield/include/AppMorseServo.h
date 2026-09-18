#pragma once
#include <Arduino.h>
#include <Servo.h>
class AppMorseServo {
public:
    void init();
    void end();              // detach servo cleanly — call on EXIT
    void update();          // call every loop when in MORSE mode
    void handleMessage(const char* msg);  // pass parsed message from CommSerial
private:
    // ── Types ──────────────────────────────────────────────────────
    enum EventType  { EV_PRESS, EV_WAIT };
    enum MorseState { MS_IDLE, MS_PRESSING, MS_HOLDING, MS_RELEASING, MS_WAITING };
    struct MorseEvent {
        EventType     type;
        unsigned long durationMs;
    };
    struct MorseChar {
        char        ch;
        const char* code;
    };
    // ── Constants ──────────────────────────────────────────────────
    static const uint8_t  SERVO_PIN    = 6;
    static const int      ENDPOINT_HI  = 30;
    static const int      ENDPOINT_LO  = 100;
    static const uint16_t QUEUE_SIZE   = 512;
    static const MorseChar MORSE_TABLE[];
    // ── Timing ─────────────────────────────────────────────────────
    unsigned long ditMs_       = 67UL;
    unsigned long dahMs_       = 0;
    unsigned long intraCharMs_ = 0;
    unsigned long interCharMs_ = 0;
    unsigned long interWordMs_ = 0;
    // ── Queue ──────────────────────────────────────────────────────
    MorseEvent morseQueue_[QUEUE_SIZE];
    uint16_t   qHead_ = 0;
    uint16_t   qTail_ = 0;
    // ── Servo ──────────────────────────────────────────────────────
    Servo        servo_;
    int          currentPos_   = ENDPOINT_LO;
    int          targetPos_    = ENDPOINT_LO;
    int          stepSize_     = 10;
    int          stepDelayMs_  = 5;
    bool         sweeping_     = false;
    bool         firstLeg_     = false;
    unsigned long lastStepTime_ = 0;
    // ── Morse FSM ──────────────────────────────────────────────────
    MorseState    morseState_      = MS_IDLE;
    unsigned long morseEventStart_ = 0;
    unsigned long morseEventDur_   = 0;
    // ── Internal methods ───────────────────────────────────────────
    void        recomputeTiming();
    const char* getMorse(char c);
    bool       queueEmpty();
    bool       queueFull();
    MorseEvent queuePeek();
    void       queuePop();
    bool       queuePush(EventType t, unsigned long dur);
    bool encodeTextToQueue(const char* text);
    void startSweepTo(int target, bool isFirstLeg);
    void advanceMorse();
    void updateServo();
    void updateMorse();
    void printStatus();
};
