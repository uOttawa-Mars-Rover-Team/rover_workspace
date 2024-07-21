#include <memory>
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include <sensor_msgs/msg/joy.hpp>
#include <tuple>
#include "/home/camilla_n/Rover/rover_workspace/src/arm_controls/serial_communication_library/include/serial_communication.hpp"

using namespace std;

class TestSerialNode : public rclcpp::Node{
    public:
        TestSerialNode() : Node("serial_subscriber"){
            RCLCPP_INFO(this->get_logger(), "Started node at: %s", this->get_fully_qualified_name());

            joy_subscriber_ = this->create_subscription<sensor_msgs::msg::Joy>(
                "/arm_joy", 10, std::bind(&TestSerialNode::serial_callback, this, std::placeholders::_1));
        
            RCLCPP_INFO(this->get_logger(), "Subscribing to messages from: %s", joy_subscriber_->get_topic_name());

            serialObject = new SerialCommunication();

            serialObject->connect_serial(0);
        }

        SerialCommunication* serialObject;

    private:
        void serial_callback(const sensor_msgs::msg::Joy & msg) const{
            string string_msg = "f;";
            for(size_t i = 0; i < msg.axes.size(); i++){
                string_msg += to_string(msg.axes[i]) + ";";
            }
            //for(size_t i = 0; i < msg.buttons.size(); i++){
            //    string_msg += to_string(msg.buttons[i]) + ";";
            //}
            string_msg += "!";
            //cout << "Message:" + string_msg << endl;
            serialObject->publishToArduino(string_msg);
        }

        rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr joy_subscriber_;

};

int main(int argc, char * argv[]){
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<TestSerialNode>());
  rclcpp::shutdown();
  return 0;
}