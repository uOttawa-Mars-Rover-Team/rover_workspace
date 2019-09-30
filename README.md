# rover_workspace

uoRover development catkin workspace

## Getting started
These steps only need to be done once and will set up your entire dev environment, which includes ROS, packages, and this code repository.

1. Create a Ubuntu 18.04 virtual machine or dual boot your computer.
2. Install git on your machine `sudo apt install git`
3. Clone this repository at your home location `cd ~ && git clone https://gitlab.com/uorover/rover_workspace.git`
4. Run the setup script with `cd ~/rover_workspace/scripts && ./full_setup.sh`
5. Open a new terminal window and run the following: `cd ~/rover_workspace && catkin_make`
