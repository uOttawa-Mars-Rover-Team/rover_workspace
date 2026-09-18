# Rover Teleop — Laptop Operator Guide

Control the uOttawa Mars Rover from your laptop over Radios using our GameSir Nova Lite (or other) gamepad.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [First-Time Setup](#first-time-setup)
3. [Daily Operation](#daily-operation)
4. [Controls Reference](#controls-reference)
5. [Known Issue: Phantom Joystick on Jetson](#known-issue-phantom-joystick-on-jetson)
6. [Troubleshooting](#troubleshooting)
7. [Quick Reference Card](#quick-reference-card)

---

## Prerequisites

### Hardware
- Laptop running **Ubuntu 22.04**
- GameSir Nova Lite gamepad (or any USB/Bluetooth controller)
- Radio connection on the **same network** as the rover's Jetson (`192.168.1.XXX`)

### Software
- The `rover_workspace` repository cloned and built (with full_setup.sh)

### Network
- Rover Jetson must be reachable at `192.168.1.201`

---

## First-Time Setup

### 1. Clone and build the workspace

```bash
cd ~/rover_workspace
colcon build
--symlink-install
```

### 2. Source the workspace

Add to your `~/.bashrc` (recommended):

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "source ~/rover_workspace/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### 3. Verify controller is detected

Plug in / pair your gamepad, then:

```bash
ls /dev/input/js*
# Should show /dev/input/js0
```

Optional test:

```bash
sudo apt install joystick
jstest /dev/input/js0
# Move sticks and press buttons — values should change
```

### 4. (Optional) Add the `killjoy` alias

You will need this before every session (for now). Add to `~/.bashrc`:

```bash
alias killjoy='ssh roverpc@192.168.1.201 "pkill -f joy_node; pkill -f teleop_twist_joy"'
```

Then reload:

```bash
source ~/.bashrc
```

---

## Daily Operation

### Step 1 — Turn on the rover
### Step 2 — Kill the phantom joystick nodes on the Jetson

> **This is required every time the rover boots.** See [Known Issue](#known-issue-phantom-joystick-on-jetson) for why.

```bash
ssh roverpc@192.168.1.201 
pkill -f joy_node; 
pkill -f teleop_twist_joy
```

Or, if you set up the alias:

```bash
killjoy
```

No output is expected — that means it worked.

### Step 3 — Launch the teleop controller

```bash
ros2 launch chassis_controls controller.launch.py
```

A TUI (text interface) will take over your terminal showing:

- Jetson connection status (green / red)
- Current speed and turn settings
- Live trigger and stick values
- Button states
- Rover live / disabled status

### Step 4 — Drive

Hold **LB (safety button)**, then use the triggers and left stick. See [Controls Reference](#controls-reference).

### Step 5 — Shut down

Press **Ctrl+C** in the terminal. Both the controller and `joy_node` shut down cleanly.

---

## Controls Reference

### Driving (requires LB held as safety)

| Input | Action |
| --- | --- |
| **LB (hold)** | Safety enable — must be held for rover to move |
| **RT** | Drive forward (variable speed) |
| **LT** | Drive backward (variable speed) |
| **Left Stick X** | Turn left / right |

### Speed & Turn Rate Adjustment

| Input | Action |
| --- | --- |
| **A (hold) + D-pad Up** | Increase max speed (+0.1 m/s) |
| **A (hold) + D-pad Down** | Decrease max speed (−0.1 m/s) |
| **X (hold) + D-pad Right** | Increase turn rate (+0.05 rad/s) |
| **X (hold) + D-pad Left** | Decrease turn rate (−0.05 rad/s) |

### Servo Movement

| Input | Action |
| --- | --- |
| **D-pad** (when A / X not held) | Servo A control — publishes `SV;A;x;y!` |
| **Right Stick** | Servo B control — publishes `SV;B;x;y!` |

Commands are only sent on state change to reduce topic spam.

### Defaults

- Max speed: **0.7 m/s** (adjustable 0.1 – 2.0)
- Turn rate: **0.4 rad/s** (adjustable 0.1 – 1.5)

### Topics Published

| Topic | Type | Purpose |
| --- | --- | --- |
| `/cmd_vel_teleop` | `geometry_msgs/Twist` | Drive commands (consumed by `twist_mux`) |
| `/arm_cmd` | `std_msgs/String` | Arm servo commands |

---

## Known Issue: Phantom Joystick on Jetson

### The Problem

The Jetson's startup service (`rover.launch.py`) also launches its own `joy_node` and `teleop_twist_joy`, intended for a locally-plugged gamepad as a backup if Wi-Fi dies.

Because no gamepad is actually plugged into the Jetson, this phantom `joy_node` publishes a stream of **zero-valued `/joy` messages** at 20 Hz.

Since ROS 2 auto-discovers nodes across the network, your laptop's `controller.py` receives **both** streams — its own real gamepad data **and** the Jetson's zero-filled phantom stream — causing severe input jitter and inaccurate control.

### The Workaround (current)

Kill the phantom nodes on every rover boot:

```bash
pkill -f joy_node 
pkill -f teleop_twist_joy
```

This does **not** stop the rover's other services — motors, controllers, and `twist_mux` all keep running.

### Verify it worked

```bash
ros2 topic info /joy --verbose
# Publisher count should be 1 (your laptop only)
```

### Long-Term Fix (planned, not yet implemented)

Namespace the two `joy_node`s (`/laptop/joy` and `/jetson/joy`) and configure `twist_mux` priorities so both can coexist:

- Laptop teleop → `cmd_vel_teleop`, priority **100**, timeout **0.5 s**
- Jetson-local pad → `cmd_vel_local`, priority **90**, timeout **0.5 s**
- Autonomous → `cmd_vel_autonomous`, priority **20**, timeout **2.0 s**

This gives automatic failover: if Wi-Fi drops, the laptop times out after 0.5 s and the Jetson-plugged pad takes over. If neither is active, the rover stops.

---

## Troubleshooting

### `Package 'chassis_controls' not found`

You didn't source the workspace:

```bash
source ~/rover_workspace/install/setup.bash
```

### `executable 'controller.py' not found`

The build didn't include the script. Rebuild:

```bash
cd ~/rover_workspace
colcon build --packages-select chassis_controls --symlink-install
source install/setup.bash
```

### TUI shows "JETSON: NOT CONNECTED" (red)

- Check ping: `ping 192.168.1.201`
- Confirm both machines are on the same Wi-Fi network
- Verify domain ID on both: `echo $ROS_DOMAIN_ID` (should be `0`)

### Rover jitters, jumps, or doesn't respond correctly

You skipped Step 2. Kill the phantom nodes:

```bash
ssh roverpc@192.168.1.201
pkill -f joy_node
 pkill -f teleop_twist_joy
```

### TUI shows "Waiting for controller input ..."

- Is the gamepad powered on?
- Press any button to wake it up
- Check `ls /dev/input/js*`
- Try unplugging / re-pairing

### Rover moves but commands feel weak or overridden

Another source may be winning at `twist_mux`. Check active publishers:

```bash
ros2 topic info /diff_cont/cmd_vel_unstamped --verbose
```

Contact a team lead if an unexpected source is present.

### Ctrl+C doesn't fully stop everything

```bash
pkill -f joy_node
pkill -f controller.py
```

### `Permission denied` on `/dev/input/js0`

Add your user to the `input` group, then log out and back in:

```bash
sudo usermod -aG input $USER
```

---

## Quick Reference Card

```text
BOOT-UP CHECKLIST
─────────────────
1. Power on rover                → wait 30s
2. ping 192.168.1.201            → confirm reachable
3. killjoy                       → remove joy nodes
4. ros2 launch chassis_controls controller.launch.py
5. Hold LB + drive
6. Ctrl+C when done
```

```text
CONTROLS
────────
LB (hold)          Safety enable — REQUIRED to move
RT / LT            Forward / Reverse
Left Stick X       Turn
A + D-pad U/D      Speed  +/- 0.1 m/s
X + D-pad L/R      Turn   +/- 0.05 rad/s
D-pad              Arm A
Right Stick        Arm B
```


---

_Last updated: July 2026_