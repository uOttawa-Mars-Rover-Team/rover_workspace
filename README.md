# rover_workspace

uoRover development catkin workspace

## Getting started
These steps only need to be done once and will set up your entire dev environment, which includes ROS, packages, and this code repository.

1. Create a Ubuntu 18.04 virtual machine or dual boot your computer.
2. Install git on your machine `sudo apt install git`
3. Clone this repository at your home location `cd ~ && git clone https://gitlab.com/uorover/rover_workspace.git`
4. Run the setup script with `cd ~/rover_workspace/scripts && ./full_setup.sh`

## New features
As we add new features to the build keep new developments on a seperate branch from the master. This way the master branch will
stay functional while we work on individual systems.
