/*
 * servo_morse.txt
 * Non-blocking servo Morse code keyer for Arduino Mega
 * PWM pin 6 | Endpoints: 160° (rest/up) → 20° (press/down)
 * ITU-R M.1677-1 compliant timing
 *
 * Timing at 66.7 ms dit unit:
 *   Dit        : 66.7 ms  (1 unit)
 *   Dah        : 200.1 ms (3 units)
 *   Intra-char : 66.7 ms  (1 unit)  gap between signals in same letter
 *   Inter-char : 200.1 ms (3 units) gap between letters
 *   Inter-word : 466.9 ms (7 units) gap between words
 *
 * NOTE: Sweep travel time is mechanical overhead and is NOT counted as
 *       part of dit/dah duration. The hold timer starts on arrival at LO.
 *
 * Serial commands (115200 baud):
 *   M <text>  — send text as Morse  (e.g. "M SOS" or "M HELLO WORLD")
 *   G         — single manual sweep (160°→20°→160°)
 *   S <n>     — step size in degrees per tick  (default 5)
 *   D <ms>    — delay between steps in ms      (default 10)
 *   T <ms>    — override dit length in ms      (default 67)
 *   P         — print current status
 */

#include <Servo.h>

// ═══════════════════════════════════════════════════════════════════════════════
// 1. TYPES
// ═══════════════════════════════════════════════════════════════════════════════

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

// ═══════════════════════════════════════════════════════════════════════════════
// 2. CONSTANTS & LOOKUP TABLE
// ═══════════════════════════════════════════════════════════════════════════════

static const uint8_t SERVO_PIN   = 6;
static const int     ENDPOINT_HI = 160;   // rest / key-up
static const int     ENDPOINT_LO = 20;    // pressed / key-down

static const MorseChar MORSE_TABLE[] = {
  // Letters
  {'A',".-"},   {'B',"-..."}, {'C',"-.-."}, {'D',"-.." },
  {'E',"."},    {'F',"..-."}, {'G',"--."},  {'H',"...."},
  {'I',".."},   {'J',".---"}, {'K',"-.-"},  {'L',".-.."},
  {'M',"--"},   {'N',"-."},   {'O',"---"},  {'P',".--."},
  {'Q',"--.-"}, {'R',".-."},  {'S',"..."},  {'T',"-"},
  {'U',"..-"},  {'V',"...-"}, {'W',".--"},  {'X',"-..-"},
  {'Y',"-.--"}, {'Z',"--.."},
  // Digits
  {'0',"-----"},{'1',".----"},{'2',"..---"},{'3',"...--"},
  {'4',"....-"},{'5',"....."},{'6',"-...."},{'7',"--..."},
  {'8',"---.."}, {'9',"----."},
  // Punctuation (ITU-R M.1677-1 §1.1.3)
  {'.', ".-.-.-"}, {',', "--..--"}, {':', "---..."},
  {'?', "..--.."}, {'\'',".----."}, {'-', "-....-"},
  {'/', "-..-." }, {'(', "-.--." }, {')', "-.--.-"},
  {'"', ".-..-."}, {'=', "-...-" }, {'+', ".-.-."},
  {'@', ".--.-." },
  {'\0', nullptr}
};

// ═══════════════════════════════════════════════════════════════════════════════
// 3. GLOBALS
// ═══════════════════════════════════════════════════════════════════════════════

// ── Morse timing ──────────────────────────────────────────────────────────────
unsigned long ditMs       = 30UL;
unsigned long dahMs       = 0;
unsigned long intraCharMs = 0;
unsigned long interCharMs = 0;
unsigned long interWordMs = 0;

// ── Event queue ───────────────────────────────────────────────────────────────
static const uint16_t QUEUE_SIZE = 512;
MorseEvent morseQueue[QUEUE_SIZE];
uint16_t   qHead = 0;
uint16_t   qTail = 0;

// ── Servo ─────────────────────────────────────────────────────────────────────
Servo servo;
int  currentPos  = ENDPOINT_HI;
int  targetPos   = ENDPOINT_HI;
int  stepSize    = 15;    // default changed to 5
int  stepDelayMs = 10;
bool sweeping    = false;
bool firstLeg    = false;
unsigned long lastStepTime = 0;

// ── Morse FSM ─────────────────────────────────────────────────────────────────
MorseState    morseState      = MS_IDLE;
unsigned long morseEventStart = 0;   // set on ARRIVAL at LO (not on sweep start)
unsigned long morseEventDur   = 0;

// ═══════════════════════════════════════════════════════════════════════════════
// 4. FUNCTION PROTOTYPES
// ═══════════════════════════════════════════════════════════════════════════════

void          recomputeTiming();
const char*   getMorse(char c);
bool          queueEmpty();
bool          queueFull();
MorseEvent    queuePeek();
void          queuePop();
bool          queuePush(EventType t, unsigned long dur);
bool          encodeTextToQueue(const char* text);
void          startSweepTo(int target, bool isFirstLeg);
void          advanceMorse();
void          updateServo();
void          updateMorse();
void          handleSerial();
void          printStatus();

// ═══════════════════════════════════════════════════════════════════════════════
// 5. TIMING
// ═══════════════════════════════════════════════════════════════════════════════

void recomputeTiming() {
  dahMs       = ditMs * 3;
  intraCharMs = ditMs;
  interCharMs = ditMs * 3;
  interWordMs = ditMs * 7;
}

// ═══════════════════════════════════════════════════════════════════════════════
// 6. MORSE LOOKUP
// ═══════════════════════════════════════════════════════════════════════════════

const char* getMorse(char c) {
  if (c >= 'a' && c <= 'z') c -= 32;
  for (int i = 0; MORSE_TABLE[i].ch != '\0'; i++) {
    if (MORSE_TABLE[i].ch == c) return MORSE_TABLE[i].code;
  }
  return nullptr;
}

// ═══════════════════════════════════════════════════════════════════════════════
// 7. QUEUE
// ═══════════════════════════════════════════════════════════════════════════════

bool queueEmpty() { return qHead == qTail; }
bool queueFull()  { return ((qTail + 1) % QUEUE_SIZE) == qHead; }

MorseEvent queuePeek() { return morseQueue[qHead]; }
void       queuePop()  { qHead = (qHead + 1) % QUEUE_SIZE; }

bool queuePush(EventType t, unsigned long dur) {
  if (queueFull()) return false;
  morseQueue[qTail] = {t, dur};
  qTail = (qTail + 1) % QUEUE_SIZE;
  return true;
}

// ═══════════════════════════════════════════════════════════════════════════════
// 8. TEXT → QUEUE ENCODER
// ═══════════════════════════════════════════════════════════════════════════════

bool encodeTextToQueue(const char* text) {
  qHead = 0; qTail = 0;

  bool prevWasLetter = false;

  for (int i = 0; text[i] != '\0'; i++) {
    char c = text[i];

    if (c == ' ') {
      // Word gap = 7 units total. Inter-char (3 units) was already queued
      // after the last letter, so add 4 more to reach 7.
      if (prevWasLetter) {
        if (!queuePush(EV_WAIT, interWordMs - interCharMs)) return false;
      }
      prevWasLetter = false;
      continue;
    }

    const char* code = getMorse(c);
    if (code == nullptr) {
      Serial.print(F("[WARN] No Morse for: "));
      Serial.println(c);
      continue;
    }

    // 3-unit inter-character gap before this letter (not before first)
    if (prevWasLetter) {
      if (!queuePush(EV_WAIT, interCharMs)) return false;
    }

    // Encode each symbol
    for (int s = 0; code[s] != '\0'; s++) {
      // 1-unit intra-character gap between symbols (not before first)
      if (s > 0) {
        if (!queuePush(EV_WAIT, intraCharMs)) return false;
      }
      unsigned long dur = (code[s] == '-') ? dahMs : ditMs;
      if (!queuePush(EV_PRESS, dur)) return false;
    }

    prevWasLetter = true;
  }

  return true;
}

// ═══════════════════════════════════════════════════════════════════════════════
// 9. SERVO HELPER
// ═══════════════════════════════════════════════════════════════════════════════

void startSweepTo(int target, bool isFirstLeg) {
  targetPos = target;
  firstLeg  = isFirstLeg;
  sweeping  = true;
}

// ═══════════════════════════════════════════════════════════════════════════════
// 10. MORSE FSM — pull next event and act
// ═══════════════════════════════════════════════════════════════════════════════

void advanceMorse() {
  if (queueEmpty()) {
    morseState = MS_IDLE;
    Serial.println(F("[MORSE] Transmission complete"));
    printStatus();
    return;
  }

  MorseEvent ev = queuePeek();
  queuePop();

  if (ev.type == EV_PRESS) {
    // Store duration; timer starts on ARRIVAL at LO, not here
    morseEventDur = ev.durationMs;
    morseState    = MS_PRESSING;
    startSweepTo(ENDPOINT_LO, true);
  } else {
    morseEventStart = millis();
    morseEventDur   = ev.durationMs;
    morseState      = MS_WAITING;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 11. SETUP & LOOP
// ═══════════════════════════════════════════════════════════════════════════════

void setup() {
  Serial.begin(115200);
  recomputeTiming();

  servo.attach(SERVO_PIN);
  servo.write(currentPos);
  delay(500);

  Serial.println(F("=== Servo Morse Keyer Ready ==="));
  Serial.println(F("Commands:"));
  Serial.println(F("  M <text> — send text as Morse  (e.g. M SOS)"));
  Serial.println(F("  G        — single manual sweep"));
  Serial.println(F("  S <n>    — step size degrees   (default 5)"));
  Serial.println(F("  D <ms>   — step delay ms        (default 10)"));
  Serial.println(F("  T <ms>   — dit length ms        (default 67)"));
  Serial.println(F("  P        — print status"));
  printStatus();
}

void loop() {
  handleSerial();
  updateServo();
  updateMorse();
}

// ═══════════════════════════════════════════════════════════════════════════════
// 12. SERVO UPDATE
// ═══════════════════════════════════════════════════════════════════════════════

void updateServo() {
  if (!sweeping) return;

  unsigned long now = millis();
  if (now - lastStepTime < (unsigned long)stepDelayMs) return;
  lastStepTime = now;

  if (currentPos < targetPos)
    currentPos = min(currentPos + stepSize, targetPos);
  else if (currentPos > targetPos)
    currentPos = max(currentPos - stepSize, targetPos);

  servo.write(currentPos);

  if (currentPos == targetPos) {
    sweeping = false;

    if (firstLeg) {
      // Arrived at ENDPOINT_LO — start hold timer NOW
      if (morseState == MS_PRESSING) {
        morseEventStart = millis();   // ← timer starts here, after travel
        morseState      = MS_HOLDING;
      } else {
        // Manual G: return leg
        startSweepTo(ENDPOINT_HI, false);
      }
    } else {
      // Arrived back at ENDPOINT_HI
      if (morseState == MS_RELEASING) {
        advanceMorse();
      }
      // Manual G complete — nothing to do
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 13. MORSE FSM UPDATE
// ═══════════════════════════════════════════════════════════════════════════════

void updateMorse() {
  if (morseState == MS_IDLE) return;

  unsigned long now = millis();

  switch (morseState) {

    case MS_HOLDING:
      if (now - morseEventStart >= morseEventDur) {
        morseState = MS_RELEASING;
        startSweepTo(ENDPOINT_HI, false);
      }
      break;

    case MS_WAITING:
      if (now - morseEventStart >= morseEventDur) {
        advanceMorse();
      }
      break;

    default:
      break;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 14. SERIAL HANDLER
// ═══════════════════════════════════════════════════════════════════════════════

void handleSerial() {
  if (!Serial.available()) return;

  char cmd = Serial.read();

  switch (cmd) {

    case 'M': case 'm': {
      delay(20);
      char textBuf[128];
      int  idx = 0;
      if (Serial.available() && Serial.peek() == ' ') Serial.read();
      while (Serial.available() && idx < 127) {
        char ch = Serial.read();
        if (ch == '\n' || ch == '\r') break;
        textBuf[idx++] = ch;
      }
      textBuf[idx] = '\0';
      while (Serial.available()) Serial.read();

      if (idx == 0) {
        Serial.println(F("[ERR] No text. Usage: M HELLO WORLD"));
        break;
      }
      if (morseState != MS_IDLE) {
        Serial.println(F("[WARN] Busy — wait for transmission to finish"));
        break;
      }

      Serial.print(F("[MORSE] Encoding: "));
      Serial.println(textBuf);

      recomputeTiming();
      if (!encodeTextToQueue(textBuf)) {
        Serial.println(F("[ERR] Queue overflow — text too long"));
        break;
      }
      advanceMorse();
      break;
    }

    case 'G': case 'g': {
      if (sweeping || morseState != MS_IDLE) {
        Serial.println(F("[WARN] Busy — ignoring G"));
        break;
      }
      Serial.println(F("[GO] Manual sweep: 160° → 20° → 160°"));
      startSweepTo(ENDPOINT_LO, true);
      break;
    }

    case 'S': case 's': {
      int val = Serial.parseInt();
      if (val >= 1 && val <= 90) {
        stepSize = val;
        Serial.print(F("[CFG] Step size = ")); Serial.print(stepSize); Serial.println(F("°"));
      } else Serial.println(F("[ERR] Step size must be 1–90"));
      break;
    }

    case 'D': case 'd': {
      int val = Serial.parseInt();
      if (val >= 1 && val <= 5000) {
        stepDelayMs = val;
        Serial.print(F("[CFG] Step delay = ")); Serial.print(stepDelayMs); Serial.println(F(" ms"));
      } else Serial.println(F("[ERR] Delay must be 1–5000 ms"));
      break;
    }

    case 'T': case 't': {
      int val = Serial.parseInt();
      if (val >= 10 && val <= 2000) {
        ditMs = (unsigned long)val;
        recomputeTiming();
        Serial.print(F("[CFG] Dit=")); Serial.print(ditMs);
        Serial.print(F("ms  Dah=")); Serial.print(dahMs);
        Serial.print(F("ms  Intra=")); Serial.print(intraCharMs);
        Serial.print(F("ms  Inter=")); Serial.print(interCharMs);
        Serial.print(F("ms  Word=")); Serial.print(interWordMs);
        Serial.println(F("ms"));
      } else Serial.println(F("[ERR] Dit length must be 10–2000 ms"));
      break;
    }

    case 'P': case 'p': {
      printStatus();
      break;
    }

    case '\n': case '\r': case ' ':
      break;

    default:
      Serial.print(F("[ERR] Unknown command: "));
      Serial.println(cmd);
      break;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 15. STATUS
// ═══════════════════════════════════════════════════════════════════════════════

void printStatus() {
  Serial.println(F("─────────────────────────────────────"));
  Serial.print(F("  Position   : ")); Serial.print(currentPos);  Serial.println(F("°"));
  Serial.print(F("  Step size  : ")); Serial.print(stepSize);    Serial.println(F("°/tick"));
  Serial.print(F("  Step delay : ")); Serial.print(stepDelayMs); Serial.println(F(" ms/tick"));
  // Estimated sweep time for info
  unsigned long est = ((unsigned long)((ENDPOINT_HI - ENDPOINT_LO) / max(stepSize,1))) * (unsigned long)stepDelayMs;
  Serial.print(F("  Sweep time : ~")); Serial.print(est); Serial.println(F(" ms (travel overhead)"));
  Serial.print(F("  Dit        : ")); Serial.print(ditMs);       Serial.println(F(" ms"));
  Serial.print(F("  Dah        : ")); Serial.print(dahMs);       Serial.println(F(" ms"));
  Serial.print(F("  Intra-char : ")); Serial.print(intraCharMs); Serial.println(F(" ms"));
  Serial.print(F("  Inter-char : ")); Serial.print(interCharMs); Serial.println(F(" ms"));
  Serial.print(F("  Word gap   : ")); Serial.print(interWordMs); Serial.println(F(" ms"));
  Serial.print(F("  Morse state: "));
  switch (morseState) {
    case MS_IDLE:      Serial.println(F("IDLE"));      break;
    case MS_PRESSING:  Serial.println(F("PRESSING"));  break;
    case MS_HOLDING:   Serial.println(F("HOLDING"));   break;
    case MS_RELEASING: Serial.println(F("RELEASING")); break;
    case MS_WAITING:   Serial.println(F("WAITING"));   break;
  }
  Serial.print(F("  Queue depth: "));
  Serial.print((qTail - qHead + QUEUE_SIZE) % QUEUE_SIZE);
  Serial.println(F(" events"));
  Serial.println(F("─────────────────────────────────────"));
}