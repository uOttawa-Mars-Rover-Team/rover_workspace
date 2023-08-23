#!/bin/bash

SCRIPTS_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
source ${SCRIPTS_DIR}/common.sh

title "----- Building project -----"

title "Running colcon build"
source /opt/ros/humble/setup.bash
(cd $ROVER_WS && colcon build)
completed
