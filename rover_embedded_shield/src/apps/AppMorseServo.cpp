#include "AppMorseServo.h"

// ── Morse table ────────────────────────────────────────────────────────────────
const AppMorseServo::MorseChar AppMorseServo::MORSE_TABLE[] = {
    {'A',".-"},   {'B',"-..."}, {'C',"-.-."}, {'D',"-.." },
    {'E',"."},    {'F',"..-."}, {'G',"--."},  {'H',"...."},
    {'I',".."},   {'J',".---"}, {'K',"-.-"},  {'L',".-.."},
    {'M',"--"},   {'N',"-."},   {'O',"---"},  {'P',".--."},
    {'Q',"--.-"}, {'R',".-."},  {'S',"..."},  {'T',"-"},
    {'U',"..-"},  {'V',"...-"}, {'W',".--"},  {'X',"-..-"},
    {'Y',"-.--"}, {'Z',"--.."},
    {'0',"-----"},{'1',".----"},{'2',"..---"},{'3',"...--"},
    {'4',"....-"},{'5',"....."},{'6',"-...."},{'7',"--..."},
    {'8',"---.."}, {'9',"----."},
    {'.', ".-.-.-"}, {',', "--..--"}, {':', "---..."},
    {'?', "..--.."}, {'\'',".----."}, {'-', "-....-"},
    {'/', "-..-." }, {'(', "-.--." }, {')', "-.--.-"},
    {'"', ".-..-."}, {'=', "-...-" }, {'+', ".-.-."},
    {'@', ".--.-." },
    {'\0', nullptr}
};

// ── Init ───────────────────────────────────────────────────────────────────────
void AppMorseServo::init() {
    recomputeTiming();

    // Guard against double-attach: if something else (e.g. TaskButton on the
    // same pin) is still holding the Servo timer channel, detach first so we
    // don't end up with two Servo instances fighting over pin 6.
    if (servo_.attached()) servo_.detach();
    servo_.attach(SERVO_PIN);

    currentPos_ = ENDPOINT_HI;
    targetPos_  = ENDPOINT_HI;
    sweeping_   = false;
    morseState_ = MS_IDLE;

    servo_.write(currentPos_);
    Serial.println(F("[MORSE] App initialized on pin 6"));
    Serial.println(F("[MORSE] Commands: M <text>, G, S <n>, D <ms>, T <ms>, P, EXIT"));
    printStatus();
}

// ── Teardown — call before handing the pin back to another consumer ───────────
void AppMorseServo::end() {
    if (servo_.attached()) servo_.detach();
    sweeping_   = false;
    morseState_ = MS_IDLE;
    qHead_ = qTail_ = 0;
}

// ── Main update — call every loop when in MORSE mode ──────────────────────────
void AppMorseServo::update() {
    updateServo();
    updateMorse();
}

// ── Message handler — receives parsed message from CommSerial ─────────────────
void AppMorseServo::handleMessage(const char* msg) {

    // Skip "RA;" prefix if present
    const char* payload = msg;
    if (strncmp(msg, "RA;", 3) == 0) payload = msg + 3;

    char cmd = payload[0];

    switch (cmd) {

        case 'M': case 'm': {
            const char* text = payload + 1;
            if (text[0] == ';') text++;   // skip separator if "M;SOS"
            if (text[0] == ' ') text++;   // skip space if "M SOS"

            if (text[0] == '\0') {
                Serial.println(F("[MORSE] No text. Usage: M SOS or M;SOS"));
                break;
            }
            if (morseState_ != MS_IDLE) {
                Serial.println(F("[MORSE] Busy — wait for transmission to finish"));
                break;
            }
            Serial.print(F("[MORSE] Encoding: "));
            Serial.println(text);
            recomputeTiming();
            if (!encodeTextToQueue(text)) {
                Serial.println(F("[MORSE] Queue overflow — text too long"));
                break;
            }
            advanceMorse();
            break;
        }

        case 'G': case 'g': {
            if (sweeping_ || morseState_ != MS_IDLE) {
                Serial.println(F("[MORSE] Busy — ignoring G"));
                break;
            }
            Serial.println(F("[MORSE] Manual sweep"));
            startSweepTo(ENDPOINT_LO, true);
            break;
        }

        case 'S': case 's': {
            int val = atoi(payload + 1 + (payload[1] == ';' ? 1 : 0));
            if (val >= 1 && val <= 90) {
                stepSize_ = val;
                Serial.print(F("[MORSE] Step size = ")); Serial.println(stepSize_);
            } else Serial.println(F("[MORSE] Step size must be 1-90"));
            break;
        }

        case 'D': case 'd': {
            int val = atoi(payload + 1 + (payload[1] == ';' ? 1 : 0));
            if (val >= 1 && val <= 5000) {
                stepDelayMs_ = val;
                Serial.print(F("[MORSE] Step delay = ")); Serial.println(stepDelayMs_);
            } else Serial.println(F("[MORSE] Delay must be 1-5000 ms"));
            break;
        }

        case 'T': case 't': {
            int val = atoi(payload + 1 + (payload[1] == ';' ? 1 : 0));
            if (val >= 10 && val <= 2000) {
                ditMs_ = (unsigned long)val;
                recomputeTiming();
                Serial.print(F("[MORSE] Dit=")); Serial.println(ditMs_);
            } else Serial.println(F("[MORSE] Dit length must be 10-2000 ms"));
            break;
        }

        case 'P': case 'p': {
            printStatus();
            break;
        }

        default:
            Serial.print(F("[MORSE] Unknown command: "));
            Serial.println(payload);
            break;
    }
}

// ── Timing ─────────────────────────────────────────────────────────────────────
void AppMorseServo::recomputeTiming() {
    dahMs_       = ditMs_ * 3;
    intraCharMs_ = ditMs_;
    interCharMs_ = ditMs_ * 3;
    interWordMs_ = ditMs_ * 7;
}

// ── Morse lookup ───────────────────────────────────────────────────────────────
const char* AppMorseServo::getMorse(char c) {
    if (c >= 'a' && c <= 'z') c -= 32;
    for (int i = 0; MORSE_TABLE[i].ch != '\0'; i++) {
        if (MORSE_TABLE[i].ch == c) return MORSE_TABLE[i].code;
    }
    return nullptr;
}

// ── Queue ──────────────────────────────────────────────────────────────────────
bool AppMorseServo::queueEmpty() { return qHead_ == qTail_; }
bool AppMorseServo::queueFull()  { return ((qTail_ + 1) % QUEUE_SIZE) == qHead_; }
AppMorseServo::MorseEvent AppMorseServo::queuePeek() { return morseQueue_[qHead_]; }
void AppMorseServo::queuePop()   { qHead_ = (qHead_ + 1) % QUEUE_SIZE; }

bool AppMorseServo::queuePush(EventType t, unsigned long dur) {
    if (queueFull()) return false;
    morseQueue_[qTail_] = {t, dur};
    qTail_ = (qTail_ + 1) % QUEUE_SIZE;
    return true;
}

// ── Encoder ────────────────────────────────────────────────────────────────────
bool AppMorseServo::encodeTextToQueue(const char* text) {
    qHead_ = 0; qTail_ = 0;
    bool prevWasLetter = false;

    for (int i = 0; text[i] != '\0'; i++) {
        char c = text[i];
        if (c == ' ') {
            if (prevWasLetter) {
                if (!queuePush(EV_WAIT, interWordMs_ - interCharMs_)) return false;
            }
            prevWasLetter = false;
            continue;
        }
        const char* code = getMorse(c);
        if (code == nullptr) continue;

        if (prevWasLetter) {
            if (!queuePush(EV_WAIT, interCharMs_)) return false;
        }
        for (int s = 0; code[s] != '\0'; s++) {
            if (s > 0) {
                if (!queuePush(EV_WAIT, intraCharMs_)) return false;
            }
            unsigned long dur = (code[s] == '-') ? dahMs_ : ditMs_;
            if (!queuePush(EV_PRESS, dur)) return false;
        }
        prevWasLetter = true;
    }
    return true;
}

// ── Servo helper ───────────────────────────────────────────────────────────────
void AppMorseServo::startSweepTo(int target, bool isFirstLeg) {
    targetPos_ = target;
    firstLeg_  = isFirstLeg;
    sweeping_  = true;
}

// ── Morse FSM advance ──────────────────────────────────────────────────────────
void AppMorseServo::advanceMorse() {
    if (queueEmpty()) {
        morseState_ = MS_IDLE;
        Serial.println(F("[MORSE] Transmission complete"));
        return;
    }
    MorseEvent ev = queuePeek();
    queuePop();

    if (ev.type == EV_PRESS) {
        morseEventDur_ = ev.durationMs;
        morseState_    = MS_PRESSING;
        startSweepTo(ENDPOINT_LO, true);
    } else {
        morseEventStart_ = millis();
        morseEventDur_   = ev.durationMs;
        morseState_      = MS_WAITING;
    }
}

// ── Servo update ───────────────────────────────────────────────────────────────
void AppMorseServo::updateServo() {
    if (!sweeping_) return;
    unsigned long now = millis();
    if (now - lastStepTime_ < (unsigned long)stepDelayMs_) return;
    lastStepTime_ = now;

    if (currentPos_ < targetPos_)
        currentPos_ = min(currentPos_ + stepSize_, targetPos_);
    else if (currentPos_ > targetPos_)
        currentPos_ = max(currentPos_ - stepSize_, targetPos_);

    servo_.write(currentPos_);

    if (currentPos_ == targetPos_) {
        sweeping_ = false;
        if (firstLeg_) {
            if (morseState_ == MS_PRESSING) {
                morseEventStart_ = millis();
                morseState_      = MS_HOLDING;
            } else {
                startSweepTo(ENDPOINT_HI, false);
            }
        } else {
            if (morseState_ == MS_RELEASING) {
                advanceMorse();
            }
        }
    }
}

// ── Morse FSM update ───────────────────────────────────────────────────────────
void AppMorseServo::updateMorse() {
    if (morseState_ == MS_IDLE) return;
    unsigned long now = millis();
    switch (morseState_) {
        case MS_HOLDING:
            if (now - morseEventStart_ >= morseEventDur_) {
                morseState_ = MS_RELEASING;
                startSweepTo(ENDPOINT_HI, false);
            }
            break;
        case MS_WAITING:
            if (now - morseEventStart_ >= morseEventDur_) {
                advanceMorse();
            }
            break;
        default:
            break;
    }
}

// ── Status ─────────────────────────────────────────────────────────────────────
void AppMorseServo::printStatus() {
    Serial.println(F("─────────────────────────────────────"));
    Serial.print(F("  Position   : ")); Serial.print(currentPos_);   Serial.println(F("°"));
    Serial.print(F("  Step size  : ")); Serial.print(stepSize_);     Serial.println(F("°/tick"));
    Serial.print(F("  Step delay : ")); Serial.print(stepDelayMs_);  Serial.println(F(" ms"));
    Serial.print(F("  Dit        : ")); Serial.print(ditMs_);        Serial.println(F(" ms"));
    Serial.print(F("  Dah        : ")); Serial.print(dahMs_);        Serial.println(F(" ms"));
    Serial.print(F("  Morse state: "));
    switch (morseState_) {
        case MS_IDLE:      Serial.println(F("IDLE"));      break;
        case MS_PRESSING:  Serial.println(F("PRESSING"));  break;
        case MS_HOLDING:   Serial.println(F("HOLDING"));   break;
        case MS_RELEASING: Serial.println(F("RELEASING")); break;
        case MS_WAITING:   Serial.println(F("WAITING"));   break;
    }
    Serial.println(F("─────────────────────────────────────"));
}
