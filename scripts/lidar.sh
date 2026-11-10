#!/bin/bash
#
# Single entry point for the LiDAR: installs what is missing, enforces the
# frozen sensor profile, then launches the driver.
#
#   ./lidar.sh              Install if needed, apply config, launch driver
#   ./lidar.sh --check      Install if needed, apply config, print it, no launch
#   ./lidar.sh --bench      Launch and print rate + bandwidth after 8 s
#   ./lidar.sh --stop       Put the sensor in STANDBY (stops motor/laser)
#   ./lidar.sh --reinstall  Force the driver install/pin to run again
#
# The install step is skipped automatically once the pinned driver is present,
# so normal runs start in a couple of seconds.
#
# The sensor config below is the single source of truth for the whole team.
# Settings are written to the sensor's flash with persist=true, so they survive
# power cycles and apply to every laptop and to the Jetson. The script still
# re-checks them on every run, so a sensor someone changed in Ouster Studio
# gets corrected automatically.
#
# Only differing keys are written. If the sensor already matches, nothing is
# sent and the sensor does not reinitialise -- that matters, because a sensor
# reinitialisation takes 15-30 s, which is longer than the driver's retry
# budget, and the driver drops into an endless self-reset loop if it starts
# polling too early.

set -e

complete() { echo -e "\e[1m\e[32mComplete.\e[0m\n"; }
title() { echo -e "\e[1m\e[44m $1 \e[0m"; }
warn() { echo -e "\e[1m\e[33m$1\e[0m"; }
fail() { echo -e "\e[1m\e[31m$1\e[0m"; exit 1; }

# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------
SENSOR_IP=${SENSOR_IP:-192.168.1.202}   # static IP set in Ouster Studio
HOST_IP=${HOST_IP:-192.168.1.111}       # this machine's IP on the LiDAR adapter
LIDAR_PORT=${LIDAR_PORT:-7502}
IMU_PORT=${IMU_PORT:-7503}

# ---------------------------------------------------------------------------
# Frozen sensor profile -- one profile for every consumer, every mission.
#
#   udp_profile_lidar   8 bytes/point instead of 16. Drops the SIGNAL field and
#                       range precision goes 19->15 bit (~8 mm, ~260 m ceiling).
#                       Neither matters for obstacles or SLAM.
#   lidar_mode          Columns per rotation x rotation rate.
#   azimuth_window      Kept at the full 360 deg on purpose. SLAM/LiDAR odometry
#                       needs the whole ring to match scans reliably, and GPS is
#                       banned in Meteorite Search. The forward-only crop for
#                       obstacle avoidance happens in software, in the terrain
#                       node, where it costs nothing.
#   columns_per_packet  Larger packets = fewer syscalls per frame.
#
# Override per run without editing the file, e.g.
#   LIDAR_MODE=512x10 ./lidar.sh --bench
# ---------------------------------------------------------------------------
UDP_PROFILE=${UDP_PROFILE:-RNG15_RFL8_NIR8}
LIDAR_MODE=${LIDAR_MODE:-1024x10}
AZIMUTH_MIN=${AZIMUTH_MIN:-0}
AZIMUTH_MAX=${AZIMUTH_MAX:-360000}
COLUMNS_PER_PACKET=${COLUMNS_PER_PACKET:-16}

# ---------------------------------------------------------------------------
# Driver-side point type (not a sensor setting).
#
# The default 'original' carries x,y,z,intensity,t,reflectivity,ring,ambient,
# range = 48 bytes per point. It needs the SIGNAL field, so it is NOT
# compatible with RNG15_RFL8_NIR8 -- and neither are 'xyzi' / 'xyzir', whose
# intensity also comes from SIGNAL.
#
# Compatible with RNG15_RFL8_NIR8:
#   xyz     16 bytes/point, geometry only            <- default
#   native  the profile's own fields (range, reflectivity, near-IR)
#
# Switch to 'native' if a SLAM package you adopt wants reflectivity for
# scan matching. Nothing in the obstacle or terrain path reads intensity.
# ---------------------------------------------------------------------------
POINT_TYPE=${POINT_TYPE:-xyz}

# Drop no-return points instead of publishing them as NaN placeholders.
# An organized cloud keeps every beam x column slot whether or not it saw
# anything, so on open terrain most of the message is padding.
ORGANIZED=${ORGANIZED:-false}

# Clip by distance before the cloud is published.
#   min: ignore returns off the rover's own chassis
#   max: CIRC obstacle avoidance does not need returns past ~30 m, and the
#        existing laserscan config already caps at 20 m
MIN_RANGE=${MIN_RANGE:-0.5}
MAX_RANGE=${MAX_RANGE:-30.0}

# Vertical beam reduction {1,2,4,8,16}. Left at 1 deliberately: the OS0-32
# spreads 32 beams over 90 deg (2.8 deg apart), so v_reduction=2 gives 5.6 deg,
# about 1 m vertical gaps at 10 m -- enough to miss a knee-high rock. It also
# decimates uniformly, including the narrow band we care about. Prefer
# mask_path to drop the sky and under-wheel bands at full resolution.
V_REDUCTION=${V_REDUCTION:-1}

# ---------------------------------------------------------------------------
# Driver pin
#
# Driver 0.16.x expects a 'WINDOW' field in each LidarScan that our OS-0-32
# firmware 2.5.3 does not send, and crashes on the first scan with:
#     terminate called after throwing an instance of 'std::out_of_range'
#       what():  Field 'WINDOW' not found in LidarScan.
# Remove the pin only after the sensor firmware has been upgraded.
# ---------------------------------------------------------------------------
ROS_DISTRO_NAME=${ROS_DISTRO_NAME:-jazzy}
OUSTER_VERSION=0.14.1
SNAPSHOT=http://snapshots.ros.org/jazzy/2026-06-18/ubuntu/pool/main/r
RMEM_TARGET=26214400

API="http://${SENSOR_IP}/api/v1/sensor"
mode=${1:-run}

# ===========================================================================
# 0. STANDBY shortcut -- no install or config needed
# ===========================================================================
if [ "$mode" = "--stop" ]; then
    title "Putting sensor in STANDBY"
    curl -s -X POST "${API}/config" -H 'Content-Type: application/json' \
        -d '{"operating_mode": "STANDBY"}' >/dev/null
    complete
    exit 0
fi

title "----- LiDAR bring-up -----"

# ===========================================================================
# 1. Install, only if something is actually missing
# ===========================================================================
driver_ok() {
    dpkg-query -W -f='${Version}' "ros-${ROS_DISTRO_NAME}-ouster-ros" 2>/dev/null \
        | grep -q "^${OUSTER_VERSION}"
}

if [ "$mode" = "--reinstall" ] || ! driver_ok; then
    title "Installing LiDAR packages (first run on this machine)"

    sudo apt-get update
    sudo apt-get install -y \
        wget curl iproute2 tcpdump \
        ros-${ROS_DISTRO_NAME}-ouster-ros \
        ros-${ROS_DISTRO_NAME}-pointcloud-to-laserscan \
        ros-${ROS_DISTRO_NAME}-slam-toolbox \
        ros-${ROS_DISTRO_NAME}-navigation2 \
        ros-${ROS_DISTRO_NAME}-nav2-bringup \
        ros-${ROS_DISTRO_NAME}-rviz2

    echo "Pinning ouster-ros to ${OUSTER_VERSION} (firmware 2.5.3 compatibility)"
    sudo apt-mark unhold ros-${ROS_DISTRO_NAME}-ouster-ros \
                         ros-${ROS_DISTRO_NAME}-ouster-sensor-msgs 2>/dev/null || true

    TMP=$(mktemp -d)
    wget -q -P "$TMP" \
        "${SNAPSHOT}/ros-jazzy-ouster-sensor-msgs/ros-jazzy-ouster-sensor-msgs_${OUSTER_VERSION}-2noble.20260615.114154_amd64.deb"
    wget -q -P "$TMP" \
        "${SNAPSHOT}/ros-jazzy-ouster-ros/ros-jazzy-ouster-ros_${OUSTER_VERSION}-2noble.20260615.151812_amd64.deb"
    sudo apt-get install -y --allow-downgrades \
        "$TMP"/ros-jazzy-ouster-sensor-msgs_*.deb \
        "$TMP"/ros-jazzy-ouster-ros_*.deb
    sudo apt-mark hold ros-${ROS_DISTRO_NAME}-ouster-ros \
                       ros-${ROS_DISTRO_NAME}-ouster-sensor-msgs
    rm -rf "$TMP"
    complete

    if [ "$mode" = "--reinstall" ]; then
        title "REINSTALL COMPLETE"
        exit 0
    fi
fi

# ===========================================================================
# 2. UDP receive buffers
#
# The sensor bursts a whole frame at once. Default buffers are far too small
# and the kernel silently drops packets, which shows up as a low
# /sensor_msgs/PointCloud2 rate (e.g. 4.7 Hz instead of 10).
# ===========================================================================
CUR_RMEM=$(cat /proc/sys/net/core/rmem_max 2>/dev/null || echo 0)
if [ "$CUR_RMEM" -lt "$RMEM_TARGET" ]; then
    warn "Raising UDP receive buffers (${CUR_RMEM} -> ${RMEM_TARGET})"
    sudo sysctl -w net.core.rmem_max=${RMEM_TARGET} >/dev/null
    sudo sysctl -w net.core.rmem_default=${RMEM_TARGET} >/dev/null
    echo "This lasts until reboot. To persist, add both lines to"
    echo "/etc/sysctl.conf on the HOST (the WSL distro, not the container)."
    echo
fi

# ===========================================================================
# 3. Reach the sensor
# ===========================================================================
echo "Sensor:  ${SENSOR_IP}"
echo "Host IP: ${HOST_IP}"

CURRENT=$(curl -s -m 5 --noproxy '*' "${API}/config" || true)
if ! printf '%s' "$CURRENT" | python3 -c 'import json,sys; json.load(sys.stdin)' 2>/dev/null; then
    fail "Cannot reach the sensor at ${SENSOR_IP}, or it did not return valid JSON.
  - Is the LiDAR powered (24 V adapter) and the cable locked, red line up?
  - Does this machine have ${HOST_IP}/24 on the LiDAR adapter?
      Linux:    ip -4 addr show
      Windows:  Get-NetIPAddress -AddressFamily IPv4
  - If using a USB-Ethernet converter, remember it is a SEPARATE adapter and
    needs its own static IP; the built-in port's IP does not carry over.
  - Close Ouster Studio, it competes for the sensor."
fi
echo "Sensor reachable."
complete

# ===========================================================================
# 4. Enforce the frozen profile (writing only what differs)
# ===========================================================================
title "Applying frozen sensor profile"

DESIRED=$(cat <<JSON
{
  "operating_mode": "NORMAL",
  "udp_profile_lidar": "${UDP_PROFILE}",
  "lidar_mode": "${LIDAR_MODE}",
  "azimuth_window": [${AZIMUTH_MIN}, ${AZIMUTH_MAX}],
  "columns_per_packet": ${COLUMNS_PER_PACKET},
  "udp_dest": "${HOST_IP}",
  "udp_port_lidar": ${LIDAR_PORT},
  "udp_port_imu": ${IMU_PORT}
}
JSON
)

DIFF=$(python3 -c '
import json, sys
current = json.loads(sys.argv[1])
desired = json.loads(sys.argv[2])
delta = {k: v for k, v in desired.items() if current.get(k) != v}
for k, v in delta.items():
    print(f"  {k}: {current.get(k)!r} -> {v!r}", file=sys.stderr)
print(json.dumps(delta))
' "$CURRENT" "$DESIRED")

if [ "$DIFF" = "{}" ]; then
    echo "Sensor already matches the frozen profile. Nothing to change."
    complete
else
    warn "Writing changes to sensor flash (persist=true)..."
    curl -s -X POST "${API}/config?persist=true" \
        -H 'Content-Type: application/json' -d "$DIFF" >/dev/null \
        || fail "Sensor rejected the config. Check the values above."

    echo -n "Waiting for the sensor to reinitialise"
    STATUS=""
    for _ in $(seq 1 40); do
        sleep 2
        echo -n "."
        STATUS=$(curl -s -m 3 --noproxy '*' "${API}/metadata/sensor_info" \
                 | python3 -c 'import json,sys; print(json.load(sys.stdin).get("status",""))' \
                 2>/dev/null || echo "")
        if [ "$STATUS" = "RUNNING" ]; then break; fi
    done
    echo
    if [ "$STATUS" != "RUNNING" ]; then
        fail "Sensor did not return to RUNNING in 80 s."
    fi
    complete
fi

# ===========================================================================
# 5. Show what we ended up with
# ===========================================================================
title "Active sensor config"
curl -s --noproxy '*' "${API}/config" | python3 -c '
import json, sys
c = json.load(sys.stdin)
for k in ["operating_mode", "lidar_mode", "udp_profile_lidar", "azimuth_window",
          "columns_per_packet", "udp_dest", "udp_port_lidar", "udp_port_imu"]:
    print(f"  {k:22} {c.get(k)}")
'
echo

if [ "$mode" = "--check" ]; then
    title "CHECK ONLY -- not launching."
    exit 0
fi

# ===========================================================================
# 6. Launch
# ===========================================================================
if [ -z "${ROS_DISTRO:-}" ]; then
    # shellcheck disable=SC1090
    source "/opt/ros/${ROS_DISTRO_NAME}/setup.bash"
fi

LAUNCH_ARGS=(
    sensor_hostname:="${SENSOR_IP}"
    udp_dest:="${HOST_IP}"
    lidar_port:="${LIDAR_PORT}"
    imu_port:="${IMU_PORT}"
    proc_mask:=PCL
    viz:=false
    point_type:="${POINT_TYPE}"
    organized:="${ORGANIZED}"
    min_range:="${MIN_RANGE}"
    max_range:="${MAX_RANGE}"
    v_reduction:="${V_REDUCTION}"
)

echo "Driver args: point_type=${POINT_TYPE} organized=${ORGANIZED}" \
     "min_range=${MIN_RANGE} max_range=${MAX_RANGE} v_reduction=${V_REDUCTION}"
echo

if [ "$mode" = "--bench" ]; then
    BENCH_SECONDS=${BENCH_SECONDS:-30}
    title "Benchmarking (${BENCH_SECONDS}s)"

    # Start the measurement subscribers FIRST, before the driver exists.
    # They then discover the publisher the moment it appears. Starting them
    # after the driver means racing DDS discovery, which intermittently
    # reports "topic does not appear to be published yet".
    ros2 topic hz /sensor_msgs/PointCloud2 > /tmp/lidar_bench_hz.log 2>&1 &
    HZ_PID=$!
    ros2 topic bw /sensor_msgs/PointCloud2 > /tmp/lidar_bench_bw.log 2>&1 &
    BW_PID=$!

    ros2 launch ouster_ros sensor.launch.xml "${LAUNCH_ARGS[@]}" \
        > /tmp/lidar_bench_driver.log 2>&1 &
    DRIVER_PID=$!

    cleanup() {
        kill $HZ_PID $BW_PID 2>/dev/null || true
        kill $DRIVER_PID 2>/dev/null || true
        wait $DRIVER_PID 2>/dev/null || true
    }
    trap cleanup EXIT

    echo -n "Collecting"
    for _ in $(seq 1 "$BENCH_SECONDS"); do
        sleep 1
        echo -n "."
        if ! kill -0 "$DRIVER_PID" 2>/dev/null; then
            echo
            warn "Driver exited early. Last lines of its log:"
            tail -20 /tmp/lidar_bench_driver.log
            exit 1
        fi
    done
    echo
    echo

    title "Rate"
    tail -4 /tmp/lidar_bench_hz.log

    title "Bandwidth"
    tail -4 /tmp/lidar_bench_bw.log

    if grep -q "does not appear to be published" /tmp/lidar_bench_hz.log; then
        echo
        warn "Nothing was published. Relevant driver log lines:"
        grep -iE "warn|error|not compatible" /tmp/lidar_bench_driver.log | tail -20
        warn "If the point type is not compatible with the udp profile,
try POINT_TYPE=xyz or POINT_TYPE=native."
    fi

    echo
    echo "Logs: /tmp/lidar_bench_{hz,bw,driver}.log"
    exit 0
fi

title "Launching driver"
exec ros2 launch ouster_ros sensor.launch.xml "${LAUNCH_ARGS[@]}"
