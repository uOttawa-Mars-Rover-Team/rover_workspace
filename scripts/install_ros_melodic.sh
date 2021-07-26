echo "---- Seting up ROS melodic ----";

echo "Setup your sources.list";
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list';
echo "Complete";
echo "";

echo "Set up your keys";
sudo apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654;
echo "Complete";
echo "";

echo "Configuring Ubuntu repositories to allow restricted, universe, and multiverse";
sudo add-apt-repository restricted;
sudo add-apt-repository universe;
sudo add-apt-repository multiverse;
echo "Complete";
echo "";

echo "Installing ROS melodic";
sudo apt update;
sudo apt -y install ros-melodic-desktop-full;
echo "Complete";
echo "";

echo "Initialize rosdep";
sudo apt install python-rosdep;
sudo rosdep init;
rosdep update;
echo "Complete";
echo "";

echo "Environment setup - sourcing bashrc";
echo "source /opt/ros/melodic/setup.bash";
echo "source /opt/ros/melodic/setup.bash" >> ~/.bashrc;
echo "source ~/rover_workspace/devel/setup.bash" >> ~/.bashrc;
source ~/.bashrc;
echo "Complete";
echo "";

echo "Dependencies for building packages";
sudo apt -y install python-rosinstall python-rosinstall-generator python-wstool build-essential;
echo "Complete";
echo "";
