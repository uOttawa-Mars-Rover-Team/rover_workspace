#include "AppMServo.h"
#include <Arduino.h>
#include <stdlib.h>
#include <string.h>

// Placeholder pins — confirm against the actual GNC shield wiring.
#define A_PAN_PIN   6
#define A_TILT_PIN  7
#define B_PIN       8
#define C_PIN       9

#define MIN_DEG     0
#define MAX_DEG     180
#define START_DEG   90
#define STEP        2
#define STEP_DELAY  15

static int8_t clampDir(int value)
{
    if (value > 0) return 1;
    if (value < 0) return -1;
    return 0;
}

void AppMServo::init()
{
    count_ = 0;

    aPan_.init (A_PAN_PIN,  MIN_DEG, MAX_DEG, START_DEG, STEP, STEP_DELAY);
    aTilt_.init(A_TILT_PIN, MIN_DEG, MAX_DEG, START_DEG, STEP, STEP_DELAY);
    servoA_.init(&aPan_, &aTilt_);

    bAxis_.init(B_PIN, MIN_DEG, MAX_DEG, START_DEG, STEP, STEP_DELAY);
    servoB_.init(&bAxis_, nullptr);

    cAxis_.init(C_PIN, MIN_DEG, MAX_DEG, START_DEG, STEP, STEP_DELAY);
    servoC_.init(&cAxis_, nullptr);

    entries_[count_++] = {'A', &servoA_, 2};
    entries_[count_++] = {'B', &servoB_, 1};
    entries_[count_++] = {'C', &servoC_, 1};

    Serial.println(F("[MSERVO] Ready  A=2-axis  B=1-axis  C=1-axis"));
    Serial.println(F("[MSERVO] msg: SV;<A|B|C>;<v>[;v]!   e.g. SV;A;-1;1!"));
}

void AppMServo::update()
{
    unsigned long now = millis();
    for (uint8_t i = 0; i < count_; i++) {
        entries_[i].servo->tick(now);
    }
}

AppMServo::Entry* AppMServo::find(char id)
{
    for (uint8_t i = 0; i < count_; i++) {
        if (entries_[i].id == id) {
            return &entries_[i];
        }
    }
    return nullptr;
}

void AppMServo::handleMessage(const char* msg)
{
    if (msg == nullptr) {
        return;
    }

    // Mutable copy for strtok. Accepts "SV;A;-1;1" (no trailing '!').
    char buffer[64];
    strncpy(buffer, msg, sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\0';

    char* cmd = strtok(buffer, ";");
    if (cmd == nullptr || strcmp(cmd, "SV") != 0) {
        Serial.print(F("[MSERVO] Not an SV cmd: "));
        Serial.println(msg);
        return;
    }

    handleServoCmd(buffer);
}

void AppMServo::handleServoCmd(char* /*bufferAlreadyTokenized*/)
{
    // Continues strtok() after the "SV" token from handleMessage().
    char* idTok = strtok(nullptr, ";");
    if (idTok == nullptr || idTok[0] == '\0') {
        Serial.println(F("[MSERVO] SV: missing servo id"));
        return;
    }

    char   id = idTok[0];
    Entry* e  = find(id);
    if (e == nullptr) {
        Serial.print(F("[MSERVO] SV: unknown servo "));
        Serial.println(id);
        return;
    }

    int8_t dirs[2] = {0, 0};
    for (uint8_t i = 0; i < e->axisCount; i++) {
        char* v = strtok(nullptr, ";");
        if (v == nullptr) {
            break;
        }
        dirs[i] = clampDir(atoi(v));
    }

    e->servo->move(dirs[0], dirs[1]);

    Serial.print(F("[MSERVO] SV "));
    Serial.print(id);
    Serial.print(F("  ax0="));
    Serial.print(dirs[0]);
    if (e->axisCount >= 2) {
        Serial.print(F("  ax1="));
        Serial.print(dirs[1]);
    }
    Serial.println();
}
