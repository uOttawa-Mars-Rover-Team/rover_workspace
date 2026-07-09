# AppMServo + AppGNC — full demonstration

**Branch:** `appgnc-mservo-thisoneplease` (from Sameed’s `c45e886` / `embedPIO_shield`)  
**What this is:** the layer that meshes operator/server strings with the working servo Driver/Task code on the GNC Mega.

For a compact command checklist only, see [`MSERVO_TEST.md`](MSERVO_TEST.md).

---

## 1. What we built (big picture)

```text
  Operator / Jetson / Serial Monitor
              |
              |  "SV;A;-1;1!"   (or "GNC;stop!" etc.)
              v
     ┌────────────────────┐
     │  AppGNC            │  reads until '!' on Serial (USB)
     │  (apps/AppGNC.cpp) │  AND Serial1 (inter-board)
     └─────────┬──────────┘
               │
       ┌───────┴────────┐
       │                │
   prefix SV;       prefix GNC;
       │                │
       v                v
 ┌───────────┐    existing GNC handlers
 │ AppMServo │    (move / stop / update)
 └─────┬─────┘
       │
       ├── Servo A  TaskServo (2 axes) → DriverServo pan + tilt
       ├── Servo B  TaskServo (1 axis) → DriverServo
       └── Servo C  TaskServo (1 axis) → DriverServo
```

| Layer | Files | Job |
|-------|--------|-----|
| **App** | `AppGNC.cpp`, `AppMServo.cpp` | Parse `!`-terminated messages; route `SV` vs `GNC` |
| **Task** | `TaskServo.cpp` | One mount = 1 or 2 axes; `move(dirs)` + `tick()` |
| **Driver** | `DriverServo.cpp` | One PWM axis; velocity `{-1,0,+1}`; clamp+lock at min/max |

**Not on this branch:** WASD keyboard push/release — that lives on `appgnc-mservo-testme`.

---

## 2. Message format

```text
SV;<id>;<v0>[;<v1>]!
```

| Field | Meaning |
|-------|---------|
| `SV` | Servo command identifier |
| `id` | Which mount: `A`, `B`, or `C` |
| `v0`, `v1` | Velocity directions: `-1` = toward min, `0` = stop, `+1` = toward max |
| `!` | Terminator (required) |

**Axis count:**

| id | Axes | Example |
|----|------|---------|
| **A** | 2 (pan, tilt) | `SV;A;-1;1!` → pan −1, tilt +1 |
| **B** | 1 | `SV;B;1!` |
| **C** | 1 | `SV;C;0!` |

Missing values default to `0` (stop). Extra junk after the expected count is ignored. Values outside `{-1,0,+1}` are clamped to that set.

**Also still supported (unchanged):**

```text
GNC;move;1!
GNC;move;-1!
GNC;stop!
GNC;update!
```

---

## 3. Hardware / pins (placeholders)

| Servo | Role | Pin(s) |
|-------|------|--------|
| A pan | 2-axis mount, axis 0 | **6** |
| A tilt | 2-axis mount, axis 1 | **7** |
| B | 1-axis | **8** |
| C | 1-axis | **9** |

| Port | Use | Baud |
|------|-----|------|
| **Serial** (USB 0/1) | Debug + type commands in Serial Monitor | 115200 |
| **Serial1** (18/19) | Same message set from RA / other board | 115200 |

Motion params (in `AppMServo.cpp`): min **0°**, max **180°**, start **90°**, step **2°**, step delay **15 ms**. End stops still **clamp and lock**.

---

## 4. Build, flash, open the demo

```bash
cd rover_workspace/rover_embedded_shield
~/.platformio/penv/bin/pio run -e AppGNC -t upload
~/.platformio/penv/bin/pio device monitor -b 115200
```

Click the monitor window so keystrokes go to the Mega.

**Boot banner you should see:**

```text
[MSERVO] Ready  A=2-axis  B=1-axis  C=1-axis
[MSERVO] msg: SV;<A|B|C>;<v>[;v]!   e.g. SV;A;-1;1!
[GNC] Online.
[GNC] Accepts GNC;...! and SV;...! on Serial (USB) and Serial1.
```

---

## 5. Scripted demo (type these in order)

After each line, wait a second or two and watch the physical servo(s) + the USB echo.

### Act 1 — Servo A, one axis at a time

| You type | What happens | Serial echo (approx.) |
|----------|--------------|------------------------|
| `SV;A;1;0!` | A pan moves toward max | `[GNC] USB: SV;A;1;0` then `[MSERVO] SV A  ax0=1  ax1=0` |
| `SV;A;0;0!` | A stops (hold) | `ax0=0  ax1=0` |
| `SV;A;-1;0!` | A pan toward min | `ax0=-1  ax1=0` |
| `SV;A;0;0!` | stop | |
| `SV;A;0;1!` | A tilt toward max | `ax0=0  ax1=1` |
| `SV;A;0;-1!` | A tilt toward min | `ax0=0  ax1=-1` |
| `SV;A;0;0!` | stop | |

### Act 2 — Servo A, both axes together

| You type | What happens |
|----------|--------------|
| `SV;A;-1;1!` | pan min + tilt max (the example from the design) |
| `SV;A;1;-1!` | pan max + tilt min |
| `SV;A;1;1!` | both toward max |
| `SV;A;-1;-1!` | both toward min |
| `SV;A;0;0!` | both stop |

### Act 3 — Servo B and C (1-axis)

| You type | What happens |
|----------|--------------|
| `SV;B;1!` | B toward max |
| `SV;B;-1!` | B toward min |
| `SV;B;0!` | B stop |
| `SV;C;1!` | C toward max |
| `SV;C;-1!` | C toward min |
| `SV;C;0!` | C stop |

### Act 4 — Targeting (only the named servo moves)

1. Start A moving: `SV;A;1;0!`
2. Start B moving: `SV;B;-1!`
3. Stop only A: `SV;A;0;0!` → B should keep moving
4. Stop B: `SV;B;0!`

This is the point of `SV;<id>;…` — not every servo moves on every message.

### Act 5 — End-stop clamp + lock

1. `SV;A;1;0!` and leave it until pan hits **180°** — motion should stop by itself (lock).
2. `SV;A;-1;0!` until **0°** — same at min.
3. Optional: same idea with `SV;B;1!` / `SV;C;-1!`.

### Act 6 — Errors / ignore paths

| You type | Expected |
|----------|----------|
| `SV;Z;1!` | `[MSERVO] SV: unknown servo Z` |
| `SV;A!` | treated as stop (`0,0`) |
| `FOO;bar!` | `[GNC] Ignored (not GNC; or SV;)` |
| `GNC;stop!` | `[GNC] Stopped` (GNC path still works) |

### Act 7 — Serial1 (optional)

Send the **same** strings on Serial1 (from RA or a second UART). USB monitor should show:

```text
[GNC] Serial1: SV;A;-1;1
[MSERVO] SV A  ax0=-1  ax1=1
```

instead of `[GNC] USB: …`.

---

## 6. Complete command cheat sheet

### SV — Servo A (2-axis)

```text
SV;A;-1;0!
SV;A;1;0!
SV;A;0;-1!
SV;A;0;1!
SV;A;-1;-1!
SV;A;-1;1!
SV;A;1;-1!
SV;A;1;1!
SV;A;0;0!
```

### SV — Servo B / C (1-axis)

```text
SV;B;-1!
SV;B;1!
SV;B;0!
SV;C;-1!
SV;C;1!
SV;C;0!
```

### GNC (regression)

```text
GNC;move;1!
GNC;move;-1!
GNC;stop!
GNC;update!
```

---

## 7. File map (where to look)

```text
rover_embedded_shield/
  include/
    AppGNC.h
    AppMServo.h
    DriverServo.h
    TaskServo.h
  src/
    main.cpp                 # picks AppGNC via -D APP_GNC
    apps/AppGNC.cpp          # ! reader + SV/GNC dispatch
    apps/AppMServo.cpp       # A/B/C + SV parse + tick
    drivers/DriverServo.cpp
    tasks/TaskServo.cpp
  platformio.ini             # env:AppGNC includes AppMServo + servo sources
  MSERVO_DEMO.md             # this file
  MSERVO_TEST.md             # short test tables
```

---

## 8. Related branches

| Branch | Purpose |
|--------|---------|
| `appgnc-mservo-thisoneplease` | **This demo** — string `SV;…!` into AppGNC |
| `appgnc-mservo-testme` | Keyboard WASD push/release bench (no AppGNC) |
| `mservo` | Earlier flat DriverServo/TaskServo WIP |
| `embedPIO_shield` @ `c45e886` | Sameed’s AppRA / AppGNC base |
