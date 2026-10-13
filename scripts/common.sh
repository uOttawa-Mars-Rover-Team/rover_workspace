#!/bin/bash

# Shared helpers for the setup scripts. Source this file, do not execute it.

complete() { echo -e "\e[1m\e[32mComplete.\e[0m\n"; }
completed() { complete; }
title() { echo -e "\e[1m\e[44m $1 \e[0m"; }
warn() { echo -e "\e[1m\e[33mWarning: $1\e[0m"; }
die() {
    echo -e "\e[1m\e[31mError: $1\e[0m" >&2
    exit 1
}

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# The workspace is wherever this repository was cloned, unless overridden
ROVER_WS="${ROVER_WS:-$(dirname "$SCRIPTS_DIR")}"

[ -f /etc/os-release ] || die "Cannot find /etc/os-release. These scripts only support Ubuntu."
. /etc/os-release
# Ubuntu derivatives (including NVIDIA's L4T) report the base release here
UBUNTU_CODENAME="${UBUNTU_CODENAME:-$VERSION_CODENAME}"
ARCH="$(dpkg --print-architecture)"

is_jetson() {
    [ -f /etc/nv_tegra_release ] ||
        tr -d '\0' </proc/device-tree/model 2>/dev/null | grep -qi "jetson"
}

# ROS only ships binary packages for one Ubuntu release per distro, so the
# distro follows the OS. Jetsons on JetPack 6 are Ubuntu 22.04 and can only get
# Humble from apt; JetPack 7 is Ubuntu 24.04 and gets Jazzy.
# Set ROVER_ROS_DISTRO to override the detection.
if [ -z "$ROVER_ROS_DISTRO" ]; then
    case "$UBUNTU_CODENAME" in
    noble) ROVER_ROS_DISTRO=jazzy ;;
    jammy) ROVER_ROS_DISTRO=humble ;;
    *)
        die "No supported ROS2 binaries for Ubuntu '$UBUNTU_CODENAME' (need 24.04 for Jazzy or 22.04 for Humble).
On a Jetson running JetPack 5 or older, upgrade JetPack or use the dev container in .devcontainer/ instead."
        ;;
    esac
fi
ROS_SETUP="/opt/ros/$ROVER_ROS_DISTRO/setup.bash"

# Appends a line to ~/.bashrc unless it is already there
add_to_bashrc() {
    grep -qxF "$1" ~/.bashrc 2>/dev/null || echo "$1" >>~/.bashrc
}

apt_upgrade() {
    sudo apt-get update
    if [ "$SKIP_APT_UPGRADE" = "1" ]; then
        warn "SKIP_APT_UPGRADE=1, not upgrading existing packages"
    else
        sudo apt-get -y upgrade
    fi
}
