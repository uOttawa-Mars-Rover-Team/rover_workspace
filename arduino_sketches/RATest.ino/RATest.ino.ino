// ============================================================
// RA_Mega.ino  —  Father device (Arduino Mega)
// ------------------------------------------------------------
// Wiring:
//   Mega TX3 (pin 14)  →  Uno RX  (pin 0)
//   Mega RX3 (pin 15)  ←  Uno TX  (pin 1)
//   Common GND
//
// Serial0 (USB)  : user / ROS terminal  @ 115200
// Serial3        : inter-board link     @ 115200
//
// Message format:
//   "RA;message\n"   → handled by this Mega
//   "GNC;message\n"  → forwarded to Uno over Serial3
//
// The Mega also listens on Serial3 for replies from the Uno
// and prints them straight to Serial0 (the user terminal).
// ============================================================

// ---------- per-character accumulator (USB side) ----------
static char  usbBuf[64];
static uint8_t usbIdx = 0;
static bool  usbReady = false;

// ---------- per-character accumulator (inter-board side) --
static char  boardBuf[64];
static uint8_t boardIdx = 0;
static bool  boardReady = false;

// ----------------------------------------------------------
void setup() {
    Serial.begin(115200);   // USB  → user / ROS
    Serial3.begin(115200);  // UART → Uno

    Serial.println("[MEGA] Online. Send RA;<msg> or GNC;<msg>");
}

// ----------------------------------------------------------
void loop() {

    // 1. Accumulate chars from USB (user / ROS)
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n' || c == '\r') {
            if (usbIdx > 0) {               // ignore blank lines
                usbBuf[usbIdx] = '\0';
                usbIdx   = 0;
                usbReady = true;
            }
        } else if (usbIdx < sizeof(usbBuf) - 1) {
            usbBuf[usbIdx++] = c;
        }
    }

    // 2. Handle completed USB message
    if (usbReady) {
        usbReady = false;
        handleUSBMessage(usbBuf);
    }

    // 3. Accumulate chars from Uno (Serial3)
    while (Serial3.available()) {
        char c = Serial3.read();
        if (c == '\n' || c == '\r') {
            if (boardIdx > 0) {
                boardBuf[boardIdx] = '\0';
                boardIdx   = 0;
                boardReady = true;
            }
        } else if (boardIdx < sizeof(boardBuf) - 1) {
            boardBuf[boardIdx++] = c;
        }
    }

    // 4. Propagate Uno reply to user terminal
    if (boardReady) {
        boardReady = false;
        Serial.print("[GNC→MEGA] ");
        Serial.println(boardBuf);
    }
}

// ----------------------------------------------------------
// Route a fully-received USB message
// ----------------------------------------------------------
void handleUSBMessage(const char* msg) {

    // Expect "PREFIX;payload"
    // Find the first ';'
    const char* sep = strchr(msg, ';');
    if (sep == NULL) {
        Serial.println("[MEGA] Malformed message (no ';')");
        return;
    }

    // Extract prefix length
    uint8_t prefixLen = sep - msg;

    // ---- RA → this Mega handles it ----
    if (prefixLen == 2 && strncmp(msg, "RA", 2) == 0) {
        const char* payload = sep + 1;
        Serial.print("[MEGA] Handling locally: ");
        Serial.println(payload);

        // TODO: plug robotArm.parseMessage(payload) here
        // noInterrupts();
        // robotArm.parseMessage(payload);
        // interrupts();
    }

    // ---- GNC → forward to Uno over Serial3 ----
    else if (prefixLen == 3 && strncmp(msg, "GNC", 3) == 0) {
        Serial.print("[MEGA] Forwarding to GNC: ");
        Serial.println(msg);          // echo so user knows it was routed
        Serial3.print(msg);           // forward the FULL original string
        Serial3.print('\n');
    }

    else {
        Serial.print("[MEGA] Unknown prefix: ");
        Serial.println(msg);
    }
}
