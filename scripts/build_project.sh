echo "----- Building project -----";

echo "Running catkin_make";
source /opt/ros/melodic/setup.bash;
(cd .. && catkin_make);
echo "Complete";
echo "";
