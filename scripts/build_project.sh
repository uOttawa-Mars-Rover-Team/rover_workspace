#!/bin/bash

complete () { echo -e "\e[1m\e[32mComplete.\e[0m\n"; }
title () { echo -e "\e[1m\e[44m $1 \e[0m"; }

title "----- Building project -----"

title "Running catkin_make"
source /opt/ros/melodic/setup.bash;
(cd .. && catkin_make);
complete
