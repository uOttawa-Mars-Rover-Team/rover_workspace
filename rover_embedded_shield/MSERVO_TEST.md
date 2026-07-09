# AppGNC + AppMServo — how to test

For the full walkthrough (architecture, scripted demo acts, expected echoes), see [`MSERVO_DEMO.md`](MSERVO_DEMO.md).

Branch: `appgnc-mservo-thisoneplease`  
Board: Mega 2560 (GNC env)  
Baud: **115200**  
Terminator: **`!`** (required). Serial Monitor may also send `\n` — that is ignored.

## Build / upload / monitor

```bash
cd rover_workspace/rover_embedded_shield
~/.platformio/penv/bin/pio run -e AppGNC -t upload
~/.platformio/penv/bin/pio device monitor -b 115200
```

Click into the serial monitor so typed commands go to the Mega.

**Pins (placeholders until wiring is confirmed):**

| Servo | Axes | Pins |
|-------|------|------|
| **A** | 2 (pan, tilt) | pan **6**, tilt **7** |
| **B** | 1 | **8** |
| **C** | 1 | **9** |

Values are velocity directions: **`-1`** toward min, **`+1`** toward max, **`0`** stop (hold). Hitting min/max still clamps and locks that axis.

---

## USB Serial (bench — type these)

### Servo A (2-axis) — all direction combos

| Command | Expected |
|---------|----------|
| `SV;A;-1;0!` | pan toward min, tilt stop |
| `SV;A;1;0!` | pan toward max, tilt stop |
| `SV;A;0;-1!` | pan stop, tilt toward min |
| `SV;A;0;1!` | pan stop, tilt toward max |
| `SV;A;-1;-1!` | pan min + tilt min |
| `SV;A;-1;1!` | pan min + tilt max |
| `SV;A;1;-1!` | pan max + tilt min |
| `SV;A;1;1!` | pan max + tilt max |
| `SV;A;0;0!` | both axes stop (hold) |

### Servo B (1-axis)

| Command | Expected |
|---------|----------|
| `SV;B;-1!` | B toward min |
| `SV;B;1!` | B toward max |
| `SV;B;0!` | B stop |

### Servo C (1-axis)

| Command | Expected |
|---------|----------|
| `SV;C;-1!` | C toward min |
| `SV;C;1!` | C toward max |
| `SV;C;0!` | C stop |

### End-stop check

1. Send `SV;A;1;0!` and hold until pan reaches max — should **clamp and lock** (stop advancing).
2. Send `SV;A;-1;0!` until min — same lock at min.
3. Repeat for tilt with `SV;A;0;1!` / `SV;A;0;-1!`, and for B/C with `SV;B;1!` / `SV;B;-1!` etc.

### Negative / error cases

| Command | Expected |
|---------|----------|
| `SV;Z;1!` | `[MSERVO] SV: unknown servo Z` |
| `SV;A!` | missing values → treated as `0,0` (stop) |
| `GNC;stop!` | still works (existing GNC handler) |
| `FOO;bar!` | `[GNC] Ignored (not GNC; or SV;)` |

---

## Serial1 (inter-board / from RA)

Same strings as above, but sent on **Serial1** (pins 18/19) from the RA Mega or a second UART.

Example from RA side (if forwarding): send the raw payload including terminator, e.g. `SV;A;-1;1!`.

On the GNC USB monitor you should see:

```text
[GNC] Serial1: SV;A;-1;1
[MSERVO] SV A  ax0=-1  ax1=1
```

USB-typed commands show `[GNC] USB: ...` instead.

---

## Existing GNC messages (regression)

Still accepted on both ports:

| Command | Expected |
|---------|----------|
| `GNC;move;1!` | Moving forward |
| `GNC;move;-1!` | Moving reverse |
| `GNC;stop!` | Stopped |
| `GNC;update!` | status reply on Serial1 |

---

## Keyboard push/release bench (separate)

The WASD hold/release demo lives on branch **`appgnc-mservo-testme`**, not this branch. This branch is **string-only** (`SV;…!`).
