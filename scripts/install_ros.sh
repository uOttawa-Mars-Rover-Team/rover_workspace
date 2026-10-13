#!/bin/bash

set -e

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# The Jetson is headless on the rover, so it gets ros-base by default. Any GUI
# packages our own packages depend on (e.g. rviz2) are still pulled in by rosdep.
# Set ROS_INSTALL_TYPE to desktop or ros-base to override.
if [ -z "$ROS_INSTALL_TYPE" ]; then
    if is_jetson; then
        ROS_INSTALL_TYPE=ros-base
    else
        ROS_INSTALL_TYPE=desktop
    fi
fi

title "---- Installing and setting up ROS2 ${ROVER_ROS_DISTRO^} ($ROS_INSTALL_TYPE) on Ubuntu $UBUNTU_CODENAME/$ARCH ----"

if [ "$ROVER_ROS_DISTRO" != "jazzy" ]; then
    warn "This workspace targets ROS2 Jazzy, but Ubuntu $UBUNTU_CODENAME only has binaries for ${ROVER_ROS_DISTRO^}."
    warn "Expect some packages to need changes. To run Jazzy on this machine, use the dev container."
fi

title "Updating and upgrading existing packages"
apt_upgrade
completed

title "Setting up locale"
if ! locale | grep -qi "utf-\?8"; then
    sudo apt-get install -y locales
    sudo locale-gen en_US en_US.UTF-8
    sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
    export LANG=en_US.UTF-8
fi
completed

title "Setting up sources"
sudo apt-get install -y software-properties-common curl
sudo add-apt-repository -y universe

if dpkg -s ros2-apt-source >/dev/null 2>&1; then
    echo "ros2-apt-source is already installed"
else
    if [ -f /etc/apt/sources.list.d/ros2.list ]; then
        warn "Found a manually added /etc/apt/sources.list.d/ros2.list. If apt reports conflicting"
        warn "Signed-By values below, delete that file and re-run this script."
    fi
    ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
    [ -n "$ROS_APT_SOURCE_VERSION" ] || die "Could not look up the latest ros-apt-source release (GitHub API unreachable or rate limited)."
    curl -fL -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.${UBUNTU_CODENAME}_all.deb"
    sudo dpkg -i /tmp/ros2-apt-source.deb
fi
completed

title "Updating and upgrading existing packages (after ROS repo installation)"
apt_upgrade
completed

title "Installing ROS2 ${ROVER_ROS_DISTRO^}"
sudo apt-get install -y "ros-$ROVER_ROS_DISTRO-$ROS_INSTALL_TYPE"
sudo apt-get install -y ros-dev-tools
completed

title "Installing and initializing rosdep"
sudo apt-get -y install python3-rosdep
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
    sudo rosdep init
fi
rosdep update
completed

title "Sourcing .bashrc - Environment setup"
add_to_bashrc "source $ROS_SETUP"
add_to_bashrc "[ -f $ROVER_WS/install/setup.bash ] && source $ROVER_WS/install/setup.bash"
completed
