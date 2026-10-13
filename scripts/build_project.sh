#!/bin/bash

set -e

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

title "----- Building project -----"

title "Running colcon build"
source "$ROS_SETUP"
(cd "$ROVER_WS" && colcon build)
completed
