echo "----- Installing external packages -----";

echo "Cloning external packages repositories";
git submodule update;
echo "Complete";
echo "";

echo "Installing dependencies for the external";
sudo apt -y install libusb-dev ros-melodic-openslam-gmapping;

echo "Installing the external packages";
rosdep install --from-paths ../src/external_packages -i -y;
echo "Complete";
echo "";

echo "Remove the wii remote from joystick_drivers";
rm -rf ./src/external_packages/joystick_drivers/wiimote;
echo "Complete";
echo "";